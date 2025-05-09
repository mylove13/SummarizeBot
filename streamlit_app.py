import streamlit as st
import os
import json
import uuid
import csv
import hashlib
from openai import OpenAI
import pandas as pd
from datetime import date, timedelta
import subprocess  # 외부 프로세스 실행을 위한 라이브러리

# ✅ API 키 로딩 (환경 변수 사용)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OpenAI API 키가 설정되지 않았습니다. 환경 변수에서 API 키를 설정하세요.")
    st.stop()

client = OpenAI(api_key=api_key)

# ✅ 사용자 회원가입 및 로그인 시스템
USER_DATA_FILE = "user_data/users.json"
os.makedirs("user_data", exist_ok=True)

# ✅ 사용자 데이터 로드 함수
def load_user_data():
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        st.error(f"⚠️ {USER_DATA_FILE} 파일이 손상되었습니다. 사용자 데이터를 초기화합니다.")
        return {}
    except FileNotFoundError:
        return {}

# ✅ 사용자 데이터 저장 함수
def save_user_data(data):
    try:
        with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"❌ 사용자 데이터를 저장하는 동안 오류가 발생했습니다: {e}")

# ✅ 사용자 데이터 로드
user_data = load_user_data()

# ✅ 비밀번호 암호화 함수
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ✅ 회원가입 또는 로그인 UI (메인 페이지로 이동)
def show_auth_form():
    mode = st.selectbox("선택", ["로그인", "회원가입"])  # 사이드바 제거

    if mode == "회원가입":
        st.subheader("회원가입")
        username = st.text_input("사용자명")
        password = st.text_input("비밀번호", type="password")
        if st.button("회원가입"):
            if username in user_data:
                st.error("❌ 이미 존재하는 사용자명입니다.")
            else:
                user_data[username] = {"password": hash_password(password), "user_id": str(uuid.uuid4())}
                save_user_data(user_data)
                st.success("✅ 회원가입 성공! 로그인하세요.")
    elif mode == "로그인":  # 'else'를 'elif mode == "로그인"'으로 명시적으로 변경
        st.subheader("로그인")
        username = st.text_input("사용자명")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if username in user_data and user_data[username]["password"] == hash_password(password):
                st.session_state.user_id = user_data[username]["user_id"]
                st.session_state.username = username
                st.success(f"✅ 로그인 성공! 환영합니다, {username}!")
                st.session_state.logged_in = True  # 로그인 상태를 True로 설정
                st.rerun()  # 로그인 성공 후 페이지를 다시 로드하여 메인 페이지를 표시
            else:
                st.error("❌ 사용자명 또는 비밀번호가 잘못되었습니다.")

# ✅ 로그아웃 기능 (사이드바로 이동)
def show_logout_button():
    if "user_id" in st.session_state:
        if st.sidebar.button("🚪 로그아웃"):  # 버튼을 사이드바로 이동
            del st.session_state.user_id
            del st.session_state.username
            st.session_state.logged_in = False
            st.rerun()

# ✅ 뉴스 업데이트 기능
def update_news():
    today = date.today().isoformat()
    last_update = st.session_state.get("last_news_update")

    if last_update == today:
        st.sidebar.info("✅ 오늘 뉴스 업데이트 완료")
        return False
    else:
        st.sidebar.info("🔄 뉴스 업데이트 중...")
        try:
            # scripts/news_collect.py 실행
            subprocess.run(["python", "scripts/news_collect.py"], check=True)
            st.session_state.last_news_update = today
            st.sidebar.success("✅ 뉴스 업데이트 완료")
            # 뉴스 데이터를 다시 로드하여 화면에 반영
            if "articles" in st.session_state:
                del st.session_state["articles"]
            return True
        except subprocess.CalledProcessError as e:
            st.sidebar.error(f"❌ 뉴스 업데이트 실패: {e}")
            return False
        except FileNotFoundError:
            st.sidebar.error("❌ scripts/news_collect.py 파일을 찾을 수 없습니다.")
            return False

