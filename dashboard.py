import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from datetime import datetime

# === 1. 設定監控關鍵字 (Key: 中文顯示名, Value: 日文搜尋詞) ===
# 建議將所有可能的日文寫法都放進去
KEYWORDS_MAP = {
    "排球少年": ["ハイキュー", "ＨＱ"],
    "藍色監獄": ["ブルーロック", "ブルロ"],
    "咒術迴戰": ["呪術廻戦", "呪術"],
    "間諜家家酒": ["SPY×FAMILY", "スパイファミリー"],
    "吉伊卡哇": ["ちいかわ"]
}

# === 2. 定義爬蟲函數 ===
def fetch_liblo_data():
    url = "https://goods.liblo.jp/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8' # 確保日文不亂碼
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        
        # Livedoor Blog 的文章區塊通常包含在 .article-header 或類似結構中
        # 這裡針對該站特徵抓取 (需實際依該站 class 微調，此為通用寫法)
        # 觀察該站結構，標題通常在 h1 或 h3 內的 a 標籤
        entry_list = soup.find_all(['h1', 'h3'], class_='article-title') 
        
        # 若找不到特定 class，嘗試抓取所有主要連結
        if not entry_list:
             entry_list = soup.select('div.main-content h3 a')

        for entry in entry_list:
            # 確保是 a 標籤
            link_tag = entry.find('a') if entry.name != 'a' else entry
            if not link_tag: continue
            
            title = link_tag.get_text(strip=True)
            link = link_tag.get('href')
            
            articles.append({
                "title": title,
                "url": link,
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            
        return articles

    except Exception as e:
        st.error(f"爬蟲發生錯誤: {e}")
        return []

# === 3. 關鍵字過濾邏輯 ===
def filter_articles(articles, keyword_map):
    matched_results = []
    
    for article in articles:
        title = article['title']
        
        # 檢查每一個設定的關鍵字類別
        for category, jp_keywords in keyword_map.items():
            # 檢查該類別下的任何一個日文詞是否出現在標題中
            if any(k in title for k in jp_keywords):
                matched_results.append({
                    "Category": category, # 顯示中文分類 (如：排球少年)
                    "Title": title,
                    "Link": article['url'],
                    "Found Time": article['scraped_at']
                })
                break # 避免同一篇文章被重複歸類
                
    return matched_results

# === 4. Streamlit 看板介面 ===
def main():
    st.set_page_config(page_title="動漫周邊情報看板", layout="wide")
    st.title("📦 日本動漫周邊情報看板 (goods.liblo.jp)")

    # 側邊欄：顯示目前的關鍵字設定
    st.sidebar.header("目前監控的關鍵字")
    for cat, keys in KEYWORDS_MAP.items():
        st.sidebar.write(f"**{cat}**: {', '.join(keys)}")

    # 按鈕：手動觸發爬蟲
    if st.button("🔄 立即更新情報"):
        with st.spinner('正在從日本抓取最新資料...'):
            raw_data = fetch_liblo_data()
            filtered_data = filter_articles(raw_data, KEYWORDS_MAP)
            
            if filtered_data:
                df = pd.DataFrame(filtered_data)
                
                # 顯示統計數據
                st.success(f"成功抓取 {len(raw_data)} 篇最新文章，其中 {len(filtered_data)} 篇命中關鍵字！")
                
                # 顯示表格 (支援點擊連結)
                st.dataframe(
                    df,
                    column_config={
                        "Link": st.column_config.LinkColumn("文章連結")
                    },
                    use_container_width=True
                )
            else:
                st.warning("抓取成功，但最新文章中沒有符合您關鍵字的內容。")

if __name__ == "__main__":
    main()