import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
import schedule
from PIL import Image
from io import BytesIO
from telegram import Bot, InputMediaPhoto
from config import BOT_TOKEN, CHANNEL_ID

# Initialize Bot
bot = Bot(token=BOT_TOKEN)
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# Telegram Channel Posting
def post_to_telegram(image_url, caption):
    try:
        img_data = requests.get(image_url).content
        photo = BytesIO(img_data)
        photo.name = "deal.jpg"
        bot.send_photo(chat_id=CHANNEL_ID, photo=photo, caption=caption, parse_mode='HTML')
        print("[✓] Posted on Telegram")
    except Exception as e:
        print("Telegram Error:", e)

# Flipkart Loot Deals Scraper
def scrape_flipkart():
    search_urls = [
        "https://www.flipkart.com/search?q=men+tshirt+under+100",
        "https://www.flipkart.com/search?q=grocery+under+99",
        "https://www.flipkart.com/search?q=electronics+under+199"
    ]
    try:
        for url in search_urls:
            r = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(r.content, "lxml")
            items = soup.select("a._1fQZEK, a.IRpwTa, a._2rpwqI")
            count = 0
            for item in items:
                if count >= 1: break  # Only one deal per category
                href = item.get("href")
                full_url = f"https://www.flipkart.com{href}"
                title = item.text[:100] + "..."
                image_tag = item.find("img")
                image = "https:" + image_tag["src"] if image_tag and "src" in image_tag.attrs else "https://via.placeholder.com/300.png"

                price_tag = item.select_one("._30jeq3")
                price = price_tag.text if price_tag else "Price Not Found"

                caption = f"<b>Flipkart Loot Deal</b>\n\n{title}\nPrice: {price}\n\n<a href='{full_url}'>Buy Now</a>\n#Flipkart #Loot #Deals"
                post_to_telegram(image, caption)
                count += 1
                time.sleep(10)
    except Exception as e:
        print("Flipkart Error:", e)

# Telegram Loot Channels
TELEGRAM_CHANNELS = [
    "https://t.me/bigsavings_lootdeals",
    "https://t.me/Loot_DealsX",
    "https://t.me/+Th6aG5Zaxz_i_u7a",
    "https://t.me/TrickXpert",
    "https://t.me/+LNRQ0Y1-9RkzZDRl",
    "https://t.me/+AdUPh392S6xhNmY1"
]

def scrape_telegram_channels():
    for url in TELEGRAM_CHANNELS:
        try:
            page = requests.get(url).text
            soup = BeautifulSoup(page, 'html.parser')
            msgs = soup.find_all('a', href=True)
            for msg in msgs[:1]:  # Only 1 deal per channel
                link = msg['href']
                if "http" in link:
                    deal_text = msg.text[:100] + "..."
                    image_url = "https://via.placeholder.com/300x300.png?text=Loot+Deal"  # fallback image
                    caption = f"<b>Loot Deal</b>\n\n{deal_text}\n\n<a href='{link}'>Buy Now</a>\n#Loot #Offer"
                    post_to_telegram(image_url, caption)
                    time.sleep(10)
        except Exception as e:
            print("Telegram Scrape Error:", e)

# Schedule & Run
def start_scheduled_bot():
    schedule.every(2).hours.do(scrape_flipkart)
    schedule.every().hour.do(scrape_telegram_channels)

    print("Bot started... Posting deals.")
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    start_scheduled_bot()
