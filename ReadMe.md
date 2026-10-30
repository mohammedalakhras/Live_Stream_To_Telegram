# 📡 Quran 24/7 Live Streamer for Telegram (RTMP & PyTgCalls)

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Dashboard-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-RTMP_Engine-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Live_Stream-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

An enterprise-grade, ultra-lightweight, and fully automated **24/7 Telegram Live Streaming System** designed to broadcast the Holy Quran (all 114 Surahs) continuously. Built with **Python, FastAPI, FFmpeg, and the Google Drive API**, this project includes an interactive Web Dashboard for real-time stream control and monitoring.

---

## 🌟 Key Features

* **🔄 Dual Streaming Architectures:**
  1. **TV-Style RTMP Broadcast (Main Version):** Streams directly to Telegram's RTMP servers using `FFmpeg`. The stream appears purely under the **Channel's Name** without exposing any personal admin account.
  2. **Interactive Group Call / Userbot Mode (Alternative):** Uses `Pyrogram` & `PyTgCalls` to stream via an admin account into a Telegram Voice/Video chat where listeners can join the call room.
* **🎛️ Interactive Web Dashboard:** Built with FastAPI, allowing admins to monitor the current Surah, progress bar, server uptime, and control the broadcast (Skip Surah, Jump to any Surah, Pause/Resume), fully protected by an admin password.
* **☁️ Official Google Drive API Integration:** Fetches video batches dynamically using a Google Cloud Service Account (`JSON`), completely bypassing `gdown` or `yt-dlp` rate limits and permission errors.
* **📉 Ultra-Low Bandwidth Optimization:** Features custom `FFmpeg` encoding profiles (`360p`, `10fps`, `yuv420p`, `Mono 32k AAC`) tailored for static/semi-static video text—ensuring smooth playback even on slow connections (<100 Kbps) and preserving free-tier cloud bandwidth.
* **🧠 Smart Local Caching:** Automatically verifies existing `.mp4` files before downloading to prevent redundant API calls and save server bandwidth across multiple full Quran cycles (Khatmas).

---

## ⚖️ Comparison of Streaming Modes

| Feature | Mode 1: RTMP Broadcast (Root Folder) | Mode 2: Stream by Owner Account |
| :--- | :--- | :--- |
| **Core Technology** | `FFmpeg` + `RTMP Protocol` | `Pyrogram` + `PyTgCalls` (MTProto) |
| **Broadcaster Identity** | **Channel Name Only** (TV Style) | **Admin Personal Account** |
| **Telegram Session Needed?** | ❌ No (Only RTMP URL & Key) | ✅ Yes (`API_ID`, `API_HASH`, `SESSION_STRING`) |
| **Account Ban Risk** | 🛡️ **0% (Zero Risk)** | ⚠️ Low (Requires valid user session) |
| **Dashboard Controls** | Skip, Jump to Surah | Pause, Resume, Skip, Jump to Surah |
| **Resource Usage** | 🟢 Ultra-Light | 🟡 Moderate |

---

## 📂 Repository Structure

```text
Live_Stream_To_Telegram/
│
├── app.py                        # [Mode 1] Main RTMP Streamer + Interactive Dashboard
├── Dockerfile                    # Docker configuration with FFmpeg pre-installed
├── requirements.txt              # Lightweight dependencies for Mode 1 (RTMP)
├── README.md                     # Project Documentation
│
└── Stream by Owner Account/      # [Mode 2] Alternative Userbot / PyTgCalls Streamer
    ├── app.py                    # PyTgCalls Streamer + Pause/Resume Dashboard
    └── requirements.txt          # Dependencies including pyrofork & py-tgcalls
```

---

## 🛠️ Prerequisites & Setup

### 1. Google Drive API Setup
To avoid Google Drive download quotas, this project uses a **Google Service Account**:
1. Divide your 114 Surah videos (`001.mp4` to `114.mp4`) into 3 folders on Google Drive:
   * **Folder 1:** `001.mp4` to `050.mp4`
   * **Folder 2:** `051.mp4` to `100.mp4`
   * **Folder 3:** `101.mp4` to `114.mp4`
