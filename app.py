import os
import shutil
import asyncio
import logging
import time
from datetime import datetime, timezone
from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# إعداد السجلات (Logging) لمراقبة كل خطوة في لوحة Render
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("QuranStreamer")

# ==================== إعدادات متغيرات البيئة ====================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@MohammedAlakhras")
SESSION_URL = os.getenv("SESSION_URL", "")

FOLDER_URL_1 = os.getenv("FOLDER_URL_1", "")
FOLDER_URL_2 = os.getenv("FOLDER_URL_2", "")
FOLDER_URL_3 = os.getenv("FOLDER_URL_3", "")

PORT = int(os.getenv("PORT", "10000"))

# أسماء سور القرآن الكريم (114 سورة) لعرضها في لوحة المعلومات
SURAH_NAMES = [
    "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة", "الأنعام", "الأعراف", "الأنفال", "التوبة", "يونس",
    "هود", "يوسف", "الرعد", "إبراهيم", "الحجر", "النحل", "الإسراء", "الكهف", "مريم", "طه",
    "الأنبياء", "الحج", "المؤمنون", "النور", "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت", "الروم",
    "لقمان", "السجدة", "الأحزاب", "سبأ", "فاطر", "يس", "الصافات", "ص", "الزمر", "غافر",
    "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية", "الأحقاف", "محمد", "الفتح", "الحجرات", "ق",
    "الذاريات", "الطور", "النجم", "القمر", "الرحمن", "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة",
    "الصف", "الجمعة", "المنافقون", "التغابن", "الطلاق", "التحريم", "الملك", "القلم", "الحاقة", "المعارج",
    "نوح", "الجن", "المزمل", "المدثر", "القيامة", "الإنسان", "المرسلات", "النبأ", "النازعات", "عبس",
    "التكوير", "الانفطار", "المطففين", "الانشقاق", "البروج", "الطارق", "الأعلى", "الغاشية", "الفجر", "البلد",
    "الشمس", "الليل", "الضحى", "الشرح", "التين", "العلق", "القدر", "البينة", "الزلزلة", "العاديات",
    "القارعة", "التكاثر", "العصر", "الهمزة", "الفيل", "قريش", "الماعون", "الكوثر", "الكافرون", "النصر",
    "المسد", "الإخلاص", "الفلق", "الناس"
]

# ==================== حالة البث (تُعرض في اللوحة الحية) ====================
stream_state = {
    "status": "جاري التهيئة...",
    "is_streaming": False,
    "current_surah_index": 0,
    "current_surah_name": "لم يبدأ بعد",
    "next_surah_name": "الفاتحة",
    "current_file": "-",
    "duration_seconds": 0.0,
    "started_at_ts": 0.0,
    "completed_khatmas": 0,
    "server_start_ts": time.time(),
    "last_ping_time": "لم يتم استقبال طلبات بعد",
    "ping_count": 0,
    "last_error": None,
}

# إعداد مسارات الفيديوهات (1 إلى 114)
video_files = []
for i in range(1, 115):
    file_name = f"{str(i).zfill(3)}.mp4"
    if 1 <= i <= 50:
        video_files.append((i, f"vid/{file_name}"))
    elif 51 <= i <= 100:
        video_files.append((i, f"vid2/{file_name}"))
    else:
        video_files.append((i, f"vid3/{file_name}"))


