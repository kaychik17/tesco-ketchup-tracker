import os
import json
import requests
import time
from bs4 import BeautifulSoup
import telegram

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
URL = "https://www.tesco.ie/groceries/en-IE/shop/food-cupboard/condiments-table-sauces-olives-and-pickles/ketchup"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

def send_report(message):
    bot = telegram.Bot(token=TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=message)

def fetch_products():
    time.sleep(2)  # Anti-bot delay
    r = requests.get(URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "lxml")
    items = soup.select("div.product")
    products = []
    for item in items:
        title = item.select_one(".product-title")
        price_tag = item.select_one(".value")
        link_tag = item.select_one("a")
        if title and price_tag and link_tag:
            name = title.get_text(strip=True)
            price = float(price_tag.get_text(strip=True).replace("€", "").replace(",", "."))
            link = "https://www.tesco.ie" + link_tag["href"]
            products.append({"name": name, "price": price, "link": link})
    return products

def load_old_data():
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            return json.load(f)
    return []

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)

def compare_and_notify(current, previous):
    report = "🛒 Tesco Ketchup Tracker:\n\n"
    previous_map = {p['name']: p for p in previous}
    current_names = {p['name'] for p in current}
    previous_names = {p['name'] for p in previous}

    new_items = [p for p in current if p['name'] not in previous_names]
    if new_items:
        report += "🆕 New products:\n"
        for p in new_items:
            report += f"- {p['name']} – €{p['price']:.2f}\n"

    removed_items = previous_names - current_names
    if removed_items:
        report += "\n❌ Removed products:\n"
        for name in removed_items:
            report += f"- {name}\n"

    for p in current:
        if p['name'] in previous_map:
            old_price = previous_map[p['name']]['price']
            if old_price != p['price']:
                diff = p['price'] - old_price
                sign = "🔺" if diff > 0 else "🔻"
                report += f"\n{sign} {p['name']}: €{old_price:.2f} → €{p['price']:.2f} ({'+' if diff > 0 else ''}{diff:.2f})"

    if report.strip() != "🛒 Tesco Ketchup Tracker:":
        send_report(report)

def main():
    current = fetch_products()
    previous = load_old_data()
    compare_and_notify(current, previous)
    save_data(current)

if __name__ == "__main__":
    main()
