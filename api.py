import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

import os
import re
import time
import random
import string
import shutil
import asyncio
import requests
import subprocess
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "kiri_audio_outputs")
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.txt")
SONJJ_API_KEY = "b8426cc102f52ba88adb3bf2bb719a9165f69c15edee16043b0cd0e8b61ae7ec"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Docker-optimized Chromium flags
CHROMIUM_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--no-first-run",
    "--no-zygote",
    "--disable-extensions",
]

# Initialize FastAPI App
app = FastAPI(
    title="Kiri TTS Khmer Voice REST API",
    description="High-performance, stable REST API for generating natural Khmer Text-to-Speech audio with automatic multi-account rotation and credit replenishment.",
    version="1.0.0"
)

# Enable CORS for external applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Account Pool Management ---
def load_accounts():
    accounts = []
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "|" in line:
                    parts = line.split("|")
                    accounts.append({"email": parts[0], "password": parts[1]})
    if not accounts:
        accounts.append({"email": "z91420hq@spyboys.com", "password": "NewPassword123!"})
    return accounts

def save_account_to_file(email, password):
    with open(ACCOUNTS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{email}|{password}\n")

def create_temp_email():
    rand = ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8))
    email = f"{rand}@spyboys.com"
    try:
        r = requests.get(f"https://app.sonjj.com/v1/temp_email/create?email={email}&lifetime=60", 
                         headers={"X-Api-Key": SONJJ_API_KEY}, timeout=10)
        if r.status_code == 200:
            return r.json().get("email", email)
    except: pass
    return email

def fetch_verification_link(email):
    try:
        r = requests.get(f"https://app.sonjj.com/v1/temp_email/inbox?email={email}",
                         headers={"X-Api-Key": SONJJ_API_KEY}, timeout=10)
        if r.status_code == 200:
            msgs = r.json().get("messages", [])
            for m in msgs:
                mid = m.get("mid")
                if not mid: continue
                r2 = requests.get(f"https://app.sonjj.com/v1/temp_email/message?email={email}&mid={mid}",
                                  headers={"X-Api-Key": SONJJ_API_KEY}, timeout=10)
                if r2.status_code == 200:
                    body = r2.json().get("body", "")
                    href_links = re.findall(r'href=[\'"]?([^\'" >]+)', body)
                    for l in href_links:
                        if "/tr/cl/" in l or "confirm?token=" in l:
                            return l
                    all_links = re.findall(r'https?://[^\s<>"\\]+', body)
                    for l in all_links:
                        if "/tr/cl/" in l or "confirm" in l or "token" in l:
                            return l
    except: pass
    return None

async def register_account():
    email = create_temp_email()
    password = "KiriPass" + ''.join(random.choices(string.digits, k=4)) + "!"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_ARGS)
        page = await browser.new_page()
        await page.goto("https://www.kiritts.com/auth/register", wait_until="networkidle")
        await page.fill('#email', email)
        await page.fill('#password', password)
        await page.fill('#confirmPassword', password)
        await page.check('#terms')
        await page.click('button:has-text("Create Account")')

        link = None
        for _ in range(15):
            await asyncio.sleep(4)
            link = fetch_verification_link(email)
            if link: break

        if not link:
            await browser.close()
            raise Exception("Failed to receive verification email from Kiri TTS")

        await page.goto(link, wait_until="networkidle")
        await asyncio.sleep(3)
        await browser.close()

    save_account_to_file(email, password)
    return {"email": email, "password": password, "status": "active", "credits": 2000}

