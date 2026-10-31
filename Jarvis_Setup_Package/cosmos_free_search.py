"""
cosmos_free_search.py - Zero-Cost Live Browser & Web Access Engine for COSMOS
Architected & Exclusively Deployed for Sri Charan Tirumaladasu ("Boss" or "Sir")

Provides ₹0 cost, zero API-key live web searching and web scraping using BeautifulSoup
and DuckDuckGo, synthesizing real-time facts and speaking answers via cosmos_speak().
"""

import os
import re
import sys

# Safeguard stdout/stderr for background pythonw.exe execution
if sys.stdout is None:
    try:
        sys.stdout = open(os.devnull, "w")
    except Exception:
        pass
if sys.stderr is None:
    try:
        sys.stderr = open(os.devnull, "w")
    except Exception:
        pass
import threading
import urllib.parse
import urllib.request
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def cosmos_speak(text: str):
    """Voice-First Output Discipline: Speaks clean text strictly via COSMOS female Edge-TTS."""
    try:
        from cosmos_human_voice import cosmos_speak as _cs
        _cs(text)
    except Exception as e:
        print(f"[COSMOS VOICE ERROR] {e}")

def cosmos_live_web_search(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """
    Zero-Cost Live Web Search using standard urllib and BeautifulSoup with DuckDuckGo.
    Extracts title, snippet, and source URL without any API keys or fees.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    results = []

    # 1. Primary: Standard urllib with DuckDuckGo HTML endpoint via GET
    try:
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(clean_query)
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            for item in soup.select(".result"):
                title_elem = item.select_one(".result__title")
                snippet_elem = item.select_one(".result__snippet")
                url_elem = item.select_one(".result__url")
                if title_elem and snippet_elem:
                    title = title_elem.get_text(strip=True)
                    snippet = snippet_elem.get_text(strip=True)
                    link = url_elem.get_text(strip=True) if url_elem else ""
                    if not title.lower().startswith("sponsored"):
                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "url": link
                        })
                        if len(results) >= max_results:
                            break
    except Exception as e:
        print(f"[COSMOS URLLIB SEARCH ERROR] {e}")

    # 2. Lite Fallback using standard urllib
    if not results:
        try:
            lite_url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote_plus(clean_query)}"
            req = urllib.request.Request(lite_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=7) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                soup = BeautifulSoup(html, "html.parser")
                rows = soup.select("table tbody tr")
                for i in range(0, len(rows) - 1, 2):
                    link_elem = rows[i].select_one(".result-link")
                    snippet_elem = rows[i + 1].select_one(".result-snippet")
                    if link_elem and snippet_elem:
                        results.append({
                            "title": link_elem.get_text(strip=True),
                            "snippet": snippet_elem.get_text(strip=True),
                            "url": link_elem.get("href", "")
                        })
                        if len(results) >= max_results:
                            break
        except Exception as e:
            print(f"[COSMOS LITE URLLIB ERROR] {e}")

    # 3. Requests fallback
    if not results:
        try:
            resp = requests.post("https://html.duckduckgo.com/html/", data={"q": clean_query}, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for item in soup.select(".result"):
                    title_elem = item.select_one(".result__title")
                    snippet_elem = item.select_one(".result__snippet")
                    url_elem = item.select_one(".result__url")
                    if title_elem and snippet_elem:
                        title = title_elem.get_text(strip=True)
                        snippet = snippet_elem.get_text(strip=True)
                        link = url_elem.get_text(strip=True) if url_elem else ""
                        if not title.lower().startswith("sponsored"):
                            results.append({"title": title, "snippet": snippet, "url": link})
                            if len(results) >= max_results:
                                break
        except Exception:
            pass

    return results

def cosmos_fetch_web_page(url: str, max_chars: int = 2500) -> str:
    """
    Fetches raw webpage text using standard urllib and strips clutter
    (scripts, styles, navs) via BeautifulSoup to return clean human-readable content.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            return text[:max_chars]
    except Exception as e:
        print(f"[COSMOS FETCH ERROR] {e}")
    return ""

def needs_live_search(query: str) -> bool:
    """
    Detects if the query explicitly demands real-time web facts, news, or internet lookup.
    Keeps conversation fast and prevents unnecessary web scraping latency.
    """
    q = query.lower().strip()
    triggers = (
        "search the web", "search online", "look up on web", "browse for",
        "latest news", "today's news", "weather today", "current weather",
        "stock price of", "nifty today", "sensex today", "gold price today"
    )
    return any(t in q for t in triggers)

def normalize_text_for_output(text: str) -> str:
    """Normalizes unicode whitespace, hyphens, and quotes for console and TTS stability."""
    if not text:
        return ""
    replacements = {
        '\u202f': ' ', '\u00a0': ' ',
        '\u2011': '-', '\u2013': '-', '\u2014': '--',
        '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"',
        '\u2192': '->', '\u2190': '<-',
        '\u2022': '-', '\u2026': '...',
        '\u200b': '', '\ufeff': '',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    try:
        text.encode('cp1252')
    except UnicodeEncodeError:
        text = text.encode('ascii', 'ignore').decode('ascii')
    return text

def synthesize_live_answer(query: str) -> Optional[str]:
    """
    Performs live search, collects snippets, and prompts the LLM
    to generate a crisp spoken response for Sri Charan.
    """
    search_results = cosmos_live_web_search(query, max_results=3)
    if not search_results:
        return None

    context_snippets = "\n".join(
        f"- {r['title']}: {r['snippet']}" for r in search_results
    )

    # Attempt synthesis using OpenAI/Groq client if available
    try:
        import jarvis_brain
        from openai import OpenAI
        key = jarvis_brain._get_api_key()
        if key:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            sys_prompt = (
                "You are COSMOS, elite autonomous intelligence created exclusively by Sri Charan Tirumaladasu ('Boss'). "
                "Synthesize the following live web search results into a concise, articulate 1-2 sentence spoken answer. "
                "Do NOT use markdown, asterisks, bullet points, or code formatting. Address the user as sir."
            )
            user_msg = f"User Query: {query}\n\nLive Web Information:\n{context_snippets}"
            resp = client.chat.completions.create(
                model=jarvis_brain.MODELS[0],
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_msg}
                ],
                max_tokens=300,
                temperature=0.4
            )
            msg_obj = resp.choices[0].message
            raw_content = getattr(msg_obj, "content", "") or ""
            reply = raw_content.strip() if raw_content else ""
            reply = re.sub(r"[\*\_#`]", "", reply)
            if reply:
                return normalize_text_for_output(reply)
    except Exception as e:
        print(f"[COSMOS SYNTHESIS FALLBACK] {e}")

    # Fallback if LLM is unavailable: Return cleanest top snippet
    best_snippet = search_results[0]["snippet"]
    best_snippet = re.sub(r"[\*\_#`]", "", best_snippet)
    return normalize_text_for_output(f"According to live web data, {best_snippet}")