# ==================== دوال التحميل وإدارة الملفات ====================
async def download_videos_from_drive(url: str, output_dir: str, clean_old_dir: str = None):
    """تحميل مجلد من Google Drive إلى مسار محدد مع مسح المجلد القديم لتوفير المساحة"""
    if not url:
        logger.warning(f"رابط المجلد الخاص بـ {output_dir} غير موجود في متغيرات البيئة!")
        return

    if clean_old_dir and os.path.exists(clean_old_dir):
        try:
            shutil.rmtree(clean_old_dir)
            logger.info(f"تم حذف المجلد القديم {clean_old_dir} لتوفير المساحة على Render.")
        except Exception as e:
            logger.error(f"خطأ أثناء حذف {clean_old_dir}: {e}")

    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"بدأ تحميل الفيديوهات إلى المجلد: {output_dir} ...")

    process = await asyncio.create_subprocess_exec(
        "gdown", "--folder", url, "-O", output_dir, "--remaining-ok",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        logger.info(f"اكتمل تحميل المجلد {output_dir} بنجاح.")
    else:
        logger.warning(f"انتهى gdown للمجلد {output_dir} مع ملاحظات: {stderr.decode(errors='ignore')[:300]}")


async def download_file(url: str, filename: str):
    """تحميل ملف الجلسة .session بأمان"""
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        logger.info(f"الملف {filename} موجود مسبقاً.")
        return

    if not url:
        raise ValueError("متغير البيئة SESSION_URL غير مضبوط!")

    logger.info(f"جاري تحميل ملف الجلسة {filename} ...")
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(filename, "wb") as f:
                    f.write(await response.read())
                logger.info(f"تم تحميل {filename} بنجاح.")
            else:
                raise RuntimeError(f"فشل تحميل {filename} - كود الاستجابة: {response.status}")


async def get_video_duration(filename: str) -> float:
    """حساب مدة الفيديو بدقة عبر ffprobe دون استهلاك الذاكرة العشوائية (RAM)"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filename,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        duration_str = stdout.decode().strip()
        if duration_str:
            return float(duration_str)
    except Exception as e:
        logger.warning(f"تعذر حساب المدة بـ ffprobe، جاري استخدام moviepy: {e}")

    # خيار احتياطي آمن مع إغلاق الملف فوراً لمنع تسريب الذاكرة
    from moviepy.editor import VideoFileClip
    with VideoFileClip(filename) as clip:
        return float(clip.duration)


# ==================== المحرك الرئيسي للبث المباشر ====================
async def start_video_stream():
    prefetch_task = None
    try:
        stream_state["status"] = "جاري تحميل ملف الجلسة والدفعة الأولى من الفيديوهات..."
        await download_file(SESSION_URL, "my_account.session")
        await download_videos_from_drive(FOLDER_URL_1, "vid")

        stream_state["status"] = "جاري الاتصال بتيلغرام وتشغيل PyTgCalls..."
        app = Client(
            "my_account",
            api_id=API_ID,
            api_hash=API_HASH,
            phone_number=PHONE_NUMBER,
        )
        pytgcalls = PyTgCalls(app)

        await app.start()
        await pytgcalls.start()

        chat = await app.get_chat(CHANNEL_ID)
        logger.info(f"تم الاتصال بالقناة بنجاح: {chat.title} ({chat.id})")

        while True:
            for surah_num, video_path in video_files:
                surah_name = SURAH_NAMES[surah_num - 1]
                next_surah_name = SURAH_NAMES[surah_num % 114]

                # التحميل المسبق في الخلفية قبل انتهاء الدفعة الحالية لمنع توقف البث
                if surah_num == 45:
                    prefetch_task = asyncio.create_task(
                        download_videos_from_drive(FOLDER_URL_2, "vid2")
                    )
                elif surah_num == 51 and prefetch_task:
                    await prefetch_task
                    shutil.rmtree("vid", ignore_errors=True)
                elif surah_num == 90:
                    prefetch_task = asyncio.create_task(
                        download_videos_from_drive(FOLDER_URL_3, "vid3")
                    )
                elif surah_num == 101 and prefetch_task:
                    await prefetch_task
                    shutil.rmtree("vid2", ignore_errors=True)

                if not os.path.exists(video_path):
                    logger.warning(f"الملف {video_path} غير موجود، يتم التخطي...")
                    await asyncio.sleep(2)
                    continue

                try:
                    duration = await get_video_duration(video_path)

                    # تحديث بيانات اللوحة الحية
                    stream_state.update({
                        "status": "يبث مباشرة الآن 🟢",
                        "is_streaming": True,
                        "current_surah_index": surah_num,
                        "current_surah_name": f"سورة {surah_name}",
                        "next_surah_name": f"سورة {next_surah_name}",
                        "current_file": video_path,
                        "duration_seconds": round(duration, 1),
                        "started_at_ts": time.time(),
                        "last_error": None,
                    })

                    # بدء أو تبديل البث المباشر للفيديو في القناة
                    await pytgcalls.play(
                        chat.id,
                        MediaStream(video_path),
                    )
                    logger.info(f"بدأ بث: سورة {surah_name} ({video_path}) - المدة: {duration:.1f} ثانية")

                    # الانتظار طوال مدة الفيديو
                    await asyncio.sleep(duration + 2)

                except Exception as e:
                    err_msg = str(e)
                    logger.error(f"حدث خطأ أثناء بث {video_path}: {err_msg}")
                    stream_state["last_error"] = err_msg
                    await asyncio.sleep(5)

            # عند إتمام الـ 114 سورة، نزيد عداد الختمات ونعيد تحميل الدفعة الأولى
            stream_state["completed_khatmas"] += 1
            stream_state["status"] = "اكتملت الختمة، جاري تحضير الختمة الجديدة..."
            await download_videos_from_drive(FOLDER_URL_1, "vid", clean_old_dir="vid3")

    except asyncio.CancelledError:
        logger.info("تم إيقاف مهمة البث المباشر.")
    except Exception as e:
        logger.critical(f"خطأ حرج في محرك البث: {e}")
        stream_state["status"] = f"توقف بسبب خطأ: {e}"
        stream_state["is_streaming"] = False
        stream_state["last_error"] = str(e)


# ==================== تطبيق FastAPI واللوحة الحية ====================
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # تشغيل البث تلقائياً في الخلفية فور إقلاع السيرفر
    stream_task = asyncio.create_task(start_video_stream())
    yield
    stream_task.cancel()


web_app = FastAPI(title="لوحة البث المباشر للقرآن الكريم", lifespan=lifespan)


def format_seconds(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hrs, rem = divmod(seconds, 3600)
    mins, secs = divmod(rem, 60)
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


@web_app.get("/ping")
async def ping():
    """نقطة اتصال خفيفة جداً للمهام الخارجية (Cron Job) لمنع الخمول في Render"""
    stream_state["ping_count"] += 1
    stream_state["last_ping_time"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return JSONResponse({
        "ok": True,
        "status": stream_state["status"],
        "current_surah": stream_state["current_surah_name"],
        "ping_count": stream_state["ping_count"],
    })


@web_app.get("/api/status")
async def api_status():
    """بيانات JSON لتحديث اللوحة الحية تلقائياً بدون إعادة تحميل الصفحة"""
    now = time.time()
    elapsed = 0.0
    remaining = 0.0
    progress_pct = 0.0

    if stream_state["is_streaming"] and stream_state["duration_seconds"] > 0:
        elapsed = min(now - stream_state["started_at_ts"], stream_state["duration_seconds"])
        remaining = max(stream_state["duration_seconds"] - elapsed, 0.0)
        progress_pct = round((elapsed / stream_state["duration_seconds"]) * 100, 1)

    uptime_sec = now - stream_state["server_start_ts"]

    return {
        **stream_state,
        "channel_id": CHANNEL_ID,
        "elapsed_formatted": format_seconds(elapsed),
        "remaining_formatted": format_seconds(remaining),
        "duration_formatted": format_seconds(stream_state["duration_seconds"]),
        "progress_pct": progress_pct,
        "uptime_formatted": format_seconds(uptime_sec),
    }


@web_app.get("/", response_class=HTMLResponse)
async def dashboard():
    """لوحة تحكم عربية تفاعلية تعرض تفاصيل البث المباشر لحظياً"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>لوحة البث المباشر للقرآن الكريم</title>
        <style>
            :root {
                --bg: #0f172a;
                --card: #1e293b;
                --accent: #10b981;
                --text: #f8fafc;
                --muted: #94a3b8;
            }
            * { box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            body {
                margin: 0; padding: 24px;
                background-color: var(--bg); color: var(--text);
                display: flex; justify-content: center; align-items: center; min-height: 100vh;
            }
            .container {
                width: 100%; max-width: 720px;
                background: var(--card); border-radius: 16px;
                padding: 28px; box-shadow: 0 20px 40px rgba(0,0,0,0.4);
                border: 1px solid rgba(255,255,255,0.08);
            }
            .header {
                display: flex; justify-content: space-between; align-items: center;
                border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 16px; margin-bottom: 24px;
            }
            .title { font-size: 1.4rem; font-weight: 700; margin: 0; }
            .badge {
                background: rgba(16, 185, 129, 0.15); color: var(--accent);
                padding: 6px 14px; border-radius: 999px; font-weight: 600; font-size: 0.9rem;
            }
            .surah-box {
                text-align: center; background: rgba(15, 23, 42, 0.6);
                padding: 24px; border-radius: 12px; margin-bottom: 20px;
            }
            .surah-label { color: var(--muted); font-size: 0.95rem; margin-bottom: 8px; }
            .surah-name { font-size: 2.2rem; font-weight: 800; color: var(--accent); margin: 4px 0 16px; }
            .progress-bar {
                width: 100%; height: 10px; background: #334155;
                border-radius: 999px; overflow: hidden; margin-bottom: 10px;
            }
            .progress-fill {
                height: 100%; background: linear-gradient(90deg, #059669, #10b981);
                width: 0%; transition: width 0.5s ease;
            }
            .time-row {
                display: flex; justify-content: space-between; color: var(--muted); font-size: 0.9rem;
            }
            .grid {
                display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 14px; margin-top: 20px;
            }
            .stat-card {
                background: rgba(15, 23, 42, 0.45); padding: 14px 18px;
                border-radius: 10px; border: 1px solid rgba(255,255,255,0.05);
            }
            .stat-label { color: var(--muted); font-size: 0.85rem; margin-bottom: 6px; }
            .stat-value { font-size: 1.05rem; font-weight: 700; }
            .error-box {
                margin-top: 16px; padding: 12px; border-radius: 8px;
                background: rgba(239, 68, 68, 0.15); color: #fca5a5; display: none; font-size: 0.9rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="title">📡 لوحة البث القرآني المباشر</h1>
                <span class="badge" id="status-badge">جاري التحميل...</span>
            </div>

            <div class="surah-box">
                <div class="surah-label">السورة التي تُبث الآن (<span id="surah-num">0</span> / 114)</div>
                <div class="surah-name" id="surah-name">...</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="progress-fill"></div>
                </div>
                <div class="time-row">
                    <span>المنقضي: <strong id="elapsed">00:00</strong></span>
                    <span>المدة الكلية: <strong id="duration">00:00</strong></span>
                    <span>المتبقي: <strong id="remaining">00:00</strong></span>
                </div>
            </div>

            <div class="grid">
                <div class="stat-card">
                    <div class="stat-label">السورة القادمة</div>
                    <div class="stat-value" id="next-surah">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">القناة المستهدفة</div>
                    <div class="stat-value" id="channel-id">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">عدد الختمات المكتملة</div>
                    <div class="stat-value" id="khatmas">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">مدة تشغيل السيرفر (Uptime)</div>
                    <div class="stat-value" id="uptime">00:00</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">طلبات منع الخمول (Pings)</div>
                    <div class="stat-value" id="pings">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">آخر طلب منع خمول</div>
                    <div class="stat-value" id="last-ping" style="font-size:0.85rem;">-</div>
                </div>
            </div>

            <div class="error-box" id="error-box"></div>
        </div>

        <script>
            async function fetchStatus() {
                try {
                    const res = await fetch('/api/status');
                    const data = await res.json();
                    document.getElementById('status-badge').textContent = data.status;
                    document.getElementById('surah-num').textContent = data.current_surah_index;
                    document.getElementById('surah-name').textContent = data.current_surah_name;
                    document.getElementById('next-surah').textContent = data.next_surah_name;
                    document.getElementById('channel-id').textContent = data.channel_id;
                    document.getElementById('khatmas').textContent = data.completed_khatmas;
                    document.getElementById('uptime').textContent = data.uptime_formatted;
                    document.getElementById('elapsed').textContent = data.elapsed_formatted;
                    document.getElementById('duration').textContent = data.duration_formatted;
                    document.getElementById('remaining').textContent = data.remaining_formatted;
                    document.getElementById('progress-fill').style.width = data.progress_pct + '%';
                    document.getElementById('pings').textContent = data.ping_count;
                    document.getElementById('last-ping').textContent = data.last_ping_time;

                    const errBox = document.getElementById('error-box');
                    if (data.last_error) {
                        errBox.style.display = 'block';
                        errBox.textContent = 'تنبيه آخر خطأ مسجل: ' + data.last_error;
                    } else {
                        errBox.style.display = 'none';
                    }
                } catch (e) {
                    console.error(e);
                }
            }
            fetchStatus();
            setInterval(fetchStatus, 2000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:web_app", host="0.0.0.0", port=PORT, log_level="info")