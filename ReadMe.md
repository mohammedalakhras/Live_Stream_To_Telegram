# 📖 Quran 24/7 Live Streamer for Telegram

A robust, fully automated Python application that streams the Holy Quran (114 Surahs) 24/7 to a Telegram Voice/Video Chat using `PyTgCalls` and `Pyrogram`. It dynamically fetches media files from Google Drive via the official Google Drive API, bypassing rate limits, and features a real-time web dashboard powered by FastAPI.

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Enabled-green.svg)
![Render](https://img.shields.io/badge/Deployment-Render-black.svg)

---

## ✨ Features
* **24/7 Continuous Streaming:** Automatically loops through all 114 Surahs infinitely.
* **Google Drive API Integration:** Fetches video/audio chunks dynamically to save server storage and bypass standard download rate limits.
* **Real-time Arabic Web Dashboard:** Built with FastAPI, displaying the current Surah, progress bar, elapsed/remaining time, and active viewers.
* **Smart Retry Mechanism:** Auto-detects corrupted files or network timeouts and safely re-downloads them without breaking the stream loop.
* **Anti-Sleep Ping Endpoint:** Includes a `/ping` route tailored for cron jobs to keep free-tier cloud platforms (like Render) awake indefinitely.

---

## 🛠 Prerequisites

Before deploying, ensure you have gathered the following:
1. **Telegram API Keys:** Get your `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org/).
2. **Telegram String Session:** A Pyrogram `SESSION_STRING` generated from your account.
3. **Google Service Account JSON:** A service account key from Google Cloud Console with Google Drive API enabled.
4. **Google Drive Folder IDs:** The specific Folder IDs containing the named video files (`001.mp4` to `114.mp4`).

---

## 🚀 Deployment to Render (Free Tier)

This project is optimized for deployment on [Render.com](https://render.com) using a `Dockerfile` to ensure `ffmpeg` is properly installed.

1. Fork or clone this repository.
2. Create a new **Web Service** on Render and connect your repository.
3. Set the Runtime to **Docker**.
4. Add the following **Environment Variables** in the Render dashboard:

| Variable | Description |
|---|---|
| `API_ID` | Your Telegram API ID |
| `API_HASH` | Your Telegram API Hash |
| `SESSION_STRING` | Your Pyrogram String Session |
| `CHANNEL_ID` | Target Telegram channel (e.g., `@YourChannel`) |
| `GDRIVE_CREDENTIALS_JSON` | The raw JSON string of your Google Service Account |
| `FOLDER_ID_1` | GDrive Folder ID for Surahs 1-50 |
| `FOLDER_ID_2` | GDrive Folder ID for Surahs 51-100 |
| `FOLDER_ID_3` | GDrive Folder ID for Surahs 101-114 |

5. Deploy the service. Once live, set up a free cron job via [UptimeRobot](https://uptimerobot.com) pointing to `https://your-app-url.onrender.com/ping` to prevent the server from sleeping.

---

## 💻 Local Development

```bash
# Clone the repository
git clone https://github.com/mohammedalakhras/Live_Stream_To_Telegram/
cd Live_Stream_To_Telegram

# Create a virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies (requires ffmpeg installed on OS)
pip install -r requirements.txt

# Run the server
uvicorn main:web_app --host 0.0.0.0 --port 10000
```
## 📜 License
This project is open-sourced under the MIT License. Feel free to use and modify it for Dawah and personal use.