# Kiri TTS Khmer Voice REST API

A high-performance, automated REST API server built with FastAPI that allows any external application, website, bot, or script to generate natural Khmer speech using Kiri TTS.

---

## 🚀 Quick Start

### 1. Launch the Server
Double-click [`run_api.bat`](file:///c:/Users/AORUS/Documents/Kiri%20TTS/run_api.bat) or execute:
```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

### 2. Interactive Swagger UI
Open your browser at:
- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 📡 API Endpoints

### 1. Generate Speech (Text to Speech)
**`POST /api/tts`**

#### Request Headers:
`Content-Type: application/json`

#### Request Body:
```json
{
  "text": "ថៃដាក់វិធានការប្រាំមួយចំណុច សាកល្បងភាពស្មោះត្រង់របស់កម្ពុជា",
  "format": "mp3",
  "stream": false,
  "auto_rotate": true
}
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `text` | `string` | *(Required)* | Khmer text to synthesize. |
| `format` | `string` | `"mp3"` | Output audio format (`"mp3"` or `"wav"`). |
| `stream` | `boolean` | `false` | If `true`, returns binary `audio/mpeg` stream directly. If `false`, returns JSON metadata. |
| `auto_rotate` | `boolean` | `true` | If `true`, automatically registers a fresh account when credits run low. |

#### JSON Response (`stream = false`):
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

---

### 2. Download / Stream Audio
**`GET /api/audio/{filename}`**

Streams or downloads the generated audio file.

**Example**:
```http
GET http://localhost:8000/api/audio/kiri_1792689605.mp3
```

---

### 3. Account Pool & Credits
**`GET /api/accounts`**

Lists all registered accounts in the pool:
```json
{
  "total_accounts": 2,
  "accounts": [
    { "email": "z91420hq@spyboys.com" },
    { "email": "rda28ejd@spyboys.com" }
  ]
}
```

---

### 4. Create Fresh Account (+2,000 Credits)
**`POST /api/accounts/create`**

Spawns a new temporary email, registers on Kiri TTS, verifies the email, and adds 2,000 fresh credits to the pool in ~15 seconds:
```json
{
  "status": "success",
  "message": "Account created and verified",
  "account": {
    "email": "abc12345@spyboys.com",
    "status": "active",
    "credits": 2000
  }
}
```

---

## 💻 Code Examples for External Use

### cURL
```bash
curl -X POST "http://localhost:8000/api/tts" \
     -H "Content-Type: application/json" \
     -d "{\"text\": \"សួស្តីកម្ពុជា!\", \"format\": \"mp3\"}"
```

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/tts",
    json={
        "text": "ថៃដាក់វិធានការប្រាំមួយចំណុច សាកល្បងភាពស្មោះត្រង់របស់កម្ពុជា",
        "format": "mp3",
        "stream": False
    }
)

data = response.json()
print("Audio URL:", f"http://localhost:8000{data['download_url']}")
```

### JavaScript / Node.js
```javascript
const response = await fetch("http://localhost:8000/api/tts", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    text: "ថៃដាក់វិធានការប្រាំមួយចំណុច សាកល្បងភាពស្មោះត្រង់របស់កម្ពុជា",
    format: "mp3",
    stream: false
  })
});

const result = await response.json();
console.log("Download URL:", `http://localhost:8000${result.download_url}`);
```
