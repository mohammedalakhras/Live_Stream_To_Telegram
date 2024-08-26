from telethon import TelegramClient, events
import socks
import os
import logging
import asyncio
import requests
import ffmpeg
import subprocess
import nest_asyncio
import http.server
import socketserver
import threading

nest_asyncio.apply()

def download_file(url, filename):
    response = requests.get(url)
    with open(filename, 'wb') as file:
        file.write(response.content)

# إعداد معلومات البوت والقناة
API_ID = os.environ['API_ID']
API_HASH = os.environ['API_HASH']
BOT_TOKEN = os.environ['TOKEN']
SERVER_URL = os.environ['SERVER_URL']
STREAM_KEY = os.environ['STREAM_KEY']
sessionFile = os.environ['sessionUrlFile']
Cookies = os.environ['cookies']

download_file(sessionFile, 'bot.session')
download_file(Cookies, 'cookies.txt')

# قائمة الملفات التي سيتم تحميلها وبثها
file_base_url = "https://archive.org/download/MishariAl-afasi/"
file_range = list(range(1, 115))  # الأرقام من 1 إلى 114
file_list = [f"{str(i).zfill(3)}.mp3" for i in file_range]  # توليد أسماء الملفات مع الصفر في البداية

async def main():
    def stream_audio(audio_path):
        # result = subprocess.run(['which', 'ffmpeg'], stdout=subprocess.PIPE)
        # ffmpeg_path = result.stdout.decode().strip()
        # بث الصوت باستخدام FFmpeg
        (
            ffmpeg
            .input(audio_path, re=None)  # قراءة الملف بالوقت الحقيقي
            .output(
                SERVER_URL + STREAM_KEY,  # رابط البث
                format='flv',  # صيغة الإخراج
                acodec='aac',  # ترميز الصوت
                audio_bitrate='128k',  # معدل البت للصوت
                vn=None  # تجاهل الفيديو
            )
            .run(cmd="/bin/bash" , capture_stderr=True)
        )

    proxy_server = '188.165.192.99'
    proxy_port = 63615
    proxy_dc_id = 2  # This is usually 2 for MTProto proxies

    proxy = (
        socks.SOCKS5,
        proxy_server,
        proxy_port,
    )

    # إعداد البوت باستخدام Telethon مع استخدام البروكسي
    client = TelegramClient(
        'bot',
        API_ID,
        API_HASH,
        # proxy=proxy
    )

    @client.on(events.NewMessage(pattern='/start'))
    async def start(event):
        await event.respond('سيتم بدء بث ملفات القرآن الكريم بشكل متتابع.')

    @client.on(events.NewMessage)
    async def handle_message(event):
        try:
            while True:
                for file_name in file_list:
                    url = file_base_url + file_name
                    download_file(url, 'current_audio.mp3')  # تحميل الملف الحالي
                    await event.respond(f"جاري بث الملف: {file_name}")

                    # بث الصوت باستخدام FFmpeg
                    stream_audio('current_audio.mp3')

                    # حذف الملف بعد الانتهاء من البث
                    os.remove('current_audio.mp3')

                # إعادة الدورة بعد الانتهاء من جميع الملفات
                await event.respond("تم الانتهاء من بث جميع الملفات، سيتم إعادة الدورة من البداية.")

        except Exception as e:
            logging.error(f"Error occurred: {e}")
            await event.respond(f"Error occurred: {e}")
            await event.respond('حدث خطأ أثناء محاولة البث.')

    await client.start(bot_token=BOT_TOKEN)
    print("Bot is running...")
    await client.run_until_disconnected()
def run_dummy_server():
    PORT = 1000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()
if __name__ == "__main__":
    # تشغيل خادم ويب بسيط في خيط منفصل
    server_thread = threading.Thread(target=run_dummy_server)
    server_thread.start()
    asyncio.run(main())
