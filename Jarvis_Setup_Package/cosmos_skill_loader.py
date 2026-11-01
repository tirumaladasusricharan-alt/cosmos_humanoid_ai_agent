"""
cosmos_skill_loader.py - Dynamic Cognitive Skill Loader & PARA Memory Router
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Architected & Deployed exclusively for Sri Charan Tirumaladasu ("Boss" / "Sir")

Capabilities:
1. Dynamic Skill Registry: Indexes all 25 modular SKILL.md files in ./cosmos_skills/.
2. Semantic Skill Matcher: Matches user intent (planning, wireframe, PARA memory, wiki, standup).
3. PARA Knowledge Graph (cosmos_para_memory): Projects, Areas, Resources, Archives & Daily Notes.
4. Context Injector: Feeds matched skill prompts seamlessly into Ollama multi-brain council.
"""

import os
import sys
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Locate skills directory
SKILLS_DIR = os.path.join(BASE_DIR, "cosmos_skills")
if not os.path.exists(SKILLS_DIR):
    SKILLS_DIR = os.path.join(os.path.dirname(BASE_DIR), "cosmos_skills")

# Locate PARA memory directory
PARA_DIR = os.path.join(BASE_DIR, "cosmos_para_memory")
if not os.path.exists(PARA_DIR):
    PARA_DIR = os.path.join(os.path.dirname(BASE_DIR), "cosmos_para_memory")

# Ensure PARA directories exist
for sub in ["projects", "areas", "resources", "archives", "daily_notes"]:
    os.makedirs(os.path.join(PARA_DIR, sub), exist_ok=True)


class CosmosSkillRegistry:
    def __init__(self):
        self.skills: Dict[str, dict] = {}
        self.indexed = False
        self.load_all_skills()

    def parse_skill_file(self, file_path: str) -> Optional[dict]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            meta = {"name": "", "description": "", "raw_content": content}
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2]
                    for line in frontmatter.splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            meta[k.strip().lower()] = v.strip().strip("'\"")
                    meta["body"] = body.strip()
            else:
                meta["body"] = content.strip()

            if not meta.get("name"):
                meta["name"] = os.path.basename(os.path.dirname(file_path))
            return meta
        except Exception as e:
            return None

    def load_all_skills(self):
        self.skills.clear()
        if not os.path.exists(SKILLS_DIR):
            return

        for root, dirs, files in os.walk(SKILLS_DIR):
            if "SKILL.md" in files:
                skill_path = os.path.join(root, "SKILL.md")
                skill_data = self.parse_skill_file(skill_path)
                if skill_data:
                    name = skill_data.get("name", "").lower()
                    self.skills[name] = skill_data

        self.indexed = True
        print(f"[COSMOS SKILLS]: Indexed {len(self.skills)} cognitive skill modules into memory.", flush=True)

    def match_skill(self, query: str) -> Optional[dict]:
        """Finds the most relevant skill for a spoken or typed command."""
        if not self.skills:
            self.load_all_skills()

        q = query.lower()
        scored: List[Tuple[float, dict]] = []

        keywords_map = {
            "para-memory-files": ["memory", "note", "daily note", "journal", "knowledge", "para", "tacit"],
            "task-planning": ["plan", "planning", "task", "roadmap", "milestone", "breakdown", "todo"],
            "wireframe": ["wireframe", "ui mockup", "svg", "design", "layout", "screen", "frontend mockup"],
            "paperclip-capsules": ["capsule", "status capsule", "widget", "hud card"],
            "directions-lab": ["directions", "design directions", "prototype", "variants"],
            "design-guide": ["design system", "colors", "typography", "tokens", "css guide"],
            "wiki-ingest": ["wiki", "ingest", "synthesize", "document", "knowledge base"],
            "paperclip-distill": ["distill", "standup summary", "recap", "executive digest"],
            "summarize-status": ["status", "executive standup", "blockers", "progress", "update"],
            "paperclip-board": ["governance", "approval", "review gate", "board", "permission"],
            "paperclip-create-agent": ["create agent", "subagent", "role", "spawn agent", "worker"],
            "agent-browser": ["browse", "verify url", "dom", "webpage check", "scrape url"],
            "suggestion-box": ["suggest", "suggestion", "idea", "improvement", "feedback"],
            "complain": ["complain", "complaint", "frustrated", "bug report", "issue report"]
        }

        for skill_name, data in self.skills.items():
            score = 0.0
            # Direct name match
            if skill_name in q:
                score += 10.0
            # Keyword triggers
            for kw in keywords_map.get(skill_name, []):
                if re.search(rf"\b{re.escape(kw)}\b", q):
                    score += 4.5
            # Description substring match
            desc = data.get("description", "").lower()
            if any(w in desc for w in q.split() if len(w) > 4):
                score += 1.5

            if score > 0:
                scored.append((score, data))

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1]
        return None

    def get_para_context(self) -> str:
        """Retrieves today's daily note and active project context."""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_note_path = os.path.join(PARA_DIR, "daily_notes", f"{today}.md")
        context_parts = []
        if os.path.exists(daily_note_path):
            try:
                with open(daily_note_path, "r", encoding="utf-8") as f:
                    context_parts.append(f"[DAILY NOTE {today}]:\n" + f.read(1500))
            except Exception:
                pass
        return "\n\n".join(context_parts)


# Global Singleton Registry
_registry = CosmosSkillRegistry()


def match_and_inject_skill_context(query: str) -> Optional[str]:
    """Matches query to active skills and returns an augmented prompt context."""
    skill = _registry.match_skill(query)
    para = _registry.get_para_context()

    if not skill and not para:
        return None

    injections = []
    if skill:
        name = skill.get("name", "Cognitive Skill")
        body = skill.get("body", "")[:2500]  # Keep context crisp and fast
        injections.append(f"[ACTIVE COSMOS SKILL: {name.upper()}]\n{body}")

    if para:
        injections.append(f"[PARA MEMORY GRAPH]:\n{para}")

    return "\n\n".join(injections)
