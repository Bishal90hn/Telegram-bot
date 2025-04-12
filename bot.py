import os
import time
import logging
import feedparser
import requests
import tempfile
from telegram import Bot, InputMediaPhoto, InputMediaVideo
from datetime import datetime, timedelta
import random

# ========== कॉन्फिग ==========
TOKEN = "YOUR_TELEGRAM_TOKEN"  # ⚠️ Render/Koyeb के Env Variables में डालें
CHANNEL = "@AiSamacharExpress"
CHECK_INTERVAL = random.randint(900, 1200)  # 15-20 मिनट

# ========== RSS फीड्स (कैटेगरी के हिसाब से) ==========
RSS_FEEDS = {
    "भारतीय समाचार 🇮🇳": "https://www.aajtak.in/rssfeeds/default.aspx",
    "वित्त समाचार 💰": "https://www.moneycontrol.com/rss/business.xml",
    "खेल समाचार ⚽": "https://www.aajtak.in/sports/rssfeed.xml"
}

# ========== लॉगिंग ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== मीडिया डाउनलोडर ==========
def download_media(url):
    try:
        response = requests.get(url, stream=True, timeout=15)
        if response.status_code == 200:
            ext = '.jpg' if 'image' in response.headers.get('content-type','') else '.mp4'
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
                return f.name
    except Exception as e:
        logger.error(f"मीडिया डाउनलोड विफल: {str(e)}")
    return None

# ========== न्यूज़ पोस्टर ==========
def send_news():
    bot = Bot(token=TOKEN)
    try:
        for category, url in RSS_FEEDS.items():
            feed = feedparser.parse(url)
            for entry in feed.entries[:2]:  # हर कैटेगरी से 2 न्यूज़
                # टेक्स्ट तैयार करें (हिंदी फॉर्मेटिंग)
                title = f"<b>{entry.title[:100]}</b>" if len(entry.title) > 100 else f"<b>{entry.title}</b>"
                desc = entry.get('description', '')[:500].split('http')[0]
                message = f"📰 <u>{category}</u>\n\n{title}\n\n{desc}"

                # मीडिया ढूंढें
                media_url = None
                if hasattr(entry, 'media_content'):
                    for media in entry.media_content:
                        if media.get('medium') in ['image','video']:
                            media_url = media['url']
                            break
                
                # पोस्ट भेजें
                if media_url:
                    media_path = download_media(media_url)
                    if media_path:
                        try:
                            if media_path.endswith('.jpg'):
                                bot.send_photo(
                                    chat_id=CHANNEL,
                                    photo=open(media_path, 'rb'),
                                    caption=message,
                                    parse_mode="HTML"
                                )
                            else:
                                bot.send_video(
                                    chat_id=CHANNEL,
                                    video=open(media_path, 'rb'),
                                    caption=message,
                                    parse_mode="HTML",
                                    supports_streaming=True
                                )
                            logger.info(f"✅ {category} - पोस्ट किया")
                        finally:
                            os.unlink(media_path)
                    else:
                        bot.send_message(
                            chat_id=CHANNEL,
                            text=message,
                            parse_mode="HTML"
                        )
                else:
                    bot.send_message(
                        chat_id=CHANNEL,
                        text=message,
                        parse_mode="HTML"
                    )
                
                time.sleep(10)  # Rate Limit से बचें
    except Exception as e:
        logger.error(f"🔥 त्रुटि: {str(e)}")

# ========== मुख्य कोड ==========
if __name__ == '__main__':
    logger.info("🚀 बॉट सक्रिय! (हिंदी न्यूज़ + फाइनेंस + मीडिया)")
    while True:
        try:
            next_run = datetime.now() + timedelta(seconds=CHECK_INTERVAL)
            logger.info(f"⏳ अगली पोस्ट: {next_run.strftime('%H:%M:%S')}")
            
            send_news()
            CHECK_INTERVAL = random.randint(900, 1200)  # नया रैंडम टाइम
            
        except Exception as e:
            logger.critical(f"💀 गंभीर त्रुटि: {str(e)}")
            time.sleep(60)
        finally:
            time.sleep(CHECK_INTERVAL)