# --- Core Speech Synthesizer ---
async def synthesize_speech(text: str, account: dict):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=CHROMIUM_ARGS)
        context = await browser.new_context()
        page = await context.new_page()

        # Listen to upstream API responses for early error detection
        upstream_error = None
        async def on_response(res):
            nonlocal upstream_error
            url = res.url
            if "generate-speech" in url and res.status >= 400:
                if res.status == 502:
                    upstream_error = "Kiri TTS server is currently experiencing a temporary 502 Bad Gateway (upstream overloaded). Please retry in 1-2 minutes."
                else:
                    upstream_error = f"Kiri TTS generate-speech returned HTTP {res.status}"

        page.on("response", on_response)

        # Step 1: Login
        await page.goto("https://www.kiritts.com/auth/login?locale=en", wait_until="domcontentloaded")
        await page.locator("#email").wait_for(state="visible", timeout=15000)
        await page.locator("#email").fill(account["email"])
        await page.locator("#password").fill(account["password"])
        await page.locator("#password").press("Enter")

        for _ in range(15):
            await asyncio.sleep(1)
            if "dashboard" in page.url:
                break

        await asyncio.sleep(2)

        # Step 2: Handle Survey Dialog (Where did you hear about us?)
        try:
            dialog = page.locator('div[role="dialog"]')
            if await dialog.count() > 0:
                later = dialog.locator('button:has-text("Later"), button:has-text("Close"), button:has-text("Skip")')
                if await later.count() > 0:
                    await later.first.click(force=True)
                    await asyncio.sleep(1)
        except Exception:
            pass

        # Step 3: Handle Onboarding Tour (Skip all)
        try:
            skip_all = page.locator('button:has-text("Skip all"), button:has-text("Skip")')
            if await skip_all.count() > 0:
                await skip_all.first.click(force=True)
                await asyncio.sleep(0.5)
        except Exception:
            pass

        # Step 4: Fill Khmer text in editor
        editor = page.locator('textarea[placeholder*="Type or paste your text here"]').first
        await editor.wait_for(state="attached", timeout=15000)
        await editor.fill(text, force=True)
        await editor.dispatch_event('input')
        await editor.dispatch_event('change')
        await editor.press("End")
        await editor.press("Space")
        await editor.press("Backspace")
        await asyncio.sleep(0.5)

        # Check again if tour popup appeared after focusing editor
        try:
            skip_again = page.locator('button:has-text("Skip all")')
            if await skip_again.count() > 0:
                await skip_again.first.click(force=True)
                await asyncio.sleep(0.5)
        except Exception:
            pass

        # Step 5: Locate and trigger Generate Speech
        gen_btn = page.locator('button:has-text("Generate Speech")')
        await gen_btn.wait_for(state="attached", timeout=10000)

        for _ in range(5):
            if await gen_btn.is_disabled():
                await editor.press("End")
                await editor.press("Space")
                await editor.press("Backspace")
                await asyncio.sleep(0.5)
            else:
                break

        await gen_btn.click(force=True)

        # Step 6: Wait for audio generation or detect upstream errors immediately
        audio_src = ""
        for i in range(75):
            if upstream_error:
                await browser.close()
                raise Exception(upstream_error)

            audio = page.locator("audio[src]")
            if await audio.count() > 0:
                src = await audio.first.get_attribute("src")
                if src and len(src) > 5:
                    audio_src = src
                    break

            # Check for credit limit notices
            if i > 5 and i % 5 == 0:
                page_text = await page.inner_text("body")
                if any(w in page_text.lower() for w in ["credit", "limit reached", "upgrade plan"]):
                    await browser.close()
                    raise Exception("OUT_OF_CREDITS")

            await asyncio.sleep(1)

        if not audio_src:
            if upstream_error:
                await browser.close()
                raise Exception(upstream_error)
            await browser.close()
            raise Exception("Speech generation timed out waiting for audio from Kiri TTS")

        # Fetch binary stream inside authenticated browser session
        audio_bytes = await page.evaluate('''async (url) => {
            const res = await fetch(url);
            if (!res.ok) throw new Error("HTTP " + res.status);
            const buf = await res.arrayBuffer();
            return Array.from(new Uint8Array(buf));
        }''', audio_src)

        await browser.close()
        return bytes(audio_bytes)

