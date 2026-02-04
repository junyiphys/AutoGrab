# app.py
import streamlit as st
import pandas as pd
import time
import re

# 匯入我們拆分出去的模組
from config import KEYWORDS_MAP
import scrapers # 匯入整個 scrapers 模組

def parse_custom_keywords(text_input):
    """解析使用者輸入的自訂關鍵字"""
    custom_map = {}
    if not text_input:
        return custom_map
    
    lines = text_input.strip().split('\n')
    for line in lines:
        # 支援全形與半形冒號
        if ':' in line or '：' in line:
            parts = re.split(r'[:：]', line, 1)
            category = parts[0].strip()
            keywords_str = parts[1].strip()
            # 支援用逗號、頓號、空格分隔
            keywords = [k.strip() for k in re.split(r'[,、\s]+', keywords_str) if k.strip()]
            if category and keywords:
                custom_map[category] = keywords
    return custom_map

def main():
    st.set_page_config(page_title="動漫周邊全網搜", layout="wide", page_icon="🛍️")
    st.title("🛍️ 動漫周邊全網搜 (Animate/Liblo)")

    # 側邊欄
    st.sidebar.header("🔍 篩選設定")

    custom_keywords_input = st.sidebar.text_area(
        "新增分類與關鍵字 (一行一組):",
        placeholder="範例格式：\n我推的孩子: 推しの子\n新番A: 關鍵字1, 關鍵字2",
        height=100
    )
    custom_map = parse_custom_keywords(custom_keywords_input)
    combined_keywords_map = {**KEYWORDS_MAP, **custom_map}

    selected_cats = st.sidebar.multiselect(
        "選擇關注作品 (可複選):",
        options=list(combined_keywords_map.keys()),
        default=["排球少年", "藍色監獄"]
    )
    
    st.sidebar.markdown("---")

    days_to_fetch = st.sidebar.number_input(
        "爬取最近幾天的情報(0為不限):",
        min_value=0, # 0 代表不限時間
        max_value=30,
        value=7,
        step=1,
        help="設定要回溯的天數。輸入 0 表示不限制時間。此設定目前僅對 Liblo (情報) 生效。"
    )

    st.sidebar.markdown("---")
    st.sidebar.info("資料來源版本 v0.12")

    if st.button("🚀 開始全網搜索", type="primary"):
        status_text = st.empty()
        status_text.info("🚀 啟動並行爬蟲模組，請稍候...")
        
        all_results = []
        progress_bar = st.progress(0)
        
        # 定義要執行的爬蟲函式 (循序執行)
        scraper_funcs = {
            "Liblo": scrapers.fetch_liblo,
            "Animate": scrapers.fetch_animate,
        }
        
        total_scrapers = len(scraper_funcs)
        for i, (name, func) in enumerate(scraper_funcs.items()):
            status_text.info(f"⏳ 正在抓取 {name} 的資料... ({i + 1}/{total_scrapers})")
            try:
                result = func(days_to_fetch)
                all_results.extend(result)
            except Exception as e:
                error_message = f"{name} 執行時發生未預期錯誤: {e}"
                print(error_message)
                all_results.append({"Source": name, "Title": f"⚠️ {error_message}", "Price": "-", "Link": "#"})
            
            progress_bar.progress((i + 1) / total_scrapers)

        status_text.success("✅ 所有網站資料搜集完畢，正在整理結果...")
        
        # 過濾邏輯
        final_data = []
        target_cats = selected_cats if selected_cats else list(combined_keywords_map.keys())
        
        for item in all_results:
            title = item['Title']
            
            # 優先處理並顯示爬蟲錯誤訊息
            if "⚠️" in title:
                item['Category'] = "爬蟲狀態"
                final_data.append(item)
                continue

            # 根據選擇的分類和關鍵字進行不分大小寫的過濾
            for cat in target_cats:
                keywords = combined_keywords_map.get(cat, [])
                # 使用 .lower() 進行不分大小寫比對，更具彈性
                if any(k.lower() in title.lower() for k in keywords):
                    item['Category'] = cat
                    final_data.append(item)
                    break # 找到分類後就跳出，避免重複加入
        
        # 顯示結果
        if final_data:
            df = pd.DataFrame(final_data)
            
            # 篩選出非錯誤狀態的資料來計算數量
            valid_df = df[df['Category'] != '爬蟲狀態']
            
            cols = st.columns(2)
            cols[0].metric("Liblo", len(valid_df[valid_df['Source'].str.contains("Liblo")]))
            cols[1].metric("Animate", len(valid_df[valid_df['Source'].str.contains("Animate")]))
            
            st.dataframe(
                df[["Category", "Source", "Title", "Price", "Link"]],
                column_config={
                    "Link": st.column_config.LinkColumn("商品連結"),
                    "Title": st.column_config.TextColumn("商品名稱", width="large"),
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("無符合條件商品。")

if __name__ == "__main__":
    main()