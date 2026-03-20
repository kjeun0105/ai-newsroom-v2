import streamlit as st
import os
import json

st.set_page_config(page_title="AI IT Newsroom", layout="centered", page_icon="🧠")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
VISITORS_FILE = os.path.join(DATA_DIR, "visitors.json")

def load_json(filepath, default_val):
    if not os.path.exists(filepath):
        return default_val
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default_val

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_visitor_count():
    if "visited" not in st.session_state:
        st.session_state["visited"] = True
        visitors = load_json(VISITORS_FILE, {"count": 0})
        visitors["count"] += 1
        save_json(VISITORS_FILE, visitors)

update_visitor_count()

st.title("🧠 AI IT Newsroom")
st.markdown("AI가 매일 정리해주는 1장짜리 IT 뉴스 브리핑")

if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

report_files = [f for f in os.listdir(REPORTS_DIR) if f.endswith('.json')]
report_files.sort(reverse=True)

if not report_files:
    st.info("아직 생성된 리포트가 없습니다. 관리자 페이지에서 뉴스를 수집하고 AI 분석을 실행하세요.")
else:
    st.sidebar.title("📅 지난 리포트")
    report_dates = [f.replace('.json', '') for f in report_files]
    selected_date = st.sidebar.selectbox("리포트 날짜 선택", report_dates)
    
    selected_file = os.path.join(REPORTS_DIR, f"{selected_date}.json")
    report_data = load_json(selected_file, {})
    
    if report_data:
        st.subheader(f"📌 오늘의 IT 뉴스 브리핑 ({report_data.get('date', selected_date)})")
        st.markdown("---")
        
        topics = report_data.get('topics', [])
        for topic in topics:
            st.markdown(f"### {topic.get('title', 'Unknown Topic')}")
            st.write(topic.get('summary', ''))
            
            links = topic.get('links', [])
            if links:
                st.markdown("**🔗 주요 뉴스 링크:**")
                for link in links:
                    st.markdown(f"- [{link}]({link})")
            
            st.markdown("---")
    else:
        st.error("리포트 데이터를 불러올 수 없습니다.")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**총 방문자 수**: {load_json(VISITORS_FILE, {'count': 0}).get('count', 0)}")
