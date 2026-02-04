import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from urllib.parse import urljoin

# ==========================================
# 1. 設定檔與全域變數
# ==========================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
}

# 您可以在這裡自由增加想要監控的作品
KEYWORDS_MAP = {
    "排球少年": ["ハイキュー", "ＨＱ"],
    "藍色監獄": ["ブルーロック", "ブルロ"],
    "咒術迴戰": ["呪術廻戦", "呪術"],
    "間諜家家酒": ["SPY×FAMILY", "スパイファミリー"],
    "吉伊卡哇": ["ちいかわ"],
    "我的英雄學院": ["僕のヒーローアカデミア", "ヒロアカ"],
    "海賊王": ["ONE PIECE", "ワンピース"],
    "銀魂": ["銀魂"],
    "獵人": ["HUNTER×HUNTER"],
    "怪獸8號": ["怪獣8号", "怪獣８号"]
}

# ==========================================
# 2. 工具函數
# ==========================================

def is_match(title, target_keywords):
    """檢查標題是否包含任一目標關鍵字"""
    if not target_keywords: return True 
    for k in target_keywords:
        if k in title:
            return True
    return False

# ==========================================
# 3. 爬蟲邏輯 (Liblo 專用 - 無翻譯版)
# ==========================================

def fetch_liblo(target_count, max_scan_limit, target_keywords, status_container):
    """
    [Liblo] 邊爬邊過濾
    """
    base_url = "https://goods.liblo.jp/"
    current_url = base_url
    
    found_items = []
    total_scanned = 0
    page = 1
    
    while len(found_items) < target_count and total_scanned < max_scan_limit:
        status_container.text(f"正在搜尋第 {page} 頁 (已找到 {len(found_items)}/{target_count} 筆符合)...")
        
        try:
            res = requests.get(current_url, headers=HEADERS, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            entries = soup.select('h1.article-title a, h3.article-title a, div.main-content h3 a')
            
            if not entries:
                break

            for entry in entries:
                if total_scanned >= max_scan_limit: break
                total_scanned += 1
                
                title = entry.get_text(strip=True)
                
                # 關鍵字比對
                if is_match(title, target_keywords):
                    found_items.append({
                        "Title": title, # 日文原名
                        "Link": entry.get('href')
                    })
                    
                    if len(found_items) >= target_count:
                        return found_items

            if len(found_items) >= target_count:
                break

            # 翻頁邏輯
            next_btn = soup.select_one('.pager-next a, .next a, a[rel="next"]')
            if not next_btn:
                links = soup.find_all('a')
                for l in links:
                    if "次へ" in l.get_text() or "Next" in l.get_text():
                        next_btn = l
                        break
            
            if next_btn:
                next_link = next_btn.get('href')
                current_url = urljoin(base_url, next_link)
                page += 1
                time.sleep(1) # 避免翻頁過快
            else:
                break 

        except Exception as e:
            st.error(f"連線錯誤: {e}")
            break
            
    return found_items

# ==========================================
# 4. 主程式介面
# ==========================================

def main():
    st.set_page_config(page_title="動漫情報看板 (Liblo)", layout="wide", page_icon="🎌")
    st.title("🎌 日本動漫情報看板")

    with st.sidebar:
        st.header("⚙️ 搜尋設定")
        
        target_count = st.number_input(
            "🎯 目標顯示筆數:",
            min_value=1, max_value=200, value=20,
        )
        
        max_scan_limit = st.number_input(
            "🛑 最大搜索上限:",
            min_value=50, max_value=5000, value=1000,
            step=50,
            help="為了湊滿筆數，最多允許爬蟲檢查幾篇文章。"
        )

        st.markdown("---")
        selected_cats = st.multiselect(
            "🔍 選擇關注作品:",
            options=list(KEYWORDS_MAP.keys()),
            default=["排球少年", "藍色監獄"],
        )
        
    if st.button("🚀 啟動搜尋", type="primary", use_container_width=True):
        
        status_area = st.empty()
        progress_bar = st.progress(0)
        
        # 準備關鍵字
        target_cats = selected_cats if selected_cats else KEYWORDS_MAP.keys()
        flat_keywords = []
        for cat in target_cats:
            flat_keywords.extend(KEYWORDS_MAP[cat])
        
        # 執行爬蟲
        status_area.text("正在連線至 goods.liblo.jp ...")
        results = fetch_liblo(target_count, max_scan_limit, flat_keywords, status_area)
        progress_bar.progress(100)
        status_area.empty()
        
        if results:
            df = pd.DataFrame(results)
            
            # 分類標籤補完
            def assign_category(title):
                for cat in target_cats:
                    if any(k in title for k in KEYWORDS_MAP[cat]):
                        return cat
                return "其他"
            
            df['Category'] = df['Title'].apply(assign_category)
            
            st.success(f"搜尋完成！找到 {len(df)} 筆資料。")
            
            # 顯示表格 (已移除翻譯欄位)
            st.dataframe(
                df[["Category", "Title", "Link"]],
                column_config={
                    "Category": st.column_config.TextColumn("作品分類", width="small"),
                    "Title": st.column_config.TextColumn("商品名稱 (日文原名)", width="large"),
                    "Link": st.column_config.LinkColumn("連結", display_text="查看情報"),
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("沒有找到符合條件的情報。")

if __name__ == "__main__":
    main()