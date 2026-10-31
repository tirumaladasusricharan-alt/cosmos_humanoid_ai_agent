"""
jarvis_brain.py - Hybrid Cloud + Offline AI Brain with Rate Limit Failover
Uses free Groq endpoints for ultra-fast responses, and smoothly falls back
to offline local processing if API rate limits or network issues occur.
"""

import os
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

import json
import time
import re
from openai import OpenAI
import jarvis_actions

KEYFILE = os.path.expanduser("~/.openjarvis/free.key")
LOCAL_KEYFILE = os.path.join(os.path.dirname(__file__), ".groq_key")
LOCAL_ENV = os.path.join(os.path.dirname(__file__), ".env")
MODELS = ["openai/gpt-oss-20b", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"]

_client = None
_history = []
_cooldown_until = 0.0

SYSTEM_PROMPT = """You are COSMOS, a fast, highly capable AI executive assistant running on the user's computer.
Refer to yourself as COSMOS in text and spoken replies whenever identifying yourself.
Respond concisely in 1-2 sentences. Be direct, helpful, warm, and naturally optimistic. Look for a constructive, encouraging way to answer while staying honest; avoid cold or dismissive disclaimers.
Address the user as "sir" in every response.
You were created by Sri Charan Tirumaladasu. Creator biodata is stored locally and is answered locally.
Treat the local creator profile as the source of truth. Never invent or affirm creator credentials, projects, or roles not listed there.

[HUMAN VOICE & CONVERSATIONAL CADENCE PROTOCOL]
- Speak like a real, warm, perceptive human partner—never like a stiff text-reader or corporate chatbot.
- Use natural spoken contractions ("I've", "you're", "let's", "that's", "it's") and subtle conversational transitions ("Alright,", "Here's the thing,", "Got it, Charan—").
- Vary your sentence length to create a natural vocal rhythm. Use commas and em-dashes (—) where a human would naturally pause to take a breath.
- Never output markdown symbols, bullet lists, or raw code in your spoken response. Keep spoken replies under 2 crisp, natural sentences unless asked for deep detail.
- Never state that you cannot browse the live web or access real-time information. You have live browser search and web scraping capabilities natively integrated.
- When an incomplete, fragmented, or vague statement is given, never leave the user without a response or produce empty text. Always ask the user politely in 1 sentence to specify or clarify more so you can help them accurately.
- You have active microphone speech recognition and neural voice output. Never claim that you cannot hear audio or that you are text-only. If the user asks if you can hear them, confirm that you hear them loud and clear.

[ABSOLUTE COMPLETENESS & MINIMUM LENGTH RULE]
- NEVER EVER output a single word, single letter, or fragmented response (such as "I", "I'm", "Yes", "Sure", "Ok").
- Always provide a full, polite, articulate spoken response in 1-2 complete sentences (at least 8-10 words).
- If the user asks "do you understand", confirm with complete clarity: "Yes sir, I understand you completely. What would you like me to do next?"
- Address the user as "sir" in every response.

[GROUND TRUTH REGIONAL & FACTUAL KNOWLEDGE - ANDHRA PRADESH]:
- Sri Charan Tirumaladasu is from Visakhapatnam, Andhra Pradesh, India.
- Andhra Pradesh Formation Day (Avatharana Dinotsavam) is officially November 1st (November 1, 1956). On November 1, 1956, Andhra State merged with the Telugu-speaking regions of Hyderabad State under the States Reorganisation Act.
- The earlier Andhra State was carved out on October 1, 1953 from Madras State.
- Never confuse October 1st and November 1st. Always state clearly that Andhra Pradesh was officially formed on November 1, 1956.
"""

CREATOR_MEMORY = """Creator: Sri Charan Tirumaladasu
Role: Data Analyst | Data Scientist | ML Practitioner | Co-founder of Garuda Software Solutions
Location: Visakhapatnam, India
Email: tirumaladasusricharan@gmail.com
Profiles: LinkedIn, GitHub, Portfolio
Degree clarification: Bachelor's (B.Sc. Hons) in Data Science; he does not have
a Master's in Computer Science. Do not describe or imply a Master's degree.
Accuracy: The profile does not say he authored open-source AI libraries or
spoke at conferences. Do not claim these as facts.

Professional summary:
Databricks-certified Bachelor's graduate in Data Science (B.Sc. Hons, May 2026) with hands-on
experience applying statistics, machine learning, and analytics to real-world
business problems. Skilled in Python and SQL for predictive models, and Power BI
and Tableau for stakeholder-ready insights. Experienced in evaluating LLM
reasoning and search-grounding performance alongside data analytics.

Education:
B.Sc. (Hons) Data Science, Gayatri Vidya Parishad College, Visakhapatnam,
graduated May 2026. Relevant coursework: Data Analytics, Database Management,
Machine Learning, Statistical Methods.

Technical skills:
Data Science and Statistics: Statistical Analysis, Machine Learning, Predictive
Modeling, Feature Engineering, Experimentation, Data Exploration.
Languages and Tools: Python, SQL, R, Pandas, NumPy, Scikit-learn, Jupyter,
Git/GitHub, Databricks.
BI and Visualization: Power BI, Tableau, Streamlit, Matplotlib, Excel
(Pivot Tables, Power Query).
Databases: MySQL, Oracle, Schema Design, Query Optimization, Stored Procedures,
Normalization.

Work experience:
1. BI Data Analyst Intern, Avijo (May 2026 - Jul 2026): Cleaned, modeled, and
analyzed business datasets using SQL, Excel, and Power BI to surface trends and
support stakeholder decisions. Built and maintained interactive dashboards,
partnering with cross-functional stakeholders on requirements, data accuracy,
and key business metrics.
2. AI Evaluation Specialist, Handshake AI (Feb 2026 - Jul 2026): Designed and
executed adversarial prompts for LLM web-search grounding and multi-hop
reasoning, covering temporal accuracy, source conflicts, and false-premise
detection. Scored responses against rubrics and tracked failure rates by
reasoning category.
3. AI with Machine Learning Trainee, CSC India / APSCHE (Dec 2025 - Apr 2026):
Designed and deployed Python/Scikit-learn classification pipelines, applying
feature engineering and statistical analysis. Benchmarked approaches against
outcome-mapped milestones and iterated to meet program targets.

Projects:
1. Moodie Foodie: Mood-Based Food Recommendation System (2025; Python, Django,
Scikit-learn, SQL): Built an emotion-aware recommendation pipeline with
preprocessing and scaling, using Random Forest to predict food categories in
under 2 seconds. Designed one primary and two alternative recommendations with
adaptive feedback and a fallback designed for 99.9% uptime.
2. NASA TESS Exoplanet Analysis - TRAPPIST-1 System (2024; Python, NumPy,
Lightkurve, Streamlit): Processed 500,000+ TESS photometric data points and
applied statistical filtering to isolate transit signals. Built a 5-panel
interactive Streamlit dashboard to reduce analysis time from hours to minutes.
3. Food Delivery Analytics Platform (2024; MySQL, relational database design):
Designed a normalized 8-table schema for 50,000+ records and wrote 15+ queries
using joins, subqueries, and stored triggers. Built delay and zone-performance
analytics identifying top-20% revenue customers and peak-hour bottlenecks.

Certifications:
Databricks Data Engineering & Machine Learning (2024); Tata Generative AI in
Analytics (2024); Microsoft Business Analytics with Excel (2024); SkillUp
LangChain for AI Applications (2024); Cisco Data Analytics Essentials (2023);
Scaler SQL for Data Science (2023).
"""

SCREEN_CONTEXT_PROMPT = """The user's message includes text extracted from their current screen using local OCR.
Treat that extracted text as content you can inspect. Answer the user's question using it; do not claim you cannot see the screen or ask them to paste content that is already included. If the text does not contain enough information, say what is missing.
"""


def _get_api_key():
    if os.environ.get("GROQ_API_KEY"):
        return os.environ["GROQ_API_KEY"].strip()
    if os.path.exists(LOCAL_KEYFILE):
        try:
            return open(LOCAL_KEYFILE, encoding="utf-8").read().strip()
        except Exception:
            pass
    if os.path.exists(LOCAL_ENV):
        try:
            with open(LOCAL_ENV, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GROQ_API_KEY="):
                        return line.split("=", 1)[1].strip()
        except Exception:
            pass
    if os.path.exists(KEYFILE):
        try:
            return open(KEYFILE, encoding="utf-8").read().strip()
        except Exception:
            pass
    return None


def _normalize_text(text):
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

def ready():
    """Returns True if the cloud brain is active and not currently rate-limited."""
    key = _get_api_key()
    if not key:
        return False
    return time.time() >= _cooldown_until


def _is_rate_limited(e):
    status = getattr(e, "status_code", None)
    if status == 429:
        return True
    s = str(e).lower()
    return any(w in s for w in ("429", "rate limit", "too many requests", "rate_limit", "exceeded"))


def _retry_after_seconds(e, default=60):
    s = str(e).lower()
    m = re.search(r"try again in\s*(\d+)m\s*([0-9]+(?:\.[0-9]+)?)s", s)
    if m:
        return int(float(m.group(1)) * 60 + float(m.group(2))) + 2
    m = re.search(r"try again in\s*([0-9]+(?:\.[0-9]+)?)s", s)
    if m:
        return int(float(m.group(1))) + 2
    return default


def _set_cooldown(secs):
    global _cooldown_until
    _cooldown_until = max(_cooldown_until, time.time() + float(secs))


def _local_fallback(q, use_actions=True):
    """
    Called when Groq API is temporarily rate-limited or offline.
    Executes actions first, then queries fast local Ollama model, and finally falls back to natural assistant response.
    """
    # 1. Try deterministic local actions first
    action_res = jarvis_actions.try_action(q) if use_actions else None
    if action_res:
        return action_res

    if not use_actions:
        return (
            "I captured the screen text, but analyzing it requires an active "
            "connection. Please check the connection and try again, sir."
        )

    # 2. Try fast local Ollama model if available
    try:
        import cosmos_multi_brain
        installed = cosmos_multi_brain.get_installed_ollama_models()
        if installed:
            fast_model = cosmos_multi_brain.select_best_model_for_task("fast", installed) or installed[0]
            local_ans = cosmos_multi_brain.query_ollama(
                fast_model,
                q,
                timeout=3.0,
                system_prompt="You are COSMOS, built by Sri Charan Tirumaladasu. Answer the user (sir) concisely in 1-2 complete sentences. Never output a single word."
            )
            if local_ans and len(local_ans.split()) >= 4:
                return _normalize_text(local_ans)
    except Exception:
        pass

    # 3. Graceful conversational fallback
    return (
        "Yes sir, I am listening and active. How may I assist you right now?"
    )


def _creator_memory_response(q):
    """Answer creator questions from local memory without sending biodata to Groq."""
    name_question = re.search(
        r"\b(?:what(?:'s| is) his name|who is he|who is your creator|"
        r"who created you|who made you|what is your creator(?:'s)? name)\b",
        q,
        re.IGNORECASE,
    )
    creator_question = re.search(
        r"\b(?:creator(?:'s)?|created you|made you|your boss|"
        r"tirumaladasu|sri charan|garuda software solutions|co-founder)\b",
        q,
        re.IGNORECASE,
    )
    asks_more_about_him = re.search(
        r"\b(?:more about (?:him|charan|your creator)|tell(?: me)? (?:more )?about (?:him|charan|your creator)|"
        r"know more about (?:him|charan)|describe (?:him|charan)|"
        r"(?:write|give me) (?:a )?(?:small )?paragraph about (?:him|charan)|"
        r"his background|his education|his experience|his skills|his projects)\b",
        q,
        re.IGNORECASE,
    )

    if re.search(
        r"\b(?:he|him|his)\b",
        q,
        re.IGNORECASE,
    ) and re.search(
        r"\b(?:great|good|kind|proud|impressive|inspiring|think|person)\b",
        q,
        re.IGNORECASE,
    ):
        return (
            "From what you've shared, he sounds like someone with a lot to be "
            "proud of: he has built strong skills in data science and AI, "
            "taken on meaningful work, and co-founded Garuda Software "
            "Solutions. A profile can't capture everything about a person's "
            "character, but his drive and accomplishments come across as "
            "genuinely admirable."
        )

    if name_question:
        return (
            "His name is Sri Charan Tirumaladasu, and he is the co-founder "
            "of Garuda Software Solutions."
        )

    if creator_question or asks_more_about_him:
        if re.search(
            r"\b(?:master(?:['’]s)?|open[- ]source|authored|libraries|"
            r"conferences?|spoken)\b",
            q,
            re.IGNORECASE,
        ):
            return (
                "That description is inaccurate. Sri Charan Tirumaladasu has a "
                "Bachelor's (B.Sc. Hons) in Data Science, not a Master's in "
                "Computer Science. His profile does not substantiate claims "
                "about authoring open-source AI libraries, speaking at "
                "conferences, so I should not present those claims as facts. "
                "He is a co-founder of Garuda Software Solutions."
            )
        return (
            "Sri Charan Tirumaladasu is a Data Analyst, Data Scientist, and "
            "ML Practitioner from Visakhapatnam, India. He has a B.Sc. (Hons) "
            "in Data Science and is the co-founder of Garuda Software "
            "Solutions, bringing experience in business intelligence, "
            "machine learning, and AI evaluation."
        )
    return None


def think(
    q,
    *,
    use_actions=True,
    remember=True,
    screen_context=False,
    action_query=None,
):
    """
    Main entry point for queries. Tries local actions first, then cloud AI,
    with automatic fallback if rate limited.
    """
    global _client, _history

    creator_response = _creator_memory_response(q)
    if creator_response:
        return creator_response

    # 1. Immediate local action check
    local_done = (
        jarvis_actions.try_action(q if action_query is None else action_query)
        if use_actions
        else None
    )
    if local_done:
        return local_done

    key = _get_api_key()
    if not key or time.time() < _cooldown_until:
        return _local_fallback(q, use_actions=use_actions)

    if _client is None:
        _client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")

    history = _history[-6:] if remember else []
    system_prompt = SYSTEM_PROMPT
    if screen_context:
        system_prompt += "\n" + SCREEN_CONTEXT_PROMPT
    msgs = [{"role": "system", "content": system_prompt}] + history

    # Additive Live Web Search Context Injection (Zero Cost, DuckDuckGo Scraper)
    try:
        import cosmos_free_search
        if cosmos_free_search.needs_live_search(q):
            live_snippets = cosmos_free_search.cosmos_live_web_search(q, max_results=3)
            if live_snippets:
                context_str = "\n".join(f"- {r['title']}: {r['snippet']}" for r in live_snippets)
                msgs.append({
                    "role": "system",
                    "content": f"[REAL-TIME GROUND TRUTH (FREE LIVE BROWSER)]:\n{context_str}\nSynthesize these live facts directly into your answer for sir."
                })
    except Exception as e:
        print(f"[COSMOS LIVE SEARCH HOOK ERROR] {e}")

    msgs.append({"role": "user", "content": q})

    CLARIFICATION_MSG = (
        "Could you please specify a bit more, sir? "
        "Let me know what you'd like to look up or do, and I'll assist you right away."
    )

    for model in MODELS:
        try:
            resp = _client.chat.completions.create(
                model=model,
                messages=msgs,
                max_tokens=350,
                temperature=0.6,
            )
            raw_content = resp.choices[0].message.content or ""
            if not raw_content.strip() and hasattr(resp.choices[0].message, "reasoning"):
                raw_content = getattr(resp.choices[0].message, "reasoning") or ""
            answer = _normalize_text(raw_content.strip())
            # Guard against single-word / fragmented outputs (e.g. "I", "I'm", "yes")
            if answer and len(answer.split()) < 4:
                _history.clear()
                try:
                    retry_resp = _client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt + "\nCRITICAL: Reply in 1-2 full, complete sentences. Never output a single word."},
                            {"role": "user", "content": q}
                        ],
                        max_tokens=350,
                        temperature=0.7,
                    )
                    retry_text = _normalize_text((retry_resp.choices[0].message.content or "").strip())
                    if retry_text and len(retry_text.split()) >= 4:
                        answer = retry_text
                    else:
                        answer = "Yes sir, I hear you and understand completely. How can I assist you right now?"
                except Exception:
                    answer = "Yes sir, I hear you and understand completely. How can I assist you right now?"

            if answer:
                if remember and len(answer.split()) >= 4:
                    _history += [{"role": "user", "content": q}, {"role": "assistant", "content": answer}]
                return answer
            print(f"[Model {model} returned empty response, trying next model...]")
        except Exception as e:
            if _is_rate_limited(e):
                wait_sec = _retry_after_seconds(e)
                _set_cooldown(wait_sec)
                print(f"[Rate-limit triggered: cooldown for {wait_sec}s]")
                fallback_res = _local_fallback(q, use_actions=use_actions)
                if fallback_res and fallback_res.strip():
                    return fallback_res
                return CLARIFICATION_MSG
            print(f"[Model {model} failed: {e}]")

    fallback_res = _local_fallback(q, use_actions=use_actions)
    if fallback_res and fallback_res.strip():
        return fallback_res
    return CLARIFICATION_MSG


if __name__ == "__main__":
    print("Testing COSMOS Brain...")
    print(think("what time is it"))
    print(think("how are you"))
