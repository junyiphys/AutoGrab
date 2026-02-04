# config.py

# 模擬真實瀏覽器的 Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/"
}

# 關鍵字對照表
KEYWORDS_MAP = {
    "排球少年": ["ハイキュー", "ＨＱ"],
    "藍色監獄": ["ブルーロック", "ブルロ"],
    "咒術迴戰": ["呪術廻戦", "呪術"],
    "間諜家家酒": ["SPY×FAMILY", "スパイファミリー"],
    "吉伊卡哇": ["ちいかわ"],
    "我的英雄學院": ["僕のヒーローアカデミア", "ヒロアカ"],
    "海賊王": ["ONE PIECE", "ワンピース"],
    "銀魂": ["銀魂"],
    "獵人": ["HUNTER×HUNTER"]
}