import os
import re
import hashlib
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
import requests
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

NOTION_VERSION = "2022-06-28"
NOTION_API_BASE = "https://api.notion.com/v1"

feeds = [
    {"source": "Zenn", "url": "https://zenn.dev/feed"},
    {"source": "Qiita-AI", "url": "https://qiita.com/tags/AI/feed"},
    {"source": "Qiita-Vue", "url": "https://qiita.com/tags/Vue/feed"},
    {"source": "Qiita-React", "url": "https://qiita.com/tags/React/feed"},
    {"source": "Qiita-Frontend", "url": "https://qiita.com/tags/frontend/feed"},
]

ai_keywords = [
    "chatgpt",
    "claude",
    "生成ai",
    "ai活用",
    "aiの使い方",
    "プロンプト",
    "claude code",
    "copilot",
    "gemini",
]

beginner_keywords = [
    "初心者",
    "入門",
    "はじめて",
    "基礎",
    "やさしく",
    "わかりやすく",
    "使い方",
    "始め方",
]

web_keywords = [
    "SPA",
    "Vue",
    "React",
    "Nuxt",
    "Next.js",
    "フロントエンド",
    "API設計",
]

exclude_keywords = [
    "論文",
    "ベンチマーク",
]


def contains_any_keyword(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()

    for keyword in keywords:
        kw = keyword.lower()

        if re.fullmatch(r"[a-z0-9\s]+", kw):
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, text_lower):
                return True
        else:
            if kw in text_lower:
                return True

    return False


def looks_japanese(text: str) -> bool:
    return re.search(r"[ぁ-んァ-ン一-龥]", text) is not None


def is_target_article(title: str) -> bool:
    if not looks_japanese(title):
        return False

    if contains_any_keyword(title, exclude_keywords):
        return False

    if not (
        contains_any_keyword(title, ai_keywords)
        or contains_any_keyword(title, web_keywords)
    ):
        return False

    return True


def get_priority(title: str) -> str:
    title_lower = title.lower()

    if contains_any_keyword(title, beginner_keywords):
        return "High"

    if (
        "claude" in title_lower
        or "chatgpt" in title_lower
        or "gemini" in title_lower
        or "vue" in title_lower
        or "react" in title_lower
        or "nuxt" in title_lower
        or "next.js" in title_lower
        or "spa" in title_lower
    ):
        return "Medium"

    if (
        "生成ai" in title_lower
        or "プロンプト" in title
        or "フロントエンド" in title
        or "api設計" in title
        or "api" in title_lower
        or "javascript" in title_lower
        or "typescript" in title_lower
    ):
        return "Medium"

    return "Low"


def get_score(title: str) -> int:
    score = 1
    title_lower = title.lower()

    if "初心者" in title:
        score += 4
    if "入門" in title:
        score += 4
    if "はじめて" in title:
        score += 3
    if "基礎" in title:
        score += 3
    if "使い方" in title:
        score += 3
    if "始め方" in title:
        score += 3
    if "わかりやすく" in title or "やさしく" in title:
        score += 2

    if "claude" in title_lower:
        score += 1
    if "chatgpt" in title_lower:
        score += 1
    if "gemini" in title_lower:
        score += 1
    if "生成ai" in title_lower:
        score += 1
    if "プロンプト" in title:
        score += 1

    if "vue" in title_lower:
        score += 1
    if "react" in title_lower:
        score += 1
    if "nuxt" in title_lower:
        score += 1
    if "next.js" in title_lower:
        score += 1
    if "spa" in title_lower:
        score += 1
    if "フロントエンド" in title:
        score += 1
    if "api設計" in title:
        score += 1
    if "api" in title_lower:
        score += 1
    if "javascript" in title_lower:
        score += 1
    if "typescript" in title_lower:
        score += 1

    return score

def make_unique_key(source: str, title: str, link: str) -> str:
    raw = f"{source}::{title}::{link}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def notion_headers() -> dict:
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def already_exists(unique_key: str) -> bool:
    url = f"{NOTION_API_BASE}/databases/{DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "UniqueKey",
            "rich_text": {
                "equals": unique_key
            }
        },
        "page_size": 1
    }

    response = requests.post(url, headers=notion_headers(), json=payload, timeout=30)

    if response.status_code != 200:
        print("重複確認APIエラー:", response.status_code, response.text)
        raise RuntimeError("Notionの重複確認に失敗しました。")

    data = response.json()
    return len(data.get("results", [])) > 0


def get_entry_date(entry) -> str:
    if getattr(entry, "published_parsed", None):
        dt = datetime(*entry.published_parsed[:6])
        return dt.date().isoformat()

    if getattr(entry, "updated_parsed", None):
        dt = datetime(*entry.updated_parsed[:6])
        return dt.date().isoformat()

    raw = getattr(entry, "published", "") or getattr(entry, "updated", "")
    if raw:
        try:
            dt = parsedate_to_datetime(raw)
            return dt.date().isoformat()
        except Exception:
            return ""

    return ""


def add_article(source: str, title: str, link: str, published: str, summary: str):

    priority = get_priority(title)
    score = get_score(title)
    unique_key = make_unique_key(source, title, link)

    if already_exists(unique_key):
        print(f"重複スキップ: {title}")
        return

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
            },

            "UniqueKey": {
                "rich_text": [
                    {
                        "text": {
                            "content": unique_key
                        }
                    }
                ]
            },

            "Summary": {
                "rich_text": [
                    {
                        "text": {
                            "content": summary[:2000]
                        }
                    }
                ]
            },

            "PublishedDate": {
                "date": {
                    "start": published
                }
            }
        }
    )

    print(f"追加: {title}")


for feed_info in feeds:
    print(f"\n取得中: {feed_info['source']} / {feed_info['url']}")
    feed = feedparser.parse(feed_info["url"])

    for entry in feed.entries[:20]:

        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()

        published = get_entry_date(entry)
        summary = getattr(entry, "summary", "")

        if not title or not link:
            continue

        print(f"確認中: {title}")

        if not is_target_article(title):
            print("  -> 対象外")
            continue

        priority = get_priority(title)
        score = get_score(title)

        print(f"  -> 追加対象 (priority={priority}, score={score})")

        add_article(feed_info["source"], title, link, published, summary)

print("完了しました")