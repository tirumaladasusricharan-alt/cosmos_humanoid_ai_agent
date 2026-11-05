# ARCHITECTURE DECISION RECORDS (ADR)
## COSMOS 3D Humanoid AI Companion
**Creator, Architect & Sole Authority:** Sri Charan Tirumaladasu ("Boss" / "Charan" / "Sir")

---

### ADR-001: Zero-Regression Multi-Brain Cognitive Architecture
- **Date:** 2026-11-04
- **Status:** Accepted
- **Context:** Need autonomous intelligence spanning local reasoning (DeepSeek-R1, Qwen2.5-Coder), cloud speed (Groq), real-time web search, and 25 Paperclip skills without disk bloat.
- **Decision:** Multi-Brain Council routing with strict local priority, in-memory streaming, and failover to Groq API.
- **Consequences:** 0 MB extra disk storage used; instant failover if any single model is offline.

---

### ADR-002: Persistent Cognee Knowledge Graph Subsystem
- **Date:** 2026-11-04
- **Status:** Accepted
- **Context:** Flat vector stores lack relational context for creator biodata, company entities, and companion bonds.
- **Decision:** Integrated Topoteretes/Cognee two-tier Knowledge Graph with zero-dependency JSON fallback at `./cosmos_agent_company/cognee_fallback_graph.json` and live `/api/cognee/*` endpoints.
- **Consequences:** Sri Charan Tirumaladasu is permanently established as the ontological root node.

---

### ADR-003: CopilotKit/OpenBot Governance & Human Handoff
- **Date:** 2026-11-05
- **Status:** Accepted
- **Context:** Automated computer-use requires strict safety against accidental destructive actions and secure human handoff at login/CAPTCHA walls.
- **Decision:** Ported OpenBot's 8 capabilities (Fail-Closed Policy Gateway, Take the Wheel state machine, Zero-Leak Secret Scrubber, 15-minute routine floor, and isolated browser profile).
- **Consequences:** Secrets never leak into logs; Sri Charan Tirumaladasu can take the wheel at any time.

---

### ADR-004: Ruflo Swarm, SPARC & Trajectory Self-Learning Harness
- **Date:** 2026-11-05
- **Status:** Accepted
- **Context:** Complex software engineering requires disciplined phase gates (SPARC), competitive multi-model tournaments (Arena), and verified trajectory self-learning.
- **Decision:** Implemented `cosmos_ruflo_harness.py` covering SPARC 5-phase gates, Arena tournaments, trajectory caching, token burn monitoring, and prompt injection defense.
- **Consequences:** 100% zero-regression, 0 MB disk footprint, automated code verification via AST parsing.

