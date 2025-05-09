import streamlit as st
import os
import json
import uuid
import csv
import hashlib
from openai import OpenAI
import pandas as pd
import subprocess
from datetime import datetime

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

# ✅ 뉴스 수집 기록 파일 (전체 사용자 공통)
LAST_RUN_FILE = os.path.join("scripts", "last_news_collect.txt")
LOG_FILE = os.path.join("scripts", "news_collect.log")
os.makedirs("scripts", exist_ok=True)

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

def get_last_run_date():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, "r") as f:
            return f.read().strip()
    return "기록 없음"

# ✅ 전체 사용자 대상 자동 뉴스 수집 (하루 1회)
def auto_collect_news():
    if not can_run_today():
        st.info(f"✅ 오늘 이미 뉴스가 수집되었습니다. ({get_last_run_date()})")
        return

    try:
        result = subprocess.run(
            ["python", "scripts/news_collect.py"],
            check=True,
            capture_output=True,
            text=True
        )
        update_last_run()
        st.success("✅ 오늘 뉴스 수집 및 저장 성공!")
    except subprocess.CalledProcessError as e:
        st.error(f"❌ 뉴스 기사 수집 실패: {e.stderr}")
    except FileNotFoundError:
        st.error("❌ scripts/news_collect.py 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")

# ✅ 로그 파일 확인
def show_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = f.read()
        st.text_area("📄 뉴스 수집 로그", logs, height=400)
        st.sidebar.download_button(
            label="📥 로그 파일 다운로드",
            data=logs,
            file_name="news_collect.log",
            mime="text/plain"
        )
    else:
        st.warning("❌ 로그 파일이 존재하지 않습니다.")

# ✅ 로그인된 사용자 확인 및 메인 페이지 표시
def show_main_page():
    if "user_id" not in st.session_state:
        st.error("❌ 로그인이 필요합니다.")
        st.stop()

    user_id = st.session_state.user_id
    username = st.session_state.get("username", "Unknown User")

    # ✅ 로그인 시 자동 뉴스 수집 실행 (전체 사용자 대상)
    if "news_collected" not in st.session_state:
        auto_collect_news()  # 전체 사용자 대상 하루 1회 수집
        st.session_state.news_collected = True

    last_run_date = get_last_run_date()
    st.sidebar.info(f"현재 로그인된 사용자: {username}")
    st.sidebar.info(f"🕒 마지막 뉴스 수집 날짜: {last_run_date}")
    show_logout_button()

    st.title("📢 AI 뉴스 요약 & 스크랩")
    st.sidebar.title("📝 로그 확인")
    if st.sidebar.button("로그 파일 보기"):
        show_logs()

# ✅ 로그아웃 기능 (사이드바로 이동)
def show_logout_button():
    if "user_id" in st.session_state:
        if st.sidebar.button("🚪 로그아웃"):
            del st.session_state.user_id
            del st.session_state.username
            st.session_state.logged_in = False
            st.rerun()

# ✅ 앱 실행
def run_app():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        show_auth_form()  # 로그인/회원 가입 폼 표시
    else:
        show_main_page()  # 메인 페이지 표시

# ✅ 회원가입 또는 로그인 UI (메인 페이지로 이동)
def show_auth_form():
    mode = st.selectbox("선택", ["로그인", "회원가입"])

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
    elif mode == "로그인":
        st.subheader("로그인")
        username = st.text_input("사용자명")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if username in user_data and user_data[username]["password"] == hash_password(password):
                st.session_state.user_id = user_data[username]["user_id"]
                st.session_state.username = username
                st.success(f"✅ 로그인 성공! 환영합니다, {username}!")
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ 사용자명 또는 비밀번호가 잘못되었습니다.")

if __name__ == "__main__":
    run_app()
