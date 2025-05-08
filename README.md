
# AI News App (Streamlit)

## 📌 개요
AI 기반 뉴스 요약 및 스크랩 웹 애플리케이션입니다.

## 🚀 주요 기능
- 뉴스 수집 (조선일보, 한겨레, 오마이뉴스, 연합뉴스)
- 키워드 기반 뉴스 필터링
- AI 기반 뉴스 요약 (GPT-4 API 사용)
- 사용자별 뉴스 스크랩 저장 및 다운로드

## 📦 설치 및 실행
```bash
# 클론 후 디렉토리 이동
git clone https://github.com/mylove13/SummarizeBot
cd SummarizeBot

# 가상 환경 생성 (선택)
python -m venv venv
source venv/bin/activate  # Windows에서는 venv\Scripts\activate

# 필요 패키지 설치
pip install -r requirements.txt

# API 키 설정
echo "YOUR_OPENAI_API_KEY" > config/hax_team4_apikey.txt

# 앱 실행
streamlit run app.py
