# Kiri TTS Khmer Voice REST API 🇰🇭

A fast, automated REST API server built with FastAPI for synthesizing natural Khmer speech using Kiri TTS. Features automatic account pool rotation and instant credit replenishment.

---

## ⚡ Features

- **Khmer Speech Synthesis**: High-quality natural Khmer voice synthesis (Maly / Sophea / Dara).
- **Format Conversion**: Direct 192kbps MP3 and WAV output powered by FFmpeg.
- **Auto-Account Rotation**: Automatic temp-email registration and verification via Sonjj API whenever credit limits are reached.
- **RESTful Endpoints**: Built with FastAPI, including streaming audio responses and full Swagger UI documentation.
- **Docker Ready**: Pre-configured `Dockerfile` with Playwright Chromium and FFmpeg pre-installed.

---

## 🚀 Quick Start (Local)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Run API Server
- **Windows**: Double-click `run_api.bat`
- **CLI**:
```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🐳 Docker Deployment (Recommended for Hosting)

Because this service uses headless Chromium and FFmpeg to generate audio, hosting via Docker is recommended:

```bash
docker compose up -d --build
```

### Free & Low-Cost Cloud Hosting Options:
1. **Render.com**: Connect GitHub repo -> Select "Docker" environment -> Deploy (Free/Starter tier).
2. **Railway.app**: New Project -> Deploy from GitHub repo -> Auto-detects `Dockerfile`.
3. **VPS (Hostinger / Ubuntu / DigitalOcean)**:
   ```bash
   git clone <your-repo>
   cd "Kiri TTS"
   docker compose up -d
   ```

---

## 📡 API Reference

### `POST /api/tts`
Synthesizes Khmer text to audio.

**Payload**:
```json
{
  "text": "ថៃដាក់វិធានការប្រាំមួយចំណុច សាកល្បងភាពស្មោះត្រង់របស់កម្ពុជា",
  "format": "mp3",
  "stream": false,
  "auto_rotate": true
}
```

**Response**:
```json
{
  "status": "success",
  "filename": "kiri_1792689605.mp3",
  "format": "mp3",
  "size_bytes": 116396,
  "download_url": "/api/audio/kiri_1792689605.mp3",
  "account_used": "rda28ejd@spyboys.com"
}
```

### `GET /api/audio/{filename}`
Streams or downloads the generated MP3/WAV file.

### `GET /api/accounts`
Lists registered accounts and pool status.

### `POST /api/accounts/create`
Spawns and verifies a fresh account with +2,000 free credits in ~15s.

---

## 📄 License
MIT License
