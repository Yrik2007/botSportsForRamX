import time
import telebot
import feedparser
from datetime import datetime, timedelta
from threading import Timer
import json
import os

# Ваш API ключ для Telegram
TELEGRAM_BOT_TOKEN = '6618460537:AAFNc6-KewtnwuH_9KktxcvD7fVZRIjh4FE'

# Инициализация Telegram бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# URL RSS-ленты
RSS_FEED_URL = 'https://news.mail.ru/rss/sport/'

# Путь к файлу для сохранения последней отправленной новости
LAST_SENT_FILE = 'last_sent.json'

# Очередь для хранения новых новостей
news_queue = []

def save_last_sent_time(last_sent_time):
    """Сохранение временной метки последней отправленной новости в файл"""
    with open(LAST_SENT_FILE, 'w') as file:
        json.dump({'last_sent_time': last_sent_time.isoformat()}, file)

def load_last_sent_time():
    """Загрузка временной метки последней отправленной новости из файла"""
    if os.path.exists(LAST_SENT_FILE):
        with open(LAST_SENT_FILE, 'r') as file:
            data = json.load(file)
            return datetime.fromisoformat(data['last_sent_time'])
    else:
        return datetime.utcnow() - timedelta(hours=12)

# Инициализация временной метки последней отправленной новости
last_sent_time = load_last_sent_time()

def get_latest_news():
    """Получение последних новостей из RSS-ленты"""
    feed = feedparser.parse(RSS_FEED_URL)
    articles = []
    for entry in reversed(feed.entries[:10]):  # Получаем только последние 10 новостей
        published_time = datetime(*entry.published_parsed[:6])
        if published_time > last_sent_time:
            articles.append({
                'title': entry.title,
                'description': entry.summary,
                'published_time': published_time
            })
    return articles

def check_for_new_articles():
    """Проверка новых новостей и добавление их в очередь"""
    global last_sent_time
    articles = get_latest_news()
    if articles:
        news_queue.extend(articles)
        last_sent_time = max(article['published_time'] for article in articles)
        save_last_sent_time(last_sent_time)
        print(f"Added {len(articles)} articles to the queue.")

    Timer(600, check_for_new_articles).start()  # Проверка каждые 10 минут

def send_news_from_queue():
    """Отправка новостей из очереди"""
    if news_queue:
        article = news_queue.pop(0)
        caption = f"{article['title']}\n\n{article['description']}"

        try:
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
