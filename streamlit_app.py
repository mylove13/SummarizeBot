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

# ✅ 로그인 후 자동 뉴스 수집 (하루 1회 - 전체 사용자 공통)
LAST_RUN_FILE = "last_news_collect.txt"
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

# ✅ 로그인 후 자동 뉴스 수집
def auto_collect_news():
    if not can_run_today():
        return  # 수집 이미 완료된 경우 조용히 종료

    try:
        subprocess.run(["python", "scripts/news_collect.py"], check=True, capture_output=True)
        update_last_run()
        st.success("✅ 오늘 뉴스 수집 및 저장 성공!")
    except subprocess.CalledProcessError as e:
        st.error(f"❌ 뉴스 기사 수집 실패: {e.stderr.decode('utf-8')}")
    except FileNotFoundError:
        st.error("❌ scripts/news_collect.py 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")

# ✅ 로그인된 사용자 확인 및 메인 페이지 표시
def show_main_page():
    if "user_id" not in st.session_state:
        st.error("❌ 로그인이 필요합니다.")
        st.stop()

    user_id = st.session_state.user_id
    username = st.session_state.get("username", "Unknown User")

    # ✅ 로그인 시 자동 뉴스 수집 실행
    if "news_collected" not in st.session_state:
        auto_collect_news()  # 이미 수집된 경우 경고 없이 무시
        st.session_state.news_collected = True

    last_run_date = get_last_run_date()

    st.sidebar.info(f"현재 로그인된 사용자: {username}")
    st.sidebar.info(f"🕒 마지막 뉴스 수집 날짜: {last_run_date}")
    show_logout_button()

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

if __name__ == "__main__":
    run_app()
