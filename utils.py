# utils.py
import re
from datetime import datetime

def parse_date(date_str):
    try:
        clean_str = date_str.strip()
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', clean_str)
        if match:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        return None
    except:
        return None

def clean_price(price_str):
    if not price_str: return "check site"
    # 移除 "円", ",", "税込" 等字眼
    return re.sub(r'[^\d]', '', price_str) + " 円"