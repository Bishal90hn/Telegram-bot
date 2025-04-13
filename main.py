import feedparser
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from PIL import Image
import io
import schedule
import time
import telegram
import random
from datetime import datetime
import json
import os
from urllib.parse import urljoin
from free_proxy import FreeProxy

# Configuration
TELEGRAM_TOKEN = "7896793670:AAGILbEyLmVLuYfBFKFR5aMof2PaLNtGIC4"
CHANNEL_ID = "@AiSamacharExpress"
RSS_FEEDS = {
    "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-latest",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml"
}
PROXY_LIST = FreeProxy().get_proxy_list()  # Fetch proxies dynamically
POSTED_NEWS_FILE = "posted_news.json"
POST_INTERVAL = 15  # Minutes

# Initialize Telegram bot
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Load posted news to avoid duplicates
def load_posted_news():
    if os.path.exists(POSTED_NEWS_FILE):
        with open(POSTED_NEWS_FILE, "r") as f:
            return json.load(f)
    return []

# Save posted news
def save_posted_news(news):
    with open(POSTED_NEWS_FILE, "w") as f:
        json.dump(news, f)

# Get a random proxy
def get_random_proxy():
    return random.choice(PROXY_LIST) if PROXY_LIST else None

# Fetch Google Trends
def fetch_google_trends():
    url = "https://trends.google.co.in/trends/trendingsearches/daily?geo=IN"
    proxy = get_random_proxy()
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        trends = []
        for trend in soup.select(".trends .title a")[:5]:  # Top 5 trends
            trends.append({"title": trend.text.strip(), "link": urljoin(url, trend["href"])})
        return trends
    except Exception as e:
        print(f"Error fetching trends: {e}")
        return []

# Fetch RSS news
def fetch_rss_news():
    news_items = []
    for source, rss_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:3]:  # Top 3 per source
                news_items.append({
                    "title": entry.title,
                    "description": entry.get("summary", entry.title),
                    "link": entry.link,
                    "source": source,
                    "pub_date": entry.get("published", "")
                })
        except Exception as e:
            print(f"Error fetching {source}: {e}")
    return news_items

# Translate text to Hindi
def translate_to_hindi(text):
    try:
        return GoogleTranslator(source="auto", target="hi").translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

# Download and edit image
def get_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        img = Image.open(io.BytesIO(response.content))
        img = img.resize((800, 400), Image.Resampling.LANCZOS)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        return img_byte_arr.getvalue()
    except Exception:
        return None

# Extract image from news page
def extract_image_url(news_url):
    try:
        proxy = get_random_proxy()
        proxies = {"http": proxy, "https": proxy} if proxy else None
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(news_url, headers=headers, proxies=proxies, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        img_tag = soup.find("meta", property="og:image")
        return img_tag["content"] if img_tag else None
    except Exception:
        return None

# Post news to Telegram
def post_news():
    posted_news = load_posted_news()
    news_items = fetch_rss_news()
    trends = fetch_google_trends()

    # Combine news and trends
    for trend in trends:
        news_items.append({
            "title": trend["title"],
            "description": f"ट्रेंडिंग: {trend['title']}",
            "link": trend["link"],
            "source": "Google Trends"
        })

    # Shuffle to mix sources
    random.shuffle(news_items)

    for news in news_items:
        news_id = news["link"]
        if news_id in posted_news:
            continue

        # Translate if needed
        title = translate_to_hindi(news["title"])
        description = translate_to_hindi(news["description"])[:200] + "..."

        # Create professional post
        post_text = (
            f"📰 *{title}* 📰\n\n"
            f"{description}\n\n"
            f"📖 स्रोत: {news['source']}\n"
            f"🔗 पढ़ें: {news['link']}\n"
            f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"#न्यूज़ #भारत #AiSamacharExpress"
        )

        # Get image
        image_url = extract_image_url(news["link"])
        image_data = get_image(image_url) if image_url else None

        try:
            if image_data:
                bot.send_photo(chat_id=CHANNEL_ID, photo=image_data, caption=post_text, parse_mode="Markdown")
            else:
                bot.send_message(chat_id=CHANNEL_ID, text=post_text, parse_mode="Markdown")
            posted_news.append(news_id)
            save_posted_news(posted_news)
            print(f"Posted: {title}")
            break  # Post one news item per cycle
        except Exception as e:
            print(f"Error posting: {e}")

# Schedule posts
schedule.every(POST_INTERVAL).minutes.do(post_news)

# Main loop
if __name__ == "__main__":
    print("Bot started...")
    while True:
        schedule.run_pending()
        time.sleep(60)
