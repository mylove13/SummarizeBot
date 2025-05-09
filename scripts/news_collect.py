import os
import feedparser
import newspaper
import uuid
import json
from bs4 import BeautifulSoup
from datetime import datetime
from collections import Counter
import re
import logging

# ✅ 로깅 설정
logging.basicConfig(filename="scripts/news_collect.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ 뉴스 수집 기록 파일 (전체 사용자 공통)
LAST_RUN_FILE = os.path.join("scripts", "last_news_collect.txt")
os.makedirs("scripts", exist_ok=True)

# ✅ RSS 피드 로드 (JSON 파일에서)
RSS_FEEDS_FILE = os.path.join(os.path.dirname(__file__), "rss_feeds.json")
if not os.path.exists(RSS_FEEDS_FILE):
    logging.error("❌ rss_feeds.json 파일이 존재하지 않습니다. 기본 파일을 생성합니다.")
    default_feeds = {
        "조선일보": {
            "정치": "https://www.chosun.com/arc/outboundfeeds/rss/category/politics/?outputType=xml",
            "경제": "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml"
        },
        "한겨레": {
            "정치": "https://www.hani.co.kr/rss/politics/",
            "경제": "https://www.hani.co.kr/rss/economy/"
        }
    }
    with open(RSS_FEEDS_FILE, "w", encoding="utf-8") as f:
        json.dump(default_feeds, f, ensure_ascii=False, indent=4)
    print("✅ 기본 rss_feeds.json 파일이 생성되었습니다.")

with open(RSS_FEEDS_FILE, "r", encoding="utf-8") as f:
    RSS_FEEDS = json.load(f)

articles = []
collected_urls = set()

# ✅ 정지어 목록 (필터링할 단어들)
STOPWORDS = set(["하다", "되다", "있다", "없다", "이다", "그리고", "하지만", "또한", "즉", "않다"])

# ✅ 수집 실행 제어 (하루 1회 실행 - 전체 사용자 대상)
def can_run_today():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, "r") as f:
            last_run = f.read().strip()
            if last_run == datetime.today().strftime("%Y-%m-%d"):
                return False
    return True

def update_last_run():
    with open(LAST_RUN_FILE, "w") as f:
        f.write(datetime.today().strftime("%Y-%m-%d"))

# ✅ 키워드 추출 함수 (정규표현식 기반 + 정지어 필터)
def extract_keywords(text, top_n=5):
    words = re.findall(r'\b[가-힣]{2,}\b', text)
    filtered_words = [word for word in words if word not in STOPWORDS]
    word_counts = Counter(filtered_words)
    ranked_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in ranked_words[:top_n]]

# ✅ 뉴스 수집 및 분석 함수
def collect_news():
    if not can_run_today():
        print("⚠️ 오늘은 이미 뉴스 수집이 완료되었습니다.")
        return []

    for source, categories in RSS_FEEDS.items():
        for category_name, rss_url in categories.items():
            feed = feedparser.parse(rss_url)
            count = 0

            for entry in feed.entries:
                if count >= 10:
                    break
                try:
                    url = entry.link
                    if url in collected_urls:
                        continue

                    title = entry.title
                    content = entry.get("summary", "") or ""

                    date = entry.published[:10] if "published" in entry else datetime.today().strftime("%Y-%m-%d")
                    keywords = extract_keywords(title + " " + content)

                    articles.append({
                        "id": str(uuid.uuid4()),
                        "title": title,
                        "content": content,
                        "source": source,
                        "category": category_name,
                        "date": date,
                        "keywords": keywords
                    })

                    collected_urls.add(url)
                    count += 1
                except Exception as e:
                    logging.error(f"[{source} - {category_name}] 수집 실패: {e}")

    update_last_run()
    return articles

# ✅ 메인 함수 (자동 실행 지원)
if __name__ == "__main__":
    articles = collect_news()
    news_file = "news_articles.json"  # scripts 폴더의 한 단계 위에 저장

    if articles:
        with open(news_file, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        print(f"✅ 총 {len(articles)}개 뉴스 수집 완료.")
    else:
        print("⚠️ 수집된 기사가 없습니다.")
