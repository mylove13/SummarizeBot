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

# ✅ RSS 피드 정의 (rss_feeds.json 파일 대신)
RSS_FEEDS = {
      "조선일보": {
    "정치": "https://www.chosun.com/arc/outboundfeeds/rss/category/politics/?outputType=xml",
    "사회": "https://www.chosun.com/arc/outboundfeeds/rss/category/national/?outputType=xml",
    "경제": "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml",
    "국제": "https://www.chosun.com/arc/outboundfeeds/rss/category/international/?outputType=xml",
    "IT": "https://www.chosun.com/arc/outboundfeeds/rss/category/digital/?outputType=xml",
    "문화/라이프": "https://www.chosun.com/arc/outboundfeeds/rss/category/culture-life/?outputType=xml",
    "오피니언": "https://www.chosun.com/arc/outboundfeeds/rss/category/opinion/?outputType=xml",
    "스포츠": "https://www.chosun.com/arc/outboundfeeds/rss/category/sports/?outputType=xml",
    "연예": "https://www.chosun.com/arc/outboundfeeds/rss/category/entertainments/?outputType=xml"
  },
  "한겨레": {
    "정치": "https://www.hani.co.kr/rss/politics/",
    "경제": "https://www.hani.co.kr/rss/economy/",
    "사회": "https://www.hani.co.kr/rss/society/",
    "국제": "https://www.hani.co.kr/rss/international/",
    "대중문화": "https://www.hani.co.kr/rss/culture/",
    "스포츠": "https://www.hani.co.kr/rss/sports/",
    "과학": "https://www.hani.co.kr/rss/science/"    
  },
  "오마이뉴스": {
    "사회": "https://rss.ohmynews.com/rss/society.xml",
    "문화": "https://rss.ohmynews.com/rss/culture.xml",
    "정치": "https://rss.ohmynews.com/rss/politics.xml",
    "경제": "https://rss.ohmynews.com/rss/economy.xml",
    "민족·국제": "https://rss.ohmynews.com/rss/international.xml",
    "교육": "https://rss.ohmynews.com/rss/education.xml",
    "미디어": "https://rss.ohmynews.com/rss/media.xml",
    "여행": "https://rss.ohmynews.com/rss/travel.xml"
  },
  "연합뉴스": {
    "정치": "https://www.yna.co.kr/rss/politics.xml",
    "사회": "https://www.yna.co.kr/rss/society.xml",
    "경제": "https://www.yna.co.kr/rss/economy.xml",
    "국제": "https://www.yna.co.kr/rss/world.xml",
    "스포츠": "https://www.yna.co.kr/rss/sports.xml"
  },
  "중앙일보": {
    "전체기사": "http://rss.joinsmsn.com/joins_news_list.xml",
    "주요기사": "http://rss.joinsmsn.com/joins_homenews_list.xml",
    "라이프": "http://rss.joinsmsn.com/news/joins_lifenews_total.xml",
    "지구촌": "http://rss.joinsmsn.com/joins_world_list.xml",
    "스포츠/연예_스포츠일반": "http://rss.joinsmsn.com/news/joins_sports_etc_list.xml",
    "스포츠/연예_방송": "http://rss.joinsmsn.com/news/joins_star_entertainment_list.xml",
    "스포츠/연예_연예일반": "http://rss.joinsmsn.com/news/joins_star_etc_list.xml"    
  },
  "동아일보": {
    "정치": "http://rss.donga.com/politics.xml",
    "사회": "http://rss.donga.com/national.xml",
    "경제": "http://rss.donga.com/economy.xml",
    "국제": "http://rss.donga.com/international.xml",    
    "의학과학": "http://rss.donga.com/science.xml",
    "문화연예": "http://rss.donga.com/culture.xml",
    "스포츠": "http://rss.donga.com/sports.xml",
    "건강": "http://rss.donga.com/health.xml",
    "레져": "http://rss.donga.com/leisure.xml",
    "도서": "http://rss.donga.com/book.xml",
    "공연": "http://rss.donga.com/show.xml",
    "여성": "http://rss.donga.com/woman.xml",
    "아동": "http://rss.donga.com/child.xml",
    "여행": "http://rss.donga.com/travel.xml",    
  },
  "경향신문": {    
    "정치": "http://www.khan.co.kr/rss/rssdata/politic.xml",
    "경제": "http://www.khan.co.kr/rss/rssdata/economy.xml",
    "사회": "http://www.khan.co.kr/rss/rssdata/society.xml",
    "문화": "http://www.khan.co.kr/rss/rssdata/culture.xml",
    "IT과학": "http://www.khan.co.kr/rss/rssdata/itnews.xml",
    "국제": "http://www.khan.co.kr/rss/rssdata/world.xml",
    "스포츠": "http://www.khan.co.kr/rss/rssdata/sports.xml"
  },
    "한국일보": {        
        "정치": "http://rss.hankooki.com/news/hk_politics.xml",
        "경제": "http://rss.hankooki.com/news/hk_economy.xml",
        "사회": "http://rss.hankooki.com/news/hk_society.xml",
        "문화": "http://rss.hankooki.com/news/hk_culture.xml",
        "라이프": "http://rss.hankooki.com/news/hk_life.xml",
        "국제": "http://rss.hankooki.com/news/hk_world.xml",
        "IT": "http://rss.hankooki.com/news/hk_it_tech.xml",
        "스포츠": "http://rss.hankooki.com/news/hk_sports.xml",
        "연예": "http://rss.hankooki.com/news/hk_entv.xml"        
    }
}

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

def extract_chosun_encoded(entry):
    raw_html = entry.get("content", [{}])[0].get("value", "")
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator="\n").strip()

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

                    if source == "조선일보":
                        title = entry.title
                        content = extract_chosun_encoded(entry)
                        if not content:
                            continue
                    else:
                        article = newspaper.Article(url, language='ko')
                        try:
                            article.download()
                            article.parse()
                            title = article.title
                            content = article.text
                        except Exception as e:
                            logging.error(f"[{source} - {category_name}] newspaper 다운로드/파싱 실패: {e} - {url}")
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
