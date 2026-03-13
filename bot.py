import os
import feedparser
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

if not NOTION_TOKEN:
    raise ValueError("NOTION_TOKEN が .env に設定されていません。")

if not DATABASE_ID:
    raise ValueError("DATABASE_ID が .env に設定されていません。")

notion = Client(auth=NOTION_TOKEN)

feeds = [
    {"source": "Zenn", "url": "https://zenn.dev/feed"},
    {"source": "Qiita", "url": "https://qiita.com/tags/AI/feed"},
]

# AI関連キーワード
ai_keywords = [
    "ai",
    "chatgpt",
    "claude",
    "生成ai",
    "ai活用",
    "aiの使い方",
    "プロンプト"
]

# 初学者向けキーワード
beginner_keywords = [
    "初心者",
    "入門",
    "はじめて",
    "基礎",
    "やさしく",
    "わかりやすく",
    "使い方",
    "始め方"
]

def contains_any_keyword(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in keywords)

def is_beginner_ai_article(title: str) -> bool:
    return (
        contains_any_keyword(title, ai_keywords)
        and contains_any_keyword(title, beginner_keywords)
    )

def get_priority(title: str) -> str:
    title_lower = title.lower()

    if "初心者" in title or "入門" in title or "はじめて" in title:
        return "High"

    if "使い方" in title or "基礎" in title or "わかりやすく" in title:
        return "High"

    if "ai活用" in title_lower or "生成ai" in title_lower:
        return "Medium"

    return "Low"

def get_score(title: str) -> int:
    score = 1

    if "初心者" in title:
        score += 3
    if "入門" in title:
        score += 3
    if "はじめて" in title:
        score += 3
    if "基礎" in title:
        score += 2
    if "使い方" in title:
        score += 2
    if "わかりやすく" in title:
        score += 2

    return score

def add_article(source: str, title: str, link: str):
    priority = get_priority(title)
    score = get_score(title)

    notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties={
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": title[:2000]
                        }
                    }
                ]
            },
            "Source": {
                "select": {
                    "name": source
                }
            },
            "Link": {
                "url": link
            },
            "Status": {
                "select": {
                    "name": "未読"
                }
            },
            "Priority": {
                "select": {
                    "name": priority
                }
            },
            "Score": {
                "number": score
            }
        }
    )
    print(f"追加: {title}")

for feed_info in feeds:
    feed = feedparser.parse(feed_info["url"])

    for entry in feed.entries[:20]:
        title = getattr(entry, "title", "")
        link = getattr(entry, "link", "")

        if not title or not link:
            continue

        if not is_beginner_ai_article(title):
            continue

        add_article(feed_info["source"], title, link)

print("完了しました")