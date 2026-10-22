import asyncio
import random
import string
import requests
import os
from playwright.async_api import async_playwright

# --- SETTINGS ---
NUM_ACCOUNTS = 1
SONJJ_API_KEY = "b8426cc102f52ba88adb3bf2bb719a9165f69c15edee16043b0cd0e8b61ae7ec"
TEXTS_TO_GENERATE = [
    "ថៃដាក់វិធានការប្រាំមួយចំណុច សាកល្បងភាពស្មោះត្រង់របស់កម្ពុជា",
    "ថៃប្រកាសថា នឹងវាយតម្លៃភាពស្មោះត្រង់របស់កម្ពុជា ដោយផ្អែកលើការអនុវត្តវិធានការកសាងទំនុកចិត្តទាំង ៦ ចំណុច ដែលភាគីទាំងពីរបានឯកភាពគ្នា ក្រោមដំណើរការផ្សះផ្សា UNCLOS",
]
OUTPUT_FOLDER = "kiri_stealth_outputs"
if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)

def get_temp_email():
    rand = ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8))
    email = f"{rand}@random.com"
    try:
        r = requests.get(f"https://app.sonjj.com/v1/temp_email/create?email={email}&lifetime=60", 
                         headers={"X-Api-Key": SONJJ_API_KEY})
        return r.json().get("email") if r.status_code == 200 else None
    except: return None

def get_verification_link(email):
    try:
        # Step 1: list inbox messages
        r = requests.get(f"https://app.sonjj.com/v1/temp_email/inbox?email={email}",
                         headers={"X-Api-Key": SONJJ_API_KEY})
        if r.status_code == 200:
            messages = r.json().get("messages", [])
            for msg in messages:
                mid = msg.get("mid")
                if not mid: continue
                # Step 2: fetch full message body
                r2 = requests.get(f"https://app.sonjj.com/v1/temp_email/message?email={email}&mid={mid}",
                                  headers={"X-Api-Key": SONJJ_API_KEY})
                if r2.status_code == 200:
                    import re
                    body = r2.json().get("body", "")
                    links = re.findall(r'https?://[^\s<>"\\]+', body)
                    if links: return links[0]
    except: pass
    return None

async def run_bot():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Set to True to hide browser
        page = await browser.new_page()
        
        for i in range(NUM_ACCOUNTS):
            email = get_temp_email()
            password = ''.join(random.choices(string.ascii_letters + string.digits + "!@#", k=12))
            if not email: continue
            
            print(f"Account {i+1}: Registering {email}...")
            try:
                await page.goto("https://www.kiritts.com/auth/register", wait_until="networkidle")
                await page.fill('#email', email)
                await page.fill('#password', password)
                await page.fill('#confirmPassword', password)
                await page.check('#terms')  # Accept Terms of Service
                await page.click('button:has-text("Create Account")')
                
                # Poll for verification link
                link = None
                for _ in range(10):
                    await asyncio.sleep(10)
                    link = get_verification_link(email)
                    if link: break
                
                if link:
                    await page.goto(link)
                    print(f"Verified {email}")
                    
                    # Generate audio
                    await page.goto("https://www.kiritts.com/dashboard/text-to-speech", wait_until="networkidle")
                    # Dismiss survey/tour popups
                    try: await page.get_by_role("button", name="Later").click(timeout=3000)
                    except: pass
                    try: await page.get_by_text("Skip all").click(timeout=3000)
                    except: pass
                    
                    for idx, text in enumerate(TEXTS_TO_GENERATE):
                        await page.fill('textarea', text)
                        await page.click('button:has-text("Generate Speech")')
                        await page.wait_for_selector('audio', timeout=60000)
                        audio_url = await page.get_attribute('audio', 'src')
                        if audio_url:
                            if audio_url.startswith('/'):
                                audio_url = f"https://www.kiritts.com{audio_url}"
                            res = requests.get(audio_url)
                            with open(f"{OUTPUT_FOLDER}/acc_{i+1}_text_{idx+1}.mp3", "wb") as f:
                                f.write(res.content)
                            print(f"Saved audio {idx+1}")
            except Exception as e:
                print(f"Failed account {i+1}: {e}")
            
            # Human-like delay between accounts
            await asyncio.sleep(random.uniform(5, 15))

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_bot())

