import streamlit as st
import os
import json
import uuid
from openai import OpenAI
import pandas as pd  # 데이터프레임 사용을 위해 import

# ✅ API 키 로딩 (환경 변수 사용)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error(
        "❌ OpenAI API 키가 설정되지 않았습니다. 환경 변수에서 API 키를 설정하세요."
    )
    st.stop()

client = OpenAI(api_key=api_key)

# ✅ 사용자 식별 (HTTP 쿠키 기반)
user_id = st.session_state.get("user_id", None)


if not user_id:
    user_id = str(uuid.uuid4())
    st.session_state.user_id = user_id
    st.write(
        f'<script>document.cookie = "user_id={user_id}; path=/";</script>',
        unsafe_allow_html=True,
    )

st.sidebar.info(f"현재 사용자 ID (쿠키): {user_id}")


# ✅ 사용자 파일 저장 디렉토리
USER_FILES_DIR = os.path.join("user_data", user_id)
os.makedirs(USER_FILES_DIR, exist_ok=True)

scrap_file = os.path.join(USER_FILES_DIR, "scrap.json")
summary_file = os.path.join(USER_FILES_DIR, "summary.json")


# ✅ 스크랩 및 요약 로드 (파일에서 항상 로드)
if "scrap_list" not in st.session_state:
    if os.path.exists(scrap_file):
        try:
            with open(scrap_file, "r", encoding="utf-8") as f:
                st.session_state.scrap_list = json.load(f)
        except json.JSONDecodeError:
            st.error(
                f"⚠️ {scrap_file} 파일이 손상되었습니다. 스크랩 목록을 초기화합니다."
            )
            st.session_state.scrap_list = []
    else:
        st.session_state.scrap_list = []

if "summary_map" not in st.session_state:
    if os.path.exists(summary_file):
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                st.session_state.summary_map = json.load(f)
        except json.JSONDecodeError:
            st.error(
                f"⚠️ {summary_file} 파일이 손상되었습니다. 요약 목록을 초기화합니다."
            )
            st.session_state.summary_map = {}
    else:
        st.session_state.summary_map = {}

scrap_list = st.session_state.scrap_list
summary_map = st.session_state.summary_map


# ✅ 뉴스 로딩
@st.cache_data
def load_articles(filename="news_articles.json"):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error(f"⚠️ {filename} 파일이 손상되었습니다.  파일을 확인하거나 다시 생성해주세요.")
            return []  # 빈 리스트를 반환하여 앱이 중단되지 않도록 함
    else:
        st.error(f"❌ 뉴스 파일 {filename}이 존재하지 않습니다.")
        return []


articles = load_articles()


# ✅ 필터 설정
st.sidebar.title("🔍 필터 설정")
if articles: # articles가 비어있지 않은 경우에만 필터 생성.
    all_categories = list(set([a["category"] for a in articles]))
    all_sources = list(set([a["source"] for a in articles]))
    all_keywords = list(set([kw for a in articles for kw in a.get("keywords", [])]))

    selected_categories = st.sidebar.multiselect("카테고리 선택", all_categories)
    selected_sources = st.sidebar.multiselect("언론사 선택", all_sources)
    selected_keyword = st.sidebar.selectbox("키워드 선택", ["(선택 안 함)"] + all_keywords)
    search_text = st.sidebar.text_input("검색어 입력")

    # ✅ 필터 적용
    filtered_articles = [
        a
        for a in articles
        if (a["category"] in selected_categories if selected_categories else True)
        and (a["source"] in selected_sources if selected_sources else True)
        and (
            selected_keyword == "(선택 안 함)"
            or selected_keyword in a.get("keywords", [])
        )
        and (search_text.lower() in (a["title"] + a["content"]).lower())
    ]
else:
    filtered_articles = [] # articles가 비어있으면, 필터링된 결과도 빈 리스트.

# ✅ UI
st.title("📢 AI 뉴스 요약 & 스크랩 (사용자별 저장)")
if not filtered_articles:
    st.warning("⚠️ 필터 조건에 맞는 뉴스가 없습니다.")
else:
    for article in filtered_articles:
        st.markdown("---")
        st.subheader(f"📰 {article['title']}")
        st.caption(f"{article['date']} | {article['source']} | 📂 {article['category']}")

        if article.get("keywords"):
            st.markdown("**🔑 키워드:** " + ", ".join(article["keywords"]))

        article_id = article["id"]

        # ✅ 사용자 요약
        if article_id in summary_map:
            st.success(summary_map[article_id])
        else:
            if st.button(f"요약 보기", key=f"{article_id}_summary"):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": f"다음 뉴스 기사를 3문장으로 요약해줘:\n\n{article['content']}",
                            }
                        ],
                    )
                    summary = response.choices[0].message.content.strip()
                    summary_map[article_id] = summary
                    with open(summary_file, "w", encoding="utf-8") as f:
                        json.dump(summary_map, f, ensure_ascii=False, indent=2)
                    st.success(summary)
                except Exception as e:
                    st.error(f"❌ 요약 생성 중 오류 발생: {e}")

        # ✅ 사용자 스크랩
        if article_id in scrap_list:
            st.info("✔ 이미 스크랩한 뉴스입니다.")
        else:
            if st.button("🤍 스크랩", key=f"{article_id}_scrap"):
                scrap_list.append(article_id)
                with open(scrap_file, "w", encoding="utf-8") as f:
                    json.dump(scrap_list, f, ensure_ascii=False)
                st.success("뉴스를 스크랩했습니다.")

# ✅ 사이드바에 스크랩된 뉴스 표시
st.sidebar.title("📌 스크랩된 뉴스")
if scrap_list: # 스크랩된 뉴스가 있을 경우에만 표시
    for article in articles:
        if article["id"] in scrap_list:
            st.sidebar.write(
                f"✅ {article['title']} ({article['date']} | {article['source']})"
            )
else:
    st.sidebar.write("스크랩된 뉴스가 없습니다.")

# ✅ 사용자별 스크랩 다운로드 (CSV)
st.sidebar.title("⬇️ 다운로드") # 다운로드 섹션 제목 추가
if scrap_list:
    scrap_info = [
        {"title": a["title"], "date": a["date"], "source": a["source"]}
        for a in articles
        if a["id"] in scrap_list
    ]
    scrap_df = pd.DataFrame(scrap_info)  # pandas DataFrame으로 변환
    scrap_csv = scrap_df.to_csv(index=False)  # index 제외하고 CSV 생성
    st.sidebar.download_button(
        label="📥 스크랩된 뉴스 다운로드 (CSV)",
        data=scrap_csv,
        file_name=f"scrap_info_{user_id}.csv",
        mime="text/csv",
    )

# ✅ 사용자별 요약 다운로드 (CSV)
if summary_map:
    summary_info = [
        {"title": a["title"], "date": a["date"], "summary": summary_map.get(a["id"], "요약 없음")}
        for a in articles
        if a["id"] in summary_map # summary_map에 있는 것만 처리.
    ]

    summary_df = pd.DataFrame(summary_info)  # pandas DataFrame으로 변환
    summary_csv = summary_df.to_csv(index=False)
    st.sidebar.download_button(
        label="📥 요약 다운로드 (CSV)",
        data=summary_csv,
        file_name=f"summary_info_{user_id}.csv",
        mime="text/csv",
    )
