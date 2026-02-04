import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import re

# === 1. 設定監控關鍵字 ===
KEYWORDS_MAP = {
    "排球少年": ["ハイキュー", "ＨＱ"],
    "藍色監獄": ["ブルーロック", "ブルロ"],
    "咒術迴戰": ["呪術廻戦", "呪術"],
    "間諜家家酒": ["SPY×FAMILY", "スパイファミリー"],
    "吉伊卡哇": ["ちいかわ"],
    "我的英雄學院": ["僕のヒーローアカデミア", "ヒロアカ"]
}

# === 2. 工具函數：解析日期 ===
def parse_date(date_str):
    """
    將各種日文日期格式轉為 datetime 物件
    例如: '2024年02月04日' -> datetime(2024, 2, 4)
    """
    try:
        # 移除多餘空白
        clean_str = date_str.strip()
        # 嘗試匹配 YYYY年MM月DD日
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', clean_str)
        if match:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        return None
    except:
        return None

# === 3. 爬蟲 A: Liblo (情報Blog) ===
def fetch_liblo_data(days_filter=7):
    url = "https://goods.liblo.jp/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        # 尋找文章區塊 (根據 Liblo 結構)
        # 通常是 h3 class="article-title" 或類似
        entries = soup.select('h1.article-title, h3.article-title') 
        if not entries:
             entries = soup.select('div.main-content h3 a')

        cutoff_date = datetime.now() - timedelta(days=days_filter)

        for entry in entries:
            link_tag = entry.find('a') if entry.name != 'a' else entry
            if not link_tag: continue
            
            title = link_tag.get_text(strip=True)
            link = link_tag.get('href')
            
            # 嘗試尋找日期 (通常在標題附近或 metadata 區塊)
            # 在 Livedoor Blog 中，日期通常在 .article-date 或 .date
            # 這裡我們往父層找一下日期
            date_obj = datetime.now() # 預設為今天
            
            # 嘗試從文章連結去推測日期 (如果結構允許) 或者找旁邊的 .date class
            # 這裡簡化處理：假設首頁抓到的都是最新的
            # 若要精確，需進入內文或找 .date 標籤
            # 假設結構： <div class="date">2024年02月04日</div>
            parent = entry.find_parent("div", class_="article-header")
            if parent:
                date_tag = parent.find_next_sibling("div", class_="article-footer") or parent.parent.find("p", class_="article-date")
                if date_tag:
                    parsed = parse_date(date_tag.get_text())
                    if parsed: date_obj = parsed
            
            # 時間篩選
            if date_obj >= cutoff_date:
                articles.append({
                    "Source": "Liblo (情報)",
                    "Title": title,
                    "Price/Info": "情報文",
                    "Date": date_obj.strftime("%Y-%m-%d"),
                    "Link": link
                })
            
        return articles

    except Exception as e:
        st.error(f"[Liblo] 爬取錯誤: {e}")
        return []

# === 4. 爬蟲 B: Toho Animation Store (官方商店) ===
def fetch_toho_data():
    # Toho 的新商品頁面
    url = "https://tohoentertainmentonline.com/shop/brand/TaS/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        items = []
        
        # 根據 Toho 結構 (通常是 .goods_list_item 或類似)
        # 這裡使用通用的 class 查找，您可能需要按 F12 確認最新 class
        product_list = soup.select('.goods_list .goods_item, .product-list-item')
        
        # 若找不到 class，嘗試抓取所有包含價格的連結區塊
        if not product_list:
             product_list = soup.select('div[class*="item"], li[class*="item"]')

        for prod in product_list[:30]: # 限制抓前 30 筆以免太久
            title_tag = prod.select_one('.name, .goods_name, h3, div[class*="name"]')
            price_tag = prod.select_one('.price, .goods_price, div[class*="price"]')
            link_tag = prod.find('a')
            
            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                link = link_tag.get('href')
                if not link.startswith('http'):
                    link = "https://tohoentertainmentonline.com" + link
                
                price = price_tag.get_text(strip=True) if price_tag else "Check Site"
                
                # 商店通常沒有「上架日期」，我們標記為 "New Arrival"
                items.append({
                    "Source": "Toho (商店)",
                    "Title": title,
                    "Price/Info": price,
                    "Date": "最新上架", # 商店首頁通常就是最新的
                    "Link": link
                })
                
        return items

    except Exception as e:
        st.error(f"[Toho] 爬取錯誤: {e}")
        return []

# === 5. 資料處理與過濾 ===
def process_data(liblo_data, toho_data, keyword_map):
    all_data = liblo_data + toho_data
    matched_results = []
    
    for item in all_data:
        title = item['Title']
        
        for category, jp_keywords in keyword_map.items():
            if any(k in title for k in jp_keywords):
                # 複製 item 並加上分類標籤
                new_item = item.copy()
                new_item['Category'] = category
                matched_results.append(new_item)
                break 
                
    return matched_results

# === 6. Streamlit 介面 ===
def main():
    st.set_page_config(page_title="動漫周邊雙站看板", layout="wide", page_icon="🛍️")
    st.title("🛍️ 動漫周邊情報看板 (Liblo + Toho)")

    # --- 側邊欄設定 ---
    st.sidebar.header("⚙️ 設定")
    
    # 時間篩選器 (主要針對 Blog 資料)
    time_filter = st.sidebar.radio(
        "選擇情報時間範圍 (僅適用 Blog):",
        options=[1, 3, 7, 30],
        format_func=lambda x: f"{x} 天內",
        index=2 # 預設 7 天
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("目前監控關鍵字")
    for cat, keys in KEYWORDS_MAP.items():
        st.sidebar.text(f"{cat}: {keys[0]}...")

    # --- 主畫面 ---
    if st.button("🔄 立即抓取並更新", type="primary"):
        with st.spinner('正在前往 Liblo 與 Toho 收集情報...'):
            # 平行或依序執行爬蟲
            data_liblo = fetch_liblo_data(days_filter=time_filter)
            data_toho = fetch_toho_data() # 商店資料通常視為「最新」
            
            # 合併與過濾
            final_data = process_data(data_liblo, data_toho, KEYWORDS_MAP)
            
            if final_data:
                df = pd.DataFrame(final_data)
                
                # 調整欄位順序
                cols = ["Category", "Source", "Date", "Title", "Price/Info", "Link"]
                df = df[cols]
                
                st.success(f"搜尋完成！共找到 {len(df)} 筆符合資料。")
                
                # 顯示統計數據
                col1, col2 = st.columns(2)
                col1.metric("Liblo (情報)", len([d for d in final_data if "Liblo" in d['Source']]))
                col2.metric("Toho (商店)", len([d for d in final_data if "Toho" in d['Source']]))

                # 顯示表格
                st.dataframe(
                    df,
                    column_config={
                        "Link": st.column_config.LinkColumn("連結"),
                        "Price/Info": st.column_config.TextColumn("價格/備註"),
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("抓取成功，但在指定時間或關鍵字範圍內沒有找到相關商品。")
                st.info("提示：試著放寬時間範圍，或確認 Toho 網站是否正常連線。")

if __name__ == "__main__":
    main()