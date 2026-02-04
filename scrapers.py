# scrapers.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
from config import HEADERS  # 從設定檔匯入
from utils import clean_price, parse_date # 從工具箱匯入

# 可以在此處統一管理每個爬蟲最多抓取的項目數量
MAX_ITEMS_PER_SCRAPER = 40

# === 爬蟲 A: Liblo ===
def fetch_liblo(days_to_fetch=0):
    url = "https://goods.liblo.jp/"
    data = []
    try:
        # 只有在 days_to_fetch > 0 時才設定截止日期
        cutoff_date = None
        if days_to_fetch > 0:
            cutoff_date = datetime.now() - timedelta(days=days_to_fetch)

        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status() # 如果請求失敗 (如 404, 500), 會直接拋出異常
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 選擇包含日期和標題的父層元素 article
        entries = soup.select('article.post-list-item')
        for entry in entries:
            date_tag = entry.select_one('time.entry-date')
            title_tag = entry.select_one('.article-title')
            article_link_tag = entry.select_one('a.post-list-link')

            if not (date_tag and title_tag and article_link_tag):
                continue

            # 如果設定了截止日期，才進行過濾
            if cutoff_date:
                item_date = parse_date(date_tag.get_text(strip=True))
                if item_date and item_date < cutoff_date:
                    continue # 如果文章日期早於截止日期，則跳過
            
            data.append({
                "Source": "Liblo (情報)",
                "Title": title_tag.get_text(strip=True),
                "Price": "情報",
                "Link": article_link_tag.get('href')
            })
            # 如果已達最大數量，提前結束迴圈
            if len(data) >= MAX_ITEMS_PER_SCRAPER:
                break

    except Exception as e:
        error_message = f"Liblo 爬取失敗: {e}"
        print(error_message)
        return [{"Source": "Liblo", "Title": f"⚠️ {error_message}", "Price": "-", "Link": url}]
    return data

# === 爬蟲 C: Animate ===
def fetch_animate(days_to_fetch=7):
    url = "https://www.animate-onlineshop.jp/products/list.php?mode=new"
    data = []
    try:
        local_headers = HEADERS.copy()
        local_headers['Referer'] = 'https://www.animate-onlineshop.jp/'
        
        res = requests.get(url, headers=local_headers, timeout=15)
        
        # Animate 網站有較強的反爬機制，特別處理 403/503 錯誤
        if res.status_code in [403, 503]:
            return [{"Source": "Animate", "Title": f"⚠️ 被阻擋 ({res.status_code})，請稍後再試", "Price": "-", "Link": url}]
        
        res.raise_for_status()
        res.encoding = 'utf-8'

        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.item_list li, .main_contents .item')
        
        for item in items[:MAX_ITEMS_PER_SCRAPER]:
            title_tag = item.select_one('h3 a, .item_title a')
            price_tag = item.select_one('.price, .item_price')
            
            if title_tag and title_tag.get('href'):
                link = urljoin(url, title_tag.get('href'))
                data.append({
                    "Source": "Animate (商店)",
                    "Title": title_tag.get_text(strip=True),
                    "Price": clean_price(price_tag.get_text(strip=True)) if price_tag else "-",
                    "Link": link
                })
    except Exception as e:
        error_message = f"Animate 爬取失敗: {e}"
        print(error_message)
        return [{"Source": "Animate", "Title": f"⚠️ {error_message}", "Price": "-", "Link": url}]
    return data