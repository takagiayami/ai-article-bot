import os
<<<<<<< HEAD
import re
import hashlib
from email.utils import parsedate_to_datetime

import feedparser
import requests
=======
import feedparser
>>>>>>> 79352706b67c0c1119e4c5fae7e64d4f9f0d6e59
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

<<<<<<< HEAD
NOTION_VERSION = "2022-06-28"
NOTION_API_BASE = "https://api.notion.com/v1"

=======
>>>>>>> 79352706b67c0c1119e4c5fae7e64d4f9f0d6e59
feeds = [
    {"source": "Zenn", "url": "https://zenn.dev/feed"},
    {"source": "Qiita", "url": "https://qiita.com/tags/AI/feed"},
]

<<<<<<< HEAD
ai_keywords = [
=======
# AI関連キーワード
ai_keywords = [
    "ai",
>>>>>>> 79352706b67c0c1119e4c5fae7e64d4f9f0d6e59
    "chatgpt",
    "claude",
    "生成ai",
    "ai活用",
    "aiの使い方",
<<<<<<< HEAD
    "プロンプト",
    "claude code",
    "copilot",
    "gemini",
]

=======
    "プロンプト"
]

# 初学者向けキーワード
>>>>>>> 79352706b67c0c1119e4c5fae7e64d4f9f0d6e59
beginner_keywords = [
    "初心者",
    "入門",
    "はじめて",
    "基礎",
    "やさしく",
    "わかりやすく",
    "使い方",
<<<<<<< HEAD
    "始め方",
]

exclude_keywords = [
    "論文",
    "ベンチマーク",
=======
    "始め方"
>>>>>>> 79352706b67c0c1119e4c5fae7e64d4f9f0d6e59
]

def contains_any_keyword(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
<<<<<<< HEAD

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

    if not contains_any_keyword(title, ai_keywords):
        return False

    return True

=======
    return any(k.lower() in text_lower for k in keywords)

def is_beginner_ai_article(title: str) -> bool:
    return (
        contains_any_keyword(title, ai_keywords)
        and contains_any_keyword(title, beginner_keywords)
    )
>>>>>>> 79352706b67c0c1119e4c5fae7e64d4f9f0d6e59

def get_priority(title: str) -> str:
    title_lower = title.lower()

<<<<<<< HEAD
    if contains_any_keyword(title, beginner_keywords):
        return "High"

    if "claude" in title_lower or "chatgpt" in title_lower or "gemini" in title_lower:
        return "Medium"

    if "生成ai" in title_lower or "プロンプト" in title_lower:
=======
    if "初心者" in title or "入門" in title or "はじめて" in title:
        return "High"

    if "使い方" in title or "基礎" in title or "わかりやすく" in title:
        return "High"

    if "ai活用" in title_lower or "生成ai" in title_lower:
>>>>>>> 79352706b67c0c1119e4c5fae7e64d4f9f0d6e59
        return "Medium"

    return "Low"

<<<<<<< HEAD

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


def format_published_date(published: str) -> str | None:
    if not published:
        return None

    try:
        dt = parsedate_to_datetime(published)
        return dt.date().isoformat()  # YYYY-MM-DD
    except Exception:
        return None


def clean_summary(summary: str) -> str:
    if not summary:
        return ""

    summary = re.sub(r"<[^>]+>", "", summary)
    summary = re.sub(r"\s+", " ", summary).strip()
    return summary[:2000]


def add_article(source: str, title: str, link: str, published: str, summary: str):
    priority = get_priority(title)
    score = get_score(title)
    unique_key = make_unique_key(source, title, link)
    published_date = format_published_date(published)
    clean_text = clean_summary(summary)

    if already_exists(unique_key):
        print(f"重複スキップ: {title}")
        return

    properties = {
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
                        "content": clean_text
                    }
                }
            ]
        },
    }

    if published_date:
        properties["PublishedDate"] = {
            "date": {
                "start": published_date
            }
        }

    notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties=properties
    )

    print(f"追加: {title}")


for feed_info in feeds:
    print(f"\n取得中: {feed_info['source']} / {feed_info['url']}")
    feed = feedparser.parse(feed_info["url"])

    for entry in feed.entries[:20]:
        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()
        published = getattr(entry, "published", "")
        summary = getattr(entry, "summary", "")
=======
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
>>>>>>> 79352706b67c0c1119e4c5fae7e64d4f9f0d6e59

        if not title or not link:
            continue

<<<<<<< HEAD
        print(f"確認中: {title}")

        if not is_target_article(title):
            print("  -> 対象外")
            continue

        priority = get_priority(title)
        score = get_score(title)

        print(f"  -> 追加対象 (priority={priority}, score={score})")
        add_article(feed_info["source"], title, link, published, summary)
=======
        if not is_beginner_ai_article(title):
            continue

        add_article(feed_info["source"], title, link)
>>>>>>> 79352706b67c0c1119e4c5fae7e64d4f9f0d6e59

print("完了しました")
