import time
import requests
import datetime
from bs4 import BeautifulSoup
import tweepy
from flask import Flask
import threading

# ==== Flask web server to keep Replit alive ====
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask).start()

# ==== Twitter API credentials ====
API_KEY = '3tYRgurBzolDQXMnDEzAl8wNy'
API_SECRET = 'cNtlsR3CmoVI6ptPDXsni4Q77wsJwCaZP6oSQlwY5vTLUstbI0'
ACCESS_TOKEN = '1938302658538012673-YTeQGk4BNnzdF1bz3PwYOjDE3plhzo'
ACCESS_SECRET = 'qcNzRQXlW6T0qgxDAMk9vXTwNx53DTtz90WCB8OJSkHBU'

# ==== Set up Twitter client ====
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

# ==== ChronicleLive RSS feed ====
FEED_URL = 'https://www.chroniclelive.co.uk/news/?service=rss'

# Track posted links and post count
posted_articles = set()
daily_post_count = 0
last_post_day = None

def is_posting_time():
    now = datetime.datetime.now()
    return now.hour >= 7 and now.hour < 12  # ✅ Post from 7 AM to 12 PM

def reset_daily_counter():
    global daily_post_count, last_post_day
    today = datetime.date.today()
    if last_post_day != today:
        daily_post_count = 0
        last_post_day = today

def fetch_latest_article():
    response = requests.get(FEED_URL)
    soup = BeautifulSoup(response.content, 'xml')
    items = soup.find_all('item')

    for item in items:
        pub_date_str = item.find('pubDate').text
        link = item.find('link').text.strip()

        if link in posted_articles:
            continue

        pub_date = datetime.datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
        pub_date_local = pub_date.astimezone().replace(tzinfo=None)

        seven_am_today = datetime.datetime.combine(datetime.date.today(), datetime.time(7, 0))
        if pub_date_local < seven_am_today:
            continue

        posted_articles.add(link)

        article_html = requests.get(link).text
        article_soup = BeautifulSoup(article_html, 'html.parser')

        headline_tag = article_soup.find('h1')
        if not headline_tag:
            continue
        headline = headline_tag.text.strip()

        img_tag = article_soup.find('img')
        if not img_tag or not img_tag.get('src'):
            continue
        image_url = img_tag['src']

        hashtags = (
            "#NorthEastNews #UKNews #BreakingNews #LocalNews #NewsUpdate #InTheNews\n"
            "#NorthEastUK #NorthEastEngland #NEEngland #GeordieNews #TyneAndWear\n"
            "#CountyDurham #TeessideNews #SunderlandNews #NewcastleNews\n"
            "#WhatYouNeedToKnow #StayInformed #CommunityUpdates #LiveUpdates\n"
            "#OnTheGround #HappeningNow"
        )

        tweet_text = f"{headline}\n\n{hashtags}"

        return {
            'text': tweet_text,
            'image_url': image_url
        }

    return None

def post_to_twitter(article):
    global daily_post_count

    img_data = requests.get(article['image_url']).content
    with open('temp.jpg', 'wb') as f:
        f.write(img_data)

    media = api.media_upload('temp.jpg')
    api.update_status(status=article['text'], media_ids=[media.media_id])
    print("✅ Posted:", article['text'].splitlines()[0])
    daily_post_count += 1

# ==== MAIN LOOP ====
if __name__ == '__main__':
    while True:
        try:
            reset_daily_counter()

            if is_posting_time() and daily_post_count < 16:
                article = fetch_latest_article()
                if article:
                    post_to_twitter(article)
            else:
                print("⏳ Waiting: outside posting window or limit reached.")

        except Exception as e:
            print("⚠️ Error:", str(e))

        time.sleep(300)  # Check every 5 minutes
