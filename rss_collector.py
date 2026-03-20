import json
import os
import requests
import feedparser
from xml.etree import ElementTree as ET
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
FEEDS_FILE = os.path.join(DATA_DIR, "feeds.json")
RAW_NEWS_FILE = os.path.join(DATA_DIR, "raw_news.json")

def load_json(filepath, default_val):
    if not os.path.exists(filepath):
        return default_val
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default_val

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fallback_xml_parsing(xml_content):
    entries = []
    try:
        root = ET.fromstring(xml_content)
        # Try RSS item
        for item in root.findall(".//item"):
            title = item.find("title")
            link = item.find("link")
            desc = item.find("description")
            pubDate = item.find("pubDate")
            
            entries.append({
                "title": title.text if title is not None else "No Title",
                "link": link.text if link is not None else "",
                "description": desc.text if desc is not None else "",
                "published": pubDate.text if pubDate is not None else None
            })
        if not entries:
            # Try Atom entry
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall(".//atom:entry", ns):
                title = entry.find("atom:title", ns)
                link = entry.find("atom:link", ns)
                desc = entry.find("atom:summary", ns)
                if desc is None:
                    desc = entry.find("atom:content", ns)
                published = entry.find("atom:published", ns)
                if published is None:
                    published = entry.find("atom:updated", ns)
                
                link_href = link.attrib.get("href", "") if link is not None else ""
                
                entries.append({
                    "title": title.text if title is not None else "No Title",
                    "link": link_href,
                    "description": desc.text if desc is not None else "",
                    "published": published.text if published is not None else None
                })
    except ET.ParseError as e:
        print(f"Fallback XML parsing failed: {e}")
    return entries

def collect_news():
    feeds = load_json(FEEDS_FILE, [])
    raw_news = load_json(RAW_NEWS_FILE, [])
    existing_links = {news.get("link") for news in raw_news}
    
    new_items_count = 0
    now_str = datetime.now().isoformat()
    
    for url in feeds:
        try:
            print(f"Fetching: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            content = response.text
            parsed = feedparser.parse(content)
            entries = []
            
            if not parsed.entries:
                print(f"feedparser returned empty for {url}. Attempting fallback.")
                entries = fallback_xml_parsing(content)
            else:
                for entry in parsed.entries:
                    entries.append({
                        "title": entry.get("title", "No Title"),
                        "link": entry.get("link", ""),
                        "description": entry.get("description", entry.get("summary", "")),
                        "published": entry.get("published", entry.get("updated", None))
                    })
            
            for item in entries:
                link = item.get("link")
                if not link or link in existing_links:
                    continue
                
                pub_date = item.get("published")
                if not pub_date:
                    pub_date = now_str
                    
                news_entry = {
                    "source_url": url,
                    "title": item.get("title"),
                    "link": link,
                    "description": item.get("description"),
                    "published": pub_date,
                    "collected_at": now_str
                }
                raw_news.append(news_entry)
                existing_links.add(link)
                new_items_count += 1
                
        except Exception as e:
            msg = f"Failed to collect from {url}: {e}"
            print(msg)
            raise RuntimeError(msg)
            
    save_json(RAW_NEWS_FILE, raw_news)
    return new_items_count

if __name__ == "__main__":
    count = collect_news()
    print(f"Collected {count} new items.")