# --- Request / Response Models ---
class TTSRequest(BaseModel):
    text: str = Field(..., description="Khmer text to convert to speech", example="ថៃដាក់វិធានការប្រាំមួយចំណុច សាកល្បងភាពស្មោះត្រង់របស់កម្ពុជា")
    format: str = Field(default="mp3", description="Output audio format ('mp3' or 'wav')")
    stream: bool = Field(default=False, description="If true, returns raw audio stream. If false, returns JSON with download URL.")
    auto_rotate: bool = Field(default=True, description="Automatically register new account if current runs out of credit.")

INDEX_HTML = os.path.join(BASE_DIR, "index.html")

# --- API Endpoints ---
@app.get("/", tags=["Web App"])
def root():
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML, media_type="text/html")
    return {
        "service": "Kiri TTS Khmer Voice REST API",
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/api/info", tags=["Info"])
def api_info():
    return {
        "service": "Kiri TTS Khmer Voice REST API",
        "status": "online",
        "docs_url": "/docs",
        "endpoints": {
            "generate_tts": "POST /api/tts",
            "list_accounts": "GET /api/accounts",
            "create_account": "POST /api/accounts/create",
            "get_audio": "GET /api/audio/{filename}"
        }
    }

@app.get("/health", tags=["Info"])
def health():
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/api/tts", tags=["TTS Generation"])
async def generate_tts(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text parameter cannot be empty.")

    accounts = load_accounts()
    data = None
    current_acc = accounts[0]
    last_error = ""

    for acc in accounts:
        try:
            current_acc = acc
            data = await synthesize_speech(req.text, acc)
            break
        except Exception as e:
            last_error = str(e)
            print(f"Account {acc['email']} error: {e}", flush=True)
            if "502" in last_error or "Bad Gateway" in last_error:
                break

    if not data and req.auto_rotate and ("OUT_OF_CREDITS" in last_error or "limit" in last_error.lower()):
        print("Auto-registering new account due to credit limit...", flush=True)
        try:
            new_acc = await register_account()
            current_acc = new_acc
            data = await synthesize_speech(req.text, new_acc)
        except Exception as reg_err:
            last_error = str(reg_err)

    if not data:
        raise HTTPException(status_code=500, detail=f"Generation failed: {last_error}")

    timestamp = int(time.time())
    wav_filename = f"kiri_{timestamp}.wav"
    mp3_filename = f"kiri_{timestamp}.mp3"
    wav_path = os.path.join(OUTPUT_DIR, wav_filename)
    mp3_path = os.path.join(OUTPUT_DIR, mp3_filename)

    with open(wav_path, "wb") as f:
        f.write(data)

    if req.format.lower() == "wav":
        final_file = wav_path
        final_filename = wav_filename
        media_type = "audio/wav"
    else:
        # Convert to MP3 via ffmpeg
        subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-b:a", "192k", mp3_path], check=True, capture_output=True)
        final_file = mp3_path
        final_filename = mp3_filename
        media_type = "audio/mpeg"

    if req.stream:
        return FileResponse(final_file, media_type=media_type, filename=final_filename)

    return {
        "status": "success",
        "filename": final_filename,
        "format": req.format.lower(),
        "size_bytes": os.path.getsize(final_file),
        "download_url": f"/api/audio/{final_filename}",
        "account_used": current_acc["email"]
    }

@app.get("/api/audio/{filename}", tags=["Audio Download"])
def get_audio_file(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    media_type = "audio/mpeg" if filename.endswith(".mp3") else "audio/wav"
    return FileResponse(file_path, media_type=media_type, filename=filename)

@app.get("/api/accounts", tags=["Account Management"])
def list_accounts():
    accounts = load_accounts()
    return {
        "total_accounts": len(accounts),
        "accounts": [{"email": a["email"]} for a in accounts]
    }

@app.post("/api/accounts/create", tags=["Account Management"])
async def create_new_account():
    """Auto-generates and verifies a new Kiri TTS account with +2,000 free credits in ~15s."""
    try:
        acc = await register_account()
        return {"status": "success", "message": "Account created and verified", "account": acc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
