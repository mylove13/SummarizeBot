import os
import feedparser
import newspaper
import uuid
import json
from bs4 import BeautifulSoup
from datetime import datetime
import networkx as nx
from konlpy.tag import Hannanum  # ✅ JVM이 필요하지 않은 형태소 분석기
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np

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
han = Hannanum()  # ✅ JVM이 필요하지 않은 형태소 분석기

def extract_chosun_encoded(entry):
    raw_html = entry.get("content", [{}])[0].get("value", "")
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator="\n").strip()

def textrank_keywords(text, top_n=5):
    """TextRank 알고리즘으로 키워드 추출"""
    words = [word for word in han.nouns(text)]  # ✅ 형태소 분석 (명사만)
    if not words:
        return []

    # CountVectorizer로 단어 빈도수 계산
    vectorizer = CountVectorizer().fit(words)
    word_matrix = vectorizer.transform(words)
    word_scores = np.array(word_matrix.sum(axis=0)).flatten()
    words = vectorizer.get_feature_names_out()

    # 그래프 구성
    word_graph = nx.Graph()
    for i, word in enumerate(words):
        for j in range(i + 1, len(words)):
            if word_scores[i] > 0 and word_scores[j] > 0:
                word_graph.add_edge(word, words[j], weight=1)

    # PageRank로 중요도 계산
    scores = nx.pagerank(word_graph, weight='weight')
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # 상위 키워드 추출
    return [word for word, score in sorted_scores[:top_n]]

# ✅ 뉴스 기사 수집 및 분석
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

                # ✅ 조선일보: 특수 처리 (본문 HTML에서 직접 추출)
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

# ✅ 데이터 저장
with open("news_articles.json", "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)

print(f"✅ 총 {len(articles)}개 기사 저장 완료 (TextRank 키워드 포함)")
