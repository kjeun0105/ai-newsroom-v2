import os
import json
from google import genai
from google.genai import types
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RAW_NEWS_FILE = os.path.join(DATA_DIR, "raw_news.json")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")

import dotenv
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
# Try to get from st.secrets first, but allow standalone execution
def get_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return api_key

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

def run_ai_analysis():
    raw_news = load_json(RAW_NEWS_FILE, [])
    if not raw_news:
        print("No raw news to analyze.")
        return None
        
    today = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
You are an AI IT News editor.
Analyze, group, and summarize the following news items into a structured briefing format.

CRITICAL INSTRUCTIONS:
- ALL generated text (titles, summaries) MUST be written in Korean (한국어).
- You MUST return valid JSON ONLY.
- Do NOT wrap it in a markdown block like ```json ... ```.
- Do NOT include any explanation text.
- Exactly follow this JSON structure:
{{
  "date": "{today}",
  "topics": [
    {{
      "title": "Topic Name",
      "summary": "Cohesive summary of relevant news",
      "links": ["https://news1.url", "https://news2.url"]
    }}
  ]
}}

Raw news data:
{json.dumps(raw_news, ensure_ascii=False)}
"""

    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    
    client = genai.Client(api_key=api_key)
    
    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            )
        )
        
        report_data = json.loads(response.text)
    except Exception as e:
        print(f"AI Analysis strictly failed: {e}")
        raise RuntimeError(f"Failed to generate or parse AI response: {e}")
        
    report_filename = os.path.join(REPORTS_DIR, f"{today}.json")
    save_json(report_filename, report_data)
    save_json(RAW_NEWS_FILE, []) # Clear raw news after process
    return report_data
