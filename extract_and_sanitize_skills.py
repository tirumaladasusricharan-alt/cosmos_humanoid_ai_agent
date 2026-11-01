"""
extract_and_sanitize_skills.py - Sparse Skill Extractor & Sanitizer for COSMOS
Architected exclusively for Sri Charan Tirumaladasu ("Boss" / "Charan" / "Sir")
"""

import os
import shutil
import re

TARGET_SKILL_MAP = {
    # 1. PARA Memory & Knowledge Graph
    "para-memory-files": "_temp_paperclip/skills/para-memory-files/SKILL.md",

    # 2. Wiki & Distillation Engine
    "wiki-ingest": "_temp_paperclip/packages/plugins/plugin-llm-wiki/skills/wiki-ingest/SKILL.md",
    "paperclip-distill": "_temp_paperclip/packages/plugins/plugin-llm-wiki/skills/paperclip-distill/SKILL.md",
    "wiki-query": "_temp_paperclip/packages/plugins/plugin-llm-wiki/skills/wiki-query/SKILL.md",
    "wiki-maintainer": "_temp_paperclip/packages/plugins/plugin-llm-wiki/skills/wiki-maintainer/SKILL.md",
    "wiki-lint": "_temp_paperclip/packages/plugins/plugin-llm-wiki/skills/wiki-lint/SKILL.md",

    # 3. Task Planning & Delegation
    "task-planning": "_temp_paperclip/packages/skills-catalog/catalog/bundled/paperclip-operations/task-planning/SKILL.md",
    "first-task": "_temp_paperclip/server/src/onboarding-assets/first-task/skills/first-task/SKILL.md",
    "paperclip-converting-plans-to-tasks": "_temp_paperclip/skills/paperclip-converting-plans-to-tasks/SKILL.md",
    "delegate-work": "_temp_paperclip/integrations/assistant-plugins/shared/skills/delegate-work/SKILL.md",
    "paperclip-task-bridge": "_temp_paperclip/packages/adapters/hermes/skills/paperclip-task-bridge/SKILL.md",

    # 4. Agent Governance & Role Creation
    "paperclip-board": "_temp_paperclip/skills/paperclip-board/SKILL.md",
    "paperclip-create-agent": "_temp_paperclip/skills/paperclip-create-agent/SKILL.md",

    # 5. Executive Standup & Status
    "summarize-status": "_temp_paperclip/packages/skills-catalog/catalog/bundled/paperclip-operations/summarize-status/SKILL.md",
    "status-card-query": "_temp_paperclip/packages/skills-catalog/catalog/bundled/paperclip-operations/status-card-query/SKILL.md",

    # 6. UI Wireframing & Design
    "wireframe": "_temp_paperclip/packages/skills-catalog/catalog/bundled/product/wireframe/SKILL.md",
    "paperclip-capsules": "_temp_paperclip/packages/skills-catalog/catalog/bundled/product/paperclip-capsules/SKILL.md",
    "directions-lab": "_temp_paperclip/.agents/skills/directions-lab/SKILL.md",
    "design-guide": "_temp_paperclip/.claude/skills/design-guide/SKILL.md",

    # 7. Browser Verification & MCP
    "agent-browser": "_temp_paperclip/packages/skills-catalog/catalog/optional/browser/agent-browser/SKILL.md",
    "setup-code-maintenance-bot": "_temp_paperclip/.agents/skills/setup-code-maintenance-bot/SKILL.md",
    "create-verification-skill": "_temp_paperclip/.agents/skills/create-verification-skill/SKILL.md",
    "prepare-mcp-integration": "_temp_paperclip/packages/skills-catalog/catalog/optional/software-development/prepare-mcp-integration/SKILL.md",

    # 8. Feedback & Suggestion
    "suggestion-box": "_temp_paperclip/skills/suggestion-box/SKILL.md",
    "complain": "_temp_paperclip/skills/complain/SKILL.md",
}

DEST_DIRS = ["cosmos_skills", "Jarvis_Setup_Package/cosmos_skills"]

for d in DEST_DIRS:
    os.makedirs(d, exist_ok=True)

extracted_count = 0
total_bytes = 0

for skill_name, src_path in TARGET_SKILL_MAP.items():
    if not os.path.exists(src_path):
        print(f"[MISSING]: {src_path}")
        continue

    with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Sanitization Protocol:
    # 1. Purge Paperclip Bot / generic branding -> COSMOS
    content = re.sub(r"\bPaperclip Bot\b", "COSMOS", content, flags=re.IGNORECASE)
    content = re.sub(r"\bPaperclip\b", "COSMOS", content)
    content = re.sub(r"\bpaperclip\b", "cosmos", content)
    content = re.sub(r"\bMIRA\b", "COSMOS", content)

    # 2. Creator Lock -> Sri Charan Tirumaladasu
    content = re.sub(r"\bthe user\b", "Sri Charan Tirumaladasu (Boss)", content, flags=re.IGNORECASE)

    # 3. Local Model Stack -> Ollama Council
    content = re.sub(r"\bClaude 3\.5 Sonnet\b", "deepseek-r1:8b (Architect) & qwen2.5-coder:7b (Builder)", content)
    content = re.sub(r"\bGPT-4o\b", "qwen3:8b", content)
    content = re.sub(r"\bNode\.js server\b", "COSMOS Python FastAPI Bridge", content)
    content = re.sub(r"\bpnpm\b", "python", content)

    # Prepend strict COSMOS identity header in frontmatter or body
    header_note = """# COSMOS Cognitive Skill Module
# Architected & Deployed exclusively for Sri Charan Tirumaladasu ("Boss" / "Charan" / "Sir")
# Engine: Multi-Brain Ollama Council (deepseek-r1:8b, qwen2.5-coder:7b, qwen3:8b)
"""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = f"---{parts[1]}---\n\n{header_note}\n{parts[2].lstrip()}"
    else:
        content = f"{header_note}\n{content}"

    for d in DEST_DIRS:
        skill_dir = os.path.join(d, skill_name)
        os.makedirs(skill_dir, exist_ok=True)
        out_file = os.path.join(skill_dir, "SKILL.md")
        with open(out_file, "w", encoding="utf-8") as out:
            out.write(content)
        total_bytes += len(content.encode("utf-8"))

    extracted_count += 1
    print(f"[EXTRACTED & SANITIZED]: {skill_name}")

print(f"\nSuccessfully extracted {extracted_count} skills into ./cosmos_skills/ ({total_bytes / 1024:.1f} KB).")

# Clean up _temp_paperclip immediately to keep 0 MB disk impact
if os.path.exists("_temp_paperclip"):
    print("Deleting _temp_paperclip to maintain ultra-low disk footprint...")
    try:
        shutil.rmtree("_temp_paperclip")
        print("[CLEANUP OK] _temp_paperclip removed completely.")
    except Exception as e:
        print(f"[CLEANUP NOTE]: {e}")
