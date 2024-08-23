from telethon import TelegramClient, events
import socks
import os
import subprocess
import logging
import yt_dlp
import nest_asyncio
import gradio as gr
import asyncio
import requests

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


async def main():
    # إعداد FFmpeg لبث الصوت فقط
    def stream_audio(audio_path):
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
            .run()
        )

    proxy_server = '188.165.192.99'
    proxy_port = 63615
    # proxy_secret = 'ee32b920dffb51643028e2f6b878d4eac1666172616b61762e636f6d'
    proxy_dc_id = 2  # This is usually 2 for MTProto proxies
    
    proxy = (
        socks.SOCKS5,
        proxy_server,
        proxy_port,
        # True,
        # 'vpn',
        # 'unlimited'
    )
    # إعداد البوت باستخدام Telethon مع استخدام البروكسي
    client = TelegramClient(
        'bot',
        API_ID,
        API_HASH,
        
        proxy=proxy
    )

    @client.on(events.NewMessage(pattern='/start'))
    async def start(event):
        await event.respond('أرسل رابط YouTube لبدء البث.')

    @client.on(events.NewMessage)
    async def handle_message(event):
        url = event.message.text
        await event.respond("URL: " + url)
        try:
            # تحميل الفيديو باستخدام yt-dlp
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': 'downloaded_audio.%(ext)s',
                # 'cookiefile': 'cookies.txt',  # إذا كنت تستخدم ملفات تعريف الارتباط
                # 'ratelimit': 1000000,  # تحديد الحد الأقصى لسرعة التحميل
                # 'sleep_interval': 10,  # تأخير بين تحميلات كل جزء
                # 'max_sleep_interval': 20
                'username': os.environ['GUser'],  # استبدل YOUR_USERNAME باسم المستخدم الخاص بك
                'password': os.environ['GPass'], 
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                audio_path = ydl.prepare_filename(info_dict)

            # أرسل رسالة لتأكيد بدء التحميل والبث
            await event.respond('تم تحميل الصوت، جاري بدء البث...')

            # بدء بث الصوت باستخدام FFmpeg
            stream_audio(audio_path)

            # إرسال رسالة عند انتهاء البث
            await event.respond('تم الانتهاء من البث!')
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            await event.respond(f"Error occurred: {e}")
            await event.respond('حدث خطأ أثناء محاولة البث.')

    await client.start(bot_token=BOT_TOKEN)
    print("Bot is running...")
    await client.run_until_disconnected()

# if __name__ == "__main__":
#     loop = asyncio.get_event_loop()
#     loop.create_task(main())
#     loop.run_forever()
inputs = []
output = "text"
gr.Interface(fn=main, inputs=inputs, outputs=output).launch(server_name="0.0.0.0",server_port=10000)
