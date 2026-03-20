import streamlit as st
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from rss_collector import collect_news
from ai_analyzer import run_ai_analysis

st.set_page_config(page_title="Admin - AI Newsroom", layout="wide")

DATA_DIR = os.path.join(BASE_DIR, "data")
FEEDS_FILE = os.path.join(DATA_DIR, "feeds.json")
RAW_NEWS_FILE = os.path.join(DATA_DIR, "raw_news.json")
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

def check_password():
    if "ADMIN_PASSWORD" not in st.secrets:
        st.error("⚠️ Streamlit Cloud 환경 설정에서 `ADMIN_PASSWORD` 시크릿이 설정되지 않았습니다. 앱 설정에서 Secrets를 추가해주세요.")
        st.stop()

    def password_entered():
        if st.session_state["password"] == st.secrets["ADMIN_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if check_password():
    st.title("⚙️ AI Newsroom Admin Dashboard")

    visitors = load_json(VISITORS_FILE, {"count": 0})
    st.metric("Total Visitors", visitors["count"])
    st.markdown("---")
    
    st.header("RSS Feed Management")
    feeds = load_json(FEEDS_FILE, [])
    
    with st.form("add_rss_form", clear_on_submit=True):
        new_url = st.text_input("RSS URL")
        submitted = st.form_submit_button("Add RSS")
        if submitted and new_url:
            if new_url not in feeds:
                feeds.append(new_url)
                save_json(FEEDS_FILE, feeds)
                st.success(f"Added: {new_url}")
                st.rerun()
            else:
                st.warning("URL already exists.")

    st.subheader("Current RSS Feeds")
    for i, f_url in enumerate(feeds):
        cols = st.columns([8, 1])
        cols[0].write(f_url)
        if cols[1].button("Delete", key=f"del_{i}"):
            feeds.remove(f_url)
            save_json(FEEDS_FILE, feeds)
            st.rerun()

    st.markdown("---")
    
    st.header("Operations")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Collect News (RSS)"):
            with st.spinner("Collecting news..."):
                try:
                    count = collect_news()
                    st.success(f"Successfully collected {count} new items.")
                except Exception as e:
                    st.error(f"Error: {e}")
                    
    with col2:
        if st.button("🧠 Run AI Analysis"):
            with st.spinner("Analyzing with Gemini..."):
                try:
                    report = run_ai_analysis()
                    if report:
                        st.success("Analysis complete! Report saved.")
                    else:
                        st.info("No raw news to analyze.")
                except Exception as e:
                    st.error(f"Error: {e}")

    with col3:
        if st.button("🚀 Integrated Run"):
            with st.spinner("Executing Full Pipeline..."):
                try:
                    count = collect_news()
                    st.write(f"Collected {count} items.")
                    raw_news_data = load_json(RAW_NEWS_FILE, [])
                    if len(raw_news_data) > 0:
                        report = run_ai_analysis()
                        st.success("Pipeline completed successfully!")
                    else:
                        st.info("No raw news to analyze, skipping AI analysis.")
                except Exception as e:
                    st.error(f"Error: {e}")
