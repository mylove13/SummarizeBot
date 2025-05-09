import os
import feedparser
import newspaper
import uuid
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import networkx as nx
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from konlpy.tag import Mecab
from collections import Counter
import streamlit as st  # streamlit 추가

# ✅ Mecab 형태소 분석기 초기화 (클래스 인스턴스 생성)
mecab = Mecab()

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

def textrank_keywords(text, top_n=5):
    """TextRank 알고리즘으로 키워드 추출 (Streamlit 호환)"""
    # 1. 형태소 분석 (Mecab 사용)
    words = mecab.nouns(text)  # Mecab 객체의 nouns 메서드 사용
    if not words:
        return []

    # 2. 단어 빈도수 계산
    word_counts = Counter(words)

    # 3. 단어 중요도 계산 (빈도수 기반)
    ranked_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

    # 4. 상위 키워드 추출
    return [word for word, count in ranked_words[:top_n]]

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
                        if not content:
                            continue
                    else:
                        article = newspaper.Article(url, language='ko')
                        article.download()
                        article.parse()
                        title = article.title
                        content = article.text

                    date = entry.published[:10] if "published" in entry else datetime.today().strftime("%Y-%m-%d")

                    # ✅ 키워드 추출 (TextRank)
                    keywords = textrank_keywords(title + " " + content)

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
                    print(f"[{source} - {category_name}] 수집 실패: {e}")
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
            st.success(f"✅ 총 {len(articles)}개 기사 저장 완료 (TextRank 키워드 포함)")
        else:
            st.warning("⚠️ 수집된 기사가 없습니다.")

if __name__ == "__main__":
    main()
