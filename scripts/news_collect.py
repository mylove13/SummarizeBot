import os
import feedparser
import newspaper
import uuid
import json
from bs4 import BeautifulSoup
from datetime import datetime
from collections import Counter
import re
import streamlit as st
import logging

# ✅ 로깅 설정
logging.basicConfig(filename="news_collect.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

st.info("✅ 간단한 한국어 키워드 추출 (Konlpy 불필요)")

# ✅ 언론사별 카테고리별 RSS URL
RSS_FEEDS = {
    "조선일보": {
        "정치": "https://www.chosun.com/arc/outboundfeeds/rss/category/politics/?outputType=xml",
        "사회": "https://www.chosun.com/arc/outboundfeeds/rss/category/national/?outputType=xml",
        "경제": "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml"
    },
    "한겨레": {
        "정치": "https://www.hani.co.kr/rss/politics/",
        "사회": "https://www.hani.co.kr/rss/society/",
        "경제": "https://www.hani.co.kr/rss/economy/"
    },
    "오마이뉴스": {
        "정치": "https://rss.ohmynews.com/rss/politics.xml",
        "사회": "https://rss.ohmynews.com/rss/society.xml",
        "경제": "https://rss.ohmynews.com/rss/economy.xml"
    },
    "연합뉴스": {
        "정치": "https://www.yna.co.kr/rss/politics.xml",
        "사회": "https://www.yna.co.kr/rss/society.xml",
        "경제": "https://www.yna.co.kr/rss/economy.xml"
    }
}

articles = []
collected_urls = set()

def extract_chosun_encoded(entry):
    """조선일보 RSS 인코딩 문제 해결 함수"""
    raw_html = entry.get("content", [{}])[0].get("value", "")
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator="\n").strip()

def simple_keyword_extraction(text, top_n=5):
    """간단한 한국어 키워드 추출 (정규표현식 기반)"""
    # 한글 단어만 추출 (명사 추출 유사)
    words = re.findall(r'\b[가-힣]{2,}\b', text)
    word_counts = Counter(words)
    ranked_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in ranked_words[:top_n]]

# ✅ 뉴스 기사 수집 및 분석
def collect_news():
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

                    # ✅ 언론사별 본문 추출
                    if source == "조선일보":
                        title = entry.title
                        content = extract_chosun_encoded(entry)
                    else:
                        article = newspaper.Article(url, language='ko')
                        article.download()
                        article.parse()
                        title = article.title
                        content = article.text

                    if not content:
                        continue

                    date = entry.published[:10] if "published" in entry else datetime.today().strftime("%Y-%m-%d")
                    keywords = simple_keyword_extraction(title + " " + content)

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
                    st.error(f"❌ [{source} - {category_name}] 수집 실패: {e}")

    return articles

# ✅ 메인 함수 (Streamlit 앱)
def main():
    st.title("뉴스 기사 수집 및 저장 앱")
    st.write("RSS 피드에서 뉴스 기사를 수집하고 JSON 파일로 저장합니다.")

    if st.button("뉴스 기사 수집 시작"):
        with st.spinner("뉴스 기사 수집 중..."):
            articles = collect_news()  # 뉴스 기사 수집 함수 호출
        
        if articles:  # articles가 비어있지 않은 경우에만 저장
            # ✅ 데이터 저장
            with open("news_articles.json", "w", encoding="utf-8") as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            st.success(f"✅ 총 {len(articles)}개 기사 저장 완료 (키워드 포함)")
        else:
            st.warning("⚠️ 수집된 기사가 없습니다.")

if __name__ == "__main__":
    main()