# ✅ 로그인된 사용자 확인 및 메인 페이지 표시
def show_main_page():
    if "user_id" not in st.session_state:
        st.error("❌ 로그인이 필요합니다.")
        st.stop()

    user_id = st.session_state.user_id
    username = st.session_state.get("username", "Unknown User")

    st.sidebar.info(f"현재 로그인된 사용자: {username}")  # 사용자 이름 표시
    show_logout_button()  # 로그아웃 버튼 사이드바에 표시

    # ✅ 뉴스 업데이트 버튼 (사이드바)
    if st.sidebar.button("📰 뉴스 업데이트"):
        update_news()

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
                st.error(f"⚠️ {scrap_file} 파일이 손상되었습니다. 스크랩 목록을 초기화합니다.")
                st.session_state.scrap_list = []
        else:
            st.session_state.scrap_list = []

    if "summary_map" not in st.session_state:
        if os.path.exists(summary_file):
            try:
                with open(summary_file, "r", encoding="utf-8") as f:
                    st.session_state.summary_map = json.load(f)
            except json.JSONDecodeError:
                st.error(f"⚠️ {summary_file} 파일이 손상되었습니다. 요약 목록을 초기화합니다.")
                st.session_state.summary_map = {}
        else:
            st.session_state.summary_map = {}

    scrap_list = st.session_state.scrap_list
    summary_map = st.session_state.summary_map

    # ✅ 뉴스 로딩 (세션 상태를 사용하여 한 번만 로드)
    @st.cache_data
    def load_articles(filename="news_articles.json"):
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                st.error(f"⚠️ {filename} 파일이 손상되었습니다. 파일을 확인하거나 다시 생성해주세요.")
                return []
            except Exception as e:
                st.error(f"⚠️ {filename} 파일을 읽는 동안 예외가 발생했습니다: {e}")
                return []
        else:
            st.error(f"❌ 뉴스 파일 {filename}이 존재하지 않습니다.")
            return []

    if "articles" not in st.session_state:
        st.session_state.articles = load_articles()
    articles = st.session_state.articles

    # ✅ 필터 설정
    st.sidebar.title("🔍 필터 설정")
    if articles:
        all_categories = list(set([a["category"] for a in articles]))
        all_sources = list(set([a["source"] for a in articles]))
        all_keywords = list(set([kw for a in articles for kw in a.get("keywords", [])]))

        selected_categories = st.sidebar.multiselect("카테고리 선택", all_categories)
        selected_sources = st.sidebar.multiselect("언론사 선택", all_sources)
        selected_keyword = st.sidebar.selectbox("키워드 선택", ["(선택 안 함)"] + all_keywords)
        search_text = st.sidebar.text_input("검색어 입력")

        # ✅ 필터 적용
        filtered_articles = [
            a for a in articles if
            (a["category"] in selected_categories if selected_categories else True)
            and (a["source"] in selected_sources if selected_sources else True)
            and (selected_keyword == "(선택 안 함)" or selected_keyword in a.get("keywords", []))
            and (search_text.lower() in (a["title"] + a["content"]).lower())
        ]
    else:
        filtered_articles = []

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
                            ]
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
                if st.button("❌ 스크랩 취소", key=f"unscrap_{article_id}"):  # 스크랩 취소 버튼
                    scrap_list.remove(article_id)
                    with open(scrap_file, "w", encoding="utf-8") as f:
                        json.dump(scrap_list, f, ensure_ascii=False)
                    st.success("스크랩이 취소되었습니다.")
                    st.rerun()  # 페이지 새로고침
            else:
                if st.button("🤍 스크랩", key=f"{article_id}_scrap"):
                    scrap_list.append(article_id)
                    with open(scrap_file, "w", encoding="utf-8") as f:
                        json.dump(scrap_list, f, ensure_ascii=False)
                    st.success("뉴스를 스크랩했습니다.")

    # ✅ 사이드바에 스크랩된 뉴스 표시
    st.sidebar.title("📌 스크랩된 뉴스")
    if scrap_list:
        for article in articles:
            if article["id"] in scrap_list:
                st.sidebar.write(f"✅ {article['title']} ({article['date']} | {article['source']})")
    else:
        st.sidebar.write("스크랩된 뉴스가 없습니다.")

    # ✅ 사용자별 스크랩 다운로드 (CSV)
    st.sidebar.title("⬇️ 다운로드")
    if scrap_list:
        scrap_info = [
            {"title": a["title"], "date": a["date"], "source": a["source"]}
            for a in articles
            if a["id"] in scrap_list
        ]
        scrap_df = pd.DataFrame(scrap_info)  # pandas DataFrame으로 변환
        scrap_csv = scrap_df.to_csv(index=False)
        st.sidebar.download_button(
            label="📥 스크랩된 뉴스 다운로드 (CSV)",
            data=scrap_csv,
            file_name=f"scrap_info_{user_id}.csv",  # 파일명에 user_id 사용
            mime="text/csv",
        )

    # ✅ 사용자별 요약 다운로드 (CSV)
    if summary_map:
        summary_info = [
            {
                "title": a["title"],
                "date": a["date"],
                "summary": summary_map.get(a["id"], "요약 없음"),
            }
            for a in articles
            if a["id"] in summary_map
        ]
        summary_df = pd.DataFrame(summary_info)  # pandas DataFrame으로 변환
        summary_csv = summary_df.to_csv(index=False)
        st.sidebar.download_button(
            label="📥 요약 다운로드 (CSV)",
            data=summary_csv,
            file_name=f"summary_info_{user_id}.csv",  # 파일명에 user_id 사용
            mime="text/csv",
        )


# ✅ 앱 실행
def run_app():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False  # 초기 로그인 상태를 False로 설정

    if not st.session_state.logged_in:
        show_auth_form()  # 로그인/회원 가입 폼 표시
    else:
        show_main_page()  # 메인 페이지 표시


if __name__ == "__main__":
    run_app()