def get_live_news_briefing() -> str:
    """
    Fetches real-time live news headlines directly from news feeds using standard urllib.
    Zero-cost, 100% real-time, speaks out loud via cosmos_speak().
    """
    import warnings
    from bs4 import XMLParsedAsHTMLWarning
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

    headlines = []
    url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
            for item in soup.find_all("item")[:4]:
                t = item.find("title")
                if t and t.text.strip():
                    clean_t = re.sub(r"\s+-\s+[^-]+$", "", t.text.strip())
                    headlines.append(clean_t)
    except Exception as e:
        print(f"[COSMOS LIVE NEWS ERROR] {e}")

    if not headlines:
        res = cosmos_live_web_search("breaking news today headlines India", max_results=3)
        for r in res:
            headlines.append(r["title"])

    if headlines:
        briefing = "Sir, here are the latest breaking headlines: " + "; ".join(headlines[:3]) + "."
    else:
        briefing = "I could not retrieve the latest news feed right now, Boss."

    return normalize_text_for_output(briefing)

def cosmos_search_and_speak(query: str) -> str:
    """
    Directive 3.1: Free Live Web Search & Fresh Data Fetching.
    Queries DuckDuckGo/Lite scrapers and BeautifulSoup with zero paid API keys,
    extracts clean text, synthesizes recent updates, and returns the response.
    """
    ans = synthesize_live_answer(query)
    if not ans:
        ans = "I could not retrieve live web data for that query right now, Boss."
    return ans

def answer_with_live_search(query: str) -> Optional[str]:
    """
    Complete workflow alias: Search -> Synthesize -> Speak -> Return text.
    """
    return cosmos_search_and_speak(query)

if __name__ == "__main__":
    test_q = sys.argv[1] if len(sys.argv) > 1 else "current world population"
    print(f"Testing live search for: {test_q}")
    answer = synthesize_live_answer(test_q)
    print("Answer:", answer)
