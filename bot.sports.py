import time
import telebot
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from threading import Timer

# Ваш API ключ для Telegram
TELEGRAM_BOT_TOKEN = '6618460537:AAFNc6-KewtnwuH_9KktxcvD7fVZRIjh4FE'

# Инициализация Telegram бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# URL RSS-ленты
RSS_FEED_URL = 'https://news.mail.ru/rss/sport/'

# Временная метка последней отправленной новости
last_sent_time = datetime.utcnow() - timedelta(hours=12)

# Очередь для хранения новых новостей
news_queue = []


def get_html_content(url):
    """Получение HTML контента по URL"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching the URL {url}: {e}")
        return None


def extract_image_url(html_content, class_name):
    """Извлечение URL изображения из HTML контента"""
    soup = BeautifulSoup(html_content, 'html.parser')
    img = soup.find('img', class_=class_name)
    return img['src'] if img else None


def extract_div_text(html_content, class_names):
    """Извлечение текста из последнего <div> с заданными классами"""
    soup = BeautifulSoup(html_content, 'html.parser')
    divs = soup.find_all('div', class_=class_names)
    if divs:
        last_div = divs[-1]
        p = last_div.find('p')
        return p.get_text() if p else ""
    return ""


def get_latest_news():
    """Получение последних новостей из RSS-ленты"""
    feed = feedparser.parse(RSS_FEED_URL)
    articles = []

    now = datetime.utcnow()
    for entry in feed.entries:
        published_time = datetime(*entry.published_parsed[:6])
        if published_time > last_sent_time:
            url = entry.link
            html_content = get_html_content(url)
            if html_content:
                image_url = extract_image_url(html_content, 'af30e1399f')
                div_text = extract_div_text(html_content, ['d4d7f9cef4', 'df068f8f97'])
                articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'image_url': image_url,
                    'div_text': div_text,
                    'description': entry.summary
                })

    return articles


def check_for_new_articles():
    """Проверка новых новостей и добавление их в очередь"""
    global last_sent_time
    articles = get_latest_news()
    if articles:
        news_queue.extend(articles)
        last_sent_time = datetime.utcnow()
        print(f"Added {len(articles)} articles to the queue.")

    Timer(10, check_for_new_articles).start()  # Проверка каждые 10 секунд


def send_news_from_queue():
    """Отправка новостей из очереди"""
    if news_queue:
        article = news_queue.pop(0)
        caption = f"{article['title']}\n\n{article['description']}\n\n{article['div_text']}"

        try:
            if article['image_url']:
                bot.send_photo(
                    chat_id=-1002174719581,
                    photo=article['image_url'],
                    caption=caption,
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(
                    chat_id=-1002174719581,
                    text=caption,
                    parse_mode='Markdown'
                )
            print(f"Sent article: {article['title']}")
        except Exception as e:
            print(f"Error sending message: {e}")

        Timer(10, send_news_from_queue).start()  # Отправка каждые 10 секунд


def main():
    """Запуск функций бота"""
    check_for_new_articles()
    send_news_from_queue()
    try:
        bot.polling()
    except Exception as e:
        print(f"Error in bot polling: {e}")
        time.sleep(15)
        main()


if __name__ == "__main__":
    main()
