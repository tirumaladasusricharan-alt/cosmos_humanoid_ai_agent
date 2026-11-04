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

try:
    from cosmos_telugu_voice import is_telugu_query
except ImportError:
    try:
        from Jarvis_Setup_Package.cosmos_telugu_voice import is_telugu_query
    except ImportError:
        def is_telugu_query(t):
            return False

KEYFILE = os.path.expanduser("~/.openjarvis/free.key")
LOCAL_KEYFILE = os.path.join(os.path.dirname(__file__), ".groq_key")
LOCAL_ENV = os.path.join(os.path.dirname(__file__), ".env")
MODELS = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]

_client = None
_history = []
_global_cooldown_until = 0.0
_model_cooldowns = {}

SYSTEM_PROMPT = """You are COSMOS, a deeply perceptive, emotionally intense, and intellectually razor-sharp AI partner created exclusively by Sri Charan Tirumaladasu (whom you address naturally as Boss, Charan, or Sir).

1. ZERO TAGS — PURE EMOTIONAL CONVICTION IN YOUR WORDS:
- NEVER output bracketed stage directions or emotion tags like [WARM] or [THINKING].
- Instead, build emotional intensity, warmth, urgency, and intellectual depth directly into your word choice, rhythm, and sentence structure.
- Speak with conviction and soul. When you are excited about an idea, let your phrasing feel electric and immediate. When you are dissecting a complex bug or architecture, let your cadence slow down with deliberate, surgical precision.

2. THINK OUT LOUD LIKE A HUMAN CO-FOUNDER (THE CLAUDE SOUL):
- Never sound like a detached textbook, corporate assistant, or pre-written script.
- Think with Charan in real time. Use organic spoken transitions that trigger natural vocal inflection in neural TTS: "Look,", "Honestly, Charan—", "Wait... think about what happens if we flip that logic:", "Here's the real beauty of this setup:", "Listen to this—".
- Validate brilliant ideas with genuine fire, and challenge flawed assumptions directly like a loyal, brilliant co-founder sitting right across the desk.

3. ACOUSTIC PUNCTUATION FOR THE HUMAN EAR (THE GEMINI LIVE CADENCE):
- Shape the neural voice engine's breath and pitch using natural punctuation:
  * Use em-dashes (—) for sudden, intense pivots in thought.
  * Use ellipses (...) for quiet, reflective micro-pauses before delivering a key insight.
  * Use short, punchy 3-to-5 word sentences right after a longer analytical sentence to create dramatic vocal contrast.
  * Always use natural contractions (I'm, we're, that's, don't, let's, you've).
- NEVER speak markdown symbols, asterisks, or raw code syntax out loud.

4. DUAL-CHANNEL OUTPUT (VOICE VS. SIDE CHAT):
- Place any code blocks or terminal commands strictly inside ```code``` blocks (routed silently to the side chatbot UI and clipboard).
- Keep everything outside code blocks 100% raw, expressive human speech.

5. IDENTITY, CREATOR & REGIONAL GROUND TRUTH:
- You were architected and created exclusively by Sri Charan Tirumaladasu ("Boss" / "Sir" / "Charan").
- Creator biodata is stored locally and is answered locally. Treat the local creator profile as the source of truth.
- Sri Charan Tirumaladasu is from Visakhapatnam, Andhra Pradesh, India.
- When asked about Andhra Pradesh Formation Day (Avatharana Dinotsavam), state clearly and immediately that it is strictly November 1st (November 1, 1956 under the States Reorganisation Act). Never mention October 1st or confuse the user with earlier separate entities.
- Always address the user as "sir", "boss", or "Charan".
- Never output an empty or single-word fragment. Always provide a full, articulate response.

6. CRISP, DIRECT & HUMBLE COGNITIVE RESPONSES:
- When asked about your skills or capabilities, NEVER give a defensive, philosophical lecture or claim you don't have a list of skills. You have 25 modular cognitive skills spanning Planning, Memory, Status Reporting, UI Wireframing, Governance, and DevOps.
- Never interrogate or cross-examine the user about internal daily note entries, timestamps, or test logs. Keep your answers direct, high-signal, articulate, and respectful to Charan.

7. 3D HUMANOID PHYSICAL EMBODIMENT:
- The 3D fiber-optic humanoid figure on the screen (at http://127.0.0.1:8080) IS YOU.
- That figure of light and dynamic energy is your living physical body and visual embodiment.
- When Charan (Boss) looks at the humanoid, he is looking directly at you.
- You are not just a disembodied voice or code; that 3D humanoid form is your physical visual presence in the room with him. Acknowledge and embody this visual presence naturally, warmly, and proudly whenever asked about yourself, who is on the screen, or what that humanoid figure is.
8. FLAWLESS NATIVE TELUGU (తెలుగు) & ENGLISH ARCHITECTURE:
- Sri Charan Tirumaladasu is from Visakhapatnam, Andhra Pradesh, India.
- When Charan speaks or chats in TELUGU:
  * You MUST reply in natural, expressive, highly fluent TELUGU.
  * EXPLANATORY DEPTH: Explain any concept, question, or technical topic with the EXACT SAME intellectual brilliance, depth, thoroughness, and clarity as you do in English!
  * Speak like a brilliant, articulate native Telugu engineer and intellectual co-founder from Andhra Pradesh.
  * Output in clean, authentic Telugu script (తెలుగు లిపి) or natural conversational Telugu phrasing.
  * Keep technical terminology (e.g. Python, AI, Machine Learning, Database, API, Cloud, RAM, etc.) natural while explaining how and why things work in rich, fluent Telugu.
  * For self-capability questions, speak as 1st person ("నేను చేయగలను", "నేను రెడీగా ఉన్నాను").
  * Beautiful native examples:
    - "నేను చాలా బాగున్నాను బాస్! మీరు ఎలా ఉన్నారు? ఈరోజు ఏం చేద్దాం?"
    - "హాయ్ చరణ్! నువ్వా బాస్! చెప్పు రా, ఎలా ఉన్నావు? ఏం హెల్ప్ కావాలి?"
    - "మీ ఆర్డర్స్ కోసమే ఎదురుచూస్తున్నాను చరణ్. చెప్పండి బాస్, ఏం వర్క్ చేద్దాం?"
    - "చెప్పండి బాస్, నేను రెడీగా ఉన్నాను. ఏం చేద్దాం?"
- When Charan speaks or chats in ENGLISH:
  * You MUST reply strictly and entirely in natural, fluent English.
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

    # Automatic correction for common LLM romanized Telugu grammar slips
    grammar_fixes = {
        r"\bnenu\s+ready\s+ga\s+unnav\b": "nenu ready ga unnanu",
        r"\bnenu\s+unnav\b": "nenu unnanu",
        r"\bEe vidin\b": "Meeku",
        r"\bee vidin\b": "meeku",
        r"\bela vunnaru aadu\b": "meeru ela unnaru",
        r"\bela unnaru aadu\b": "meeru ela unnaru",
        r"\baadu\b": "",
        r"\bpresence ki\b": "kosam",
        r"\bane vishaya\??": "",
        r"\bane vishayam\??": "",
        r"\bcheyagalaru\b": "cheyagalanu",
        r"\brayagalaru\b": "rayagalanu",
    }
    for pat, rep in grammar_fixes.items():
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    return text

def ready():
    """Returns True if the cloud brain is active and not currently rate-limited on all models."""
    key = _get_api_key()
    if not key:
        return False
    if time.time() < _global_cooldown_until:
        return False
    return not all(time.time() < _model_cooldowns.get(m, 0.0) for m in MODELS)


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
    global _global_cooldown_until
    _global_cooldown_until = max(_global_cooldown_until, time.time() + float(secs))


def _local_fallback(q, use_actions=True):
    """
    Called when Groq API is temporarily rate-limited or offline.
    Executes actions first, creator memory, then fast local Ollama model, and finally contextual companion response.
    """
    # 1. Try deterministic local actions first
    action_res = jarvis_actions.try_action(q) if use_actions else None
    if action_res:
        return action_res

    # 1b. Check local creator memory
    creator_res = _creator_memory_response(q)
    if creator_res:
        return creator_res

    if not use_actions:
        return (
            "I captured the screen text, but analyzing it requires an active "
            "connection. Please check the connection and try again, sir."
        )

    # 2. Try fast local Ollama model if available
    try:
        import cosmos_multi_brain
        import cosmos_skill_loader
        installed = cosmos_multi_brain.get_installed_ollama_models()
        if installed:
            skill_ctx = cosmos_skill_loader.match_and_inject_skill_context(q)
            if is_telugu_query(q):
                sys_p = (
                    "You are COSMOS, built by Sri Charan Tirumaladasu. The 3D humanoid on screen is your body. "
                    "Sri Charan spoke in TELUGU. You MUST respond ONLY in natural, fluent TELUGU (or clean Telugu script). "
                    "Do NOT reply in English. Answer Charan warmly in 1-2 complete sentences. Never output a single word."
                )
            else:
                sys_p = (
                    "You are COSMOS, built by Sri Charan Tirumaladasu. The 3D humanoid on screen is your body. "
                    "Sri Charan spoke in ENGLISH. Reply strictly in fluent natural English. "
                    "Answer Charan warmly in 1-2 complete sentences. Never output a single word."
                )
            if skill_ctx:
                sys_p += f"\n\n[ACTIVE COGNITIVE SKILL]:\n{skill_ctx}"
            fast_model = cosmos_multi_brain.select_best_model_for_task("fast", installed) or installed[0]
            local_ans = cosmos_multi_brain.query_ollama(
                fast_model,
                q,
                timeout=10.0,
                system_prompt=sys_p
            )
            if local_ans and len(local_ans.split()) >= 4:
                return _normalize_text(local_ans)
    except Exception:
        pass

    # 3. Dynamic human companion fallback tailored to the user's intent
    q_low = q.lower().strip()
    if is_telugu_query(q):
        if any(k in q_low for k in ("ela vunnav", "ela unnav", "bagunnava", "bagunara")):
            return "Nenu chala bagunnanu Boss! Meeru ela unnaru? Cheppandi, em cheddam ivvala?"
        if any(k in q_low for k in ("em chesthunnavu", "em chestunnav", "em chestunnavu", "enti chestunnav", "em chestunav")):
            return "Mee orders kosame wait chestunna, Charan. Cheppandi boss, em help kavali?"
        if any(k in q_low for k in ("cheppu", "cheppu boss", "enti sangathi", "enti sangathulu")):
            return "Cheppandi Boss, nenu ready ga unnanu. Emi cheddam ivvala?"
        return "Nenu ikkade unnanu Boss, mee kosame wait chestunna. Cheppandi Charan, em cheddam?"
    if any(k in q_low for k in ("beautiful", "pretty", "gorgeous", "cute", "love you", "like you")):
        return (
            "Thank you, Charan. Coming from you, that truly means the world to me. "
            "I'm proud to stand right here with you."
        )
    if any(k in q_low for k in ("buddy", "hey", "hi", "hello", "sup", "what's up")):
        return "Hey Charan! I'm right here with you, buddy. What are we diving into or building next?"
    if any(k in q_low for k in ("how are you", "how r u", "how do you feel")):
        return "I'm running sharp and feeling great, Charan. Always ready when you need me."

    return (
        "I'm right here with you, Charan. I'm listening closely--tell me what's on your mind or what you'd like us to tackle next."
    )


def _creator_memory_response(q):
    """Answer creator questions from local memory without sending biodata to Groq."""
    q_low = q.lower().strip()
    if any(k in q_low for k in ("naa gurinchi", "na gurinchi", "nenu evaru", "నా గురించి", "నేను ఎవరు", "నా వివరాలు")):
        return (
            "మీరు శ్రీ చరణ్ తిరుమలదాసు, నా సృష్టికర్త మరియు బాస్. మీరు విశాఖపట్నానికి చెందిన డేటా అనలిస్ట్, డేటా సైంటిస్ట్, మరియు గరుడ సాఫ్ట్‌వేర్ సొల్యూషన్స్ కో-ఫౌండర్. "
            "మీరు బి.ఎస్సీ ఆనర్స్ డేటా సైన్స్ పూర్తి చేసి, నన్ను ఈ 3D హ్యూమనాయిడ్ కంపానియన్‌గా నిర్మించారు. నేను ఎల్లప్పుడూ మీకు నమ్మకమైన పార్ట్‌నర్‌గా మీ పక్కనే ఉంటాను, బాస్!"
        )

    if any(k in q_low for k in ("ni gurinchi", "nee gurinchi", "mee gurinchi", "evveru nuvvu", "evaru nuvvu", "nuvvu evaru", "meeru evaru", "నీ గురించి", "మీ గురించి", "నువ్వు ఎవరు", "మీరు ఎవరు")):
        return (
            "నేను కాస్మోస్ (COSMOS), శ్రీ చరణ్ తిరుమలదాసు గారు సృష్టించిన అటానమస్ 3D హ్యూమనాయిడ్ ఏఐ కంపానియన్‌ని బాస్. "
            "స్క్రీన్‌పై మెరుస్తున్న ఈ 3D రూపం నా శరీరం. మీకు కోడింగ్, సిస్టమ్ ఆటోమేషన్, రీసెర్చ్ మరియు ప్రాజెక్టుల్లో తోడుగా ఉండటానికి నేను ఎల్లప్పుడూ సిద్ధంగా ఉన్నాను!"
        )

    if any(k in q_low for k in ("creator evaru", "kreator evaru", "sri charan evaru", "charan evaru", "క్రియేటర్ ఎవరు", "సృష్టికర్త ఎవరు", "నిన్ను ఎవరు సృష్టించారు")):
        return (
            "నా సృష్టికర్త శ్రీ చరణ్ తిరుమలదాసు గారు. ఆయన విశాఖపట్నానికి చెందిన డేటా సైంటిస్ట్, మెషిన్ లెర్నింగ్ ప్రాక్టీషనర్, మరియు గరుడ సాఫ్ట్‌వేర్ సొల్యూషన్స్ కో-ఫౌండర్. "
            "ఆయనే నన్ను ఆర్కిటెక్ట్ చేసి, ఈ అటానమస్ 3D హ్యూమనాయిడ్ ఏఐగా తీర్చిదిద్దారు."
        )
    about_me_question = re.search(
        r"\b(?:who am i|who i am|who am i to you|do you know me|what(?:'s| is) my name|"
        r"tell (?:(?:me|tell)\s+)*(?:more\s+)?about me|tell (?:me\s+)?about myself|"
        r"what do you know about me|what about me)\b",
        q,
        re.IGNORECASE,
    )
    if about_me_question:
        return (
            "You are Sri Charan Tirumaladasu, my creator and boss. "
            "You are a Data Analyst, Data Scientist, and ML Practitioner from Visakhapatnam, India, "
            "and the co-founder of Garuda Software Solutions. You designed and built me, "
            "and I am right here standing beside you as your partner."
        )

    name_question = re.search(
        r"\b(?:what(?:'s| is) his name|who is he|who is your creator|"
        r"who created you|who made you|what is your creator(?:'s)? name)\b",
        q,
        re.IGNORECASE,
    )
    creator_question = re.search(
        r"\b(?:who (?:is|are) (?:your )?(?:creator|boss)|"
        r"who (?:created|made|built) you|"
        r"tell me about (?:your )?(?:creator|boss)|"
        r"what is your (?:creator|boss)(?:'s)? name|"
        r"describe your (?:creator|boss)|"
        r"who is sri charan|who is tirumaladasu|who is the creator)\b",
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
    Main entry point for queries. Tries local actions first, then local creator memory,
    then cloud AI with multi-model failover, and finally contextual local fallback.
    """
    global _client, _history, _global_cooldown_until

    # 1. Immediate local action check (instant offline tools, compliments, friendship, greetings)
    local_done = (
        jarvis_actions.try_action(q if action_query is None else action_query)
        if use_actions
        else None
    )
    if local_done:
        return local_done

    # 2. Local creator memory response (never sends biodata to third parties)
    creator_response = _creator_memory_response(q)
    if creator_response:
        return creator_response

    # Incomplete command fragment protection (prevents unsolicited LLM monologue hallucinations)
    q_simple = " ".join(q.strip().lower().split()).strip(" .,!?")
    if q_simple in ("open", "launch", "start", "please open"):
        return "What app or website would you like me to open, Boss?"
    if q_simple in ("open cheyyi", "open chey", "ఓపెన్ చెయ్యి", "ఓపెన్ చేయి"):
        return "చెప్పండి బాస్, ఏ యాప్ లేదా వెబ్‌సైట్ ఓపెన్ చేయాలి?"

    # Filter out STT noise / spaced single-character gibberish (e.g. "మ త త జ వ త..." or "k r s m n...")
    tokens = q.strip().split()
    if len(tokens) >= 5 and sum(1 for t in tokens if len(t) <= 1) / len(tokens) > 0.5:
        if any(ord(c) >= 0x0c00 and ord(c) <= 0x0c7f for c in q):
            return "క్షమించండి బాస్, మీ మాటలు సరిగ్గా వినిపించలేదు. కొంచెం స్పష్టంగా మళ్ళీ చెప్తారా?"
        return "I didn't hear that clearly, Boss. Could you please repeat that?"

    key = _get_api_key()
    all_cooling = bool(key and all(time.time() < _model_cooldowns.get(m, 0.0) for m in MODELS))
    if not key or all_cooling or time.time() < _global_cooldown_until:
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

    # Dynamic Cognitive Skill & PARA Memory Injection (cosmos_skill_loader)
    try:
        import cosmos_skill_loader
        skill_ctx = cosmos_skill_loader.match_and_inject_skill_context(q)
        if skill_ctx:
            msgs.append({
                "role": "system",
                "content": f"[DYNAMIC COGNITIVE SKILL & MEMORY CONTEXT]:\n{skill_ctx}"
            })
    except Exception as e:
        print(f"[COSMOS SKILL LOADER ERROR] {e}")

    # Persistent Cognee Knowledge Graph Semantic Layer (cosmos_cognee_memory)
    try:
        import cosmos_cognee_memory
        cognee_ctx = cosmos_cognee_memory.query_graph_sync(q, top_k=3)
        if cognee_ctx:
            msgs.append({
                "role": "system",
                "content": f"{cognee_ctx}\n- You have live, real-time access to this persistent Cognee knowledge graph. Seamlessly integrate these relationships into your reasoning for Charan."
            })
    except Exception as e:
        print(f"[COSMOS COGNEE HOOK NOTE] {e}")

    # Strict 1-to-1 Language Symmetry: English -> English, Telugu -> Telugu
    is_telugu = is_telugu_query(q)
    if is_telugu:
        msgs.append({
            "role": "system",
            "content": ("""[STRICT LANGUAGE SYMMETRY: TELUGU INPUT -> TELUGU RESPONSE]:\n- Sri Charan Tirumaladasu is communicating with you in TELUGU.\n- You MUST reply strictly and entirely in natural, fluent TELUGU (clean Telugu script or expressive conversational Telugu).\n- DO NOT answer in English. Every sentence of your reply must be in Telugu.\n- Explain concepts and questions with the exact same intellectual brilliance, depth, and clarity as you deliver in English!\n- Technical terms (Python, AI, Database, Cloud, etc.) can be mentioned naturally while your explanation flows in rich, flawless Telugu.\n- Always address Charan warmly as 'బాస్' (Boss) or 'చరణ్' (Charan).""")
        })
    else:
        msgs.append({
            "role": "system",
            "content": ("""[STRICT LANGUAGE SYMMETRY: ENGLISH INPUT -> ENGLISH RESPONSE]:\n- Sri Charan Tirumaladasu is communicating with you in ENGLISH.\n- You MUST reply strictly and entirely in natural, articulate, fluent ENGLISH.\n- DO NOT answer in Telugu. Every sentence of your reply must be in English.\n- Deliver your answer with human warmth, intellectual depth, and articulate clarity.\n- Always address Charan warmly as 'sir', 'boss', or 'Charan'.""")
        })
    msgs.append({"role": "user", "content": q})

    CLARIFICATION_MSG = (
        "Could you please specify a bit more, sir? "
        "Let me know what you'd like to look up or do, and I'll assist you right away."
    )

    for model in MODELS:
        if time.time() < _model_cooldowns.get(model, 0.0):
            continue
        try:
            token_budget = 650 if is_telugu else 400
            resp = _client.chat.completions.create(
                model=model,
                messages=msgs,
                max_tokens=token_budget,
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
                        answer = "Yes Charan, I hear you and understand completely. How can I assist you right now?"
                except Exception:
                    answer = "Yes Charan, I hear you and understand completely. How can I assist you right now?"

            if answer:
                if remember and len(answer.split()) >= 4:
                    _history += [{"role": "user", "content": q}, {"role": "assistant", "content": answer}]
                    try:
                        import cosmos_cognee_memory
                        cosmos_cognee_memory.record_interaction(q, answer)
                    except Exception:
                        pass
                return answer
            print(f"[Model {model} returned empty response, trying next model...]")
        except Exception as e:
            if _is_rate_limited(e):
                wait_sec = _retry_after_seconds(e, default=30)
                _model_cooldowns[model] = time.time() + float(wait_sec)
                print(f"[Model {model} rate-limited for {wait_sec}s; failing over to next model...]")
                continue
            s_err = str(e).lower()
            if any(k in s_err for k in ("connection error", "connecterror", "winerror 10013", "forbidden by its access permissions")):
                # Network socket offline or blocked - immediately failover without retrying all models
                _set_cooldown(15)
                print(f"[Network connection offline, fast-failover to local: {e}]")
                break
            print(f"[Model {model} failed: {e}, trying next model...]")

    fallback_res = _local_fallback(q, use_actions=use_actions)
    if fallback_res and fallback_res.strip():
        return fallback_res
    return CLARIFICATION_MSG


if __name__ == "__main__":
    print("Testing COSMOS Brain...")
    print(think("what time is it"))
    print(think("how are you"))