2. Go to the [Google Cloud Console](https://console.cloud.google.com/), create a project, and enable the **Google Drive API**.
3. Go to **Credentials** -> **Create Credentials** -> **Service Account**, then generate and download a **JSON Key**.
4. Open the downloaded `.json` file, copy the `client_email` address, and **Share** your 3 Google Drive folders with this email (Grant **Viewer** permission).
5. Copy the **Folder ID** from the URL of each of your 3 Google Drive folders (e.g., if the URL is `https://drive.google.com/drive/folders/19w-noPiy9WY6...`, the ID is `19w-noPiy9WY6...`).

---

## 🔐 Environment Variables

> **⚠️ Important Note:** For `FOLDER_URL_1`, `FOLDER_URL_2`, and `FOLDER_URL_3`, you must enter the **Google Drive Folder ID only** (not the full HTTP link).

### 🅰️ Mode 1: RTMP Broadcast (Root Directory - Recommended)

| Variable | Required | Description | Example |
| :--- | :---: | :--- | :--- |
| `RTMP_URL` | ✅ | Full Telegram RTMP Server URL + Stream Key combined | `rtmps://dc4-1.rtmp.t.me/s/12345:AbCdEfG...` |
| `CHANNEL_ID` | ✅ | Channel username or display name for the dashboard | `@QuranLiveChannel` |
| `GDRIVE_CREDENTIALS_JSON` | ✅ | Full raw text content of your Google Service Account `.json` file | `{"type": "service_account", ...}` |
| `FOLDER_URL_1` | ✅ | Google Drive **Folder ID** for Surahs 001 to 050 | `19w-noPiy9WY6VwjZWSr8RKO3f_juODEu` |
| `FOLDER_URL_2` | ✅ | Google Drive **Folder ID** for Surahs 051 to 100 | `1AbCdEfGhIjKlMnOpQrStUvWxYz123456` |
| `FOLDER_URL_3` | ✅ | Google Drive **Folder ID** for Surahs 101 to 114 | `1ZyXwVuTsRqPoNmLkJiHgFeDcBa654321` |
| `ADMIN_PASSWORD` | ❌ | Password to unlock Skip/Jump controls on the Web Dashboard | `MySecretPass123` (Default: `123456`) |
| `PORT` | ❌ | Port for the FastAPI web server | `10000` or `3000` |

### 🅱️ Mode 2: Stream by Owner Account (`PyTgCalls` Mode)

If you use the code inside `Stream by Owner Account/`, replace `RTMP_URL` with the following Telegram MTProto variables:

| Variable | Required | Description |
| :--- | :---: | :--- |
| `API_ID` | ✅ | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | ✅ | Telegram API Hash from [my.telegram.org](https://my.telegram.org) |
| `SESSION_STRING` | ✅ | Pyrogram String Session of the admin account |
| `CHANNEL_ID` | ✅ | Target Telegram Channel Username (e.g., `@MyChannel`) or Chat ID |

*(Plus the same `GDRIVE_CREDENTIALS_JSON`, `FOLDER_URL_1/2/3`, `ADMIN_PASSWORD`, and `PORT` variables from Mode 1).*

---

## 🚀 Deployment Guide

### Option 1: Deploy on Koyeb or Render (Using Docker)
1. Fork this repository to your GitHub account.
2. Create a new **Web Service** on [Koyeb](https://www.koyeb.com/) or [Render](https://render.com/).
3. Select **Docker** as the Builder / Runtime (leave custom build/run commands empty so it utilizes the `Dockerfile`).
4. Add the required **Environment Variables** from the table above.
5. Click **Deploy**.
6. **Keep-Alive:** Add your deployed URL followed by `/ping` (e.g., `https://your-app.koyeb.app/ping`) to [UptimeRobot](https://uptimerobot.com/) (set to `GET` method every 5 minutes) to prevent the server from sleeping.

### Option 2: Run Locally or on a VPS
```bash
# 1. Clone the repository
git clone https://github.com/mohammedalakhras/Live_Stream_To_Telegram.git
cd Live_Stream_To_Telegram

# 2. Install FFmpeg (Ubuntu/Debian)
sudo apt update && sudo apt install -y ffmpeg

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Run the server
uvicorn app:web_app --host 0.0.0.0 --port 10000
```

---

## 🖥️ Interactive Web Dashboard

Once deployed, open your server URL in any browser to access the dashboard:
* **Live Progress Bar:** Displays elapsed time, total duration, and remaining time for the active Surah.
* **Instant Skip:** Terminates the current Surah stream and immediately transitions to the next one.
* **Direct Surah Jump:** Select any of the 114 Surahs from the dropdown menu to broadcast it immediately.
* **Storage & Khatma Counter:** Tracks locally cached files (`X / 114`) and completed full Quran cycles (Khatmas).

---

## 🔍 SEO Keywords & Topics
`telegram-live-stream` `quran-24-7` `telegram-rtmp` `pytgcalls` `pyrogram` `ffmpeg-streaming` `fastapi-dashboard` `islamic-bot` `quran-radio` `google-drive-streamer` `koyeb-deployment` `render-docker`

## 📜 License
Distributed under the **MIT License**. Feel free to fork, modify, and share this project as an ongoing charity (Sadaqah Jariyah).