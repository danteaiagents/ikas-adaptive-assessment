# IKAS — Handover Document

> **For**: New conversation window to continue development  
> **Date**: 2026-08-16  
> **Previous conversation**: [64cf164c](conversation://64cf164c-1aa0-4409-8ca8-8f446db6a1ef)

---

## What is IKAS?

**Intelligent Knowledge Assessment System** — an adaptive assessment platform that evaluates learners across 4 cognitive levels (Repeat → Summary → Intuitive → Apply) using:

- **Neo4j knowledge graph** for concept relationships and question storage
- **Bayesian adaptive engine** (IRT 3PL + BKT + Graph Belief Propagation) for optimal question selection
- **Flask REST API** backend with JWT auth
- **React + TypeScript + Vite** frontend with glassmorphism dark UI

**Core Intent**: Solve the "what to study / where are my gaps" problem for competitive exam preparation.

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Frontend   │────▶│    Nginx     │────▶│  Flask Backend   │────▶│   Neo4j     │
│  React/TS   │     │   :5173      │     │    :5001→5000    │     │  :7474/7687 │
│  Vite build │     │  /api proxy  │     │  Adaptive Engine │     │  50 questions│
└─────────────┘     └──────────────┘     │  JWT Auth        │     │  6 concepts  │
                                         │  Grading Service │     └─────────────┘
                                         └────────┬─────────┘
                                                  │
                                         ┌────────▼─────────┐
                                         │   PostgreSQL     │
                                         │    :5432         │
                                         │  Users/Sessions  │
                                         └──────────────────┘
```

---

## What's Working (Phase 1 ✅)

### Backend — All Verified via E2E Testing
| Endpoint | Status |
|----------|--------|
| `POST /api/v1/register` | ✅ Creates user in PostgreSQL |
| `POST /api/v1/login` | ✅ Returns JWT |
| `POST /api/v1/sessions` | ✅ Creates adaptive engine instance |
| `GET /api/v1/sessions/:id/next` | ✅ Serves adaptive questions with 5 options |
| `POST /api/v1/sessions/:id/answer` | ✅ Grades, updates theta + BKT mastery |
| `POST /api/v1/sessions/:id/complete` | ✅ Returns final theta/SE |
| `GET /api/v1/presets` | ✅ Returns test presets |

### Adaptive Engine — Fully Functional
- IRT 3PL probability model
- EAP theta estimation
- BKT mastery tracking per concept/level
- Graph belief propagation across prerequisites
- Multi-objective question selection (information × entropy × prerequisite × level)
- Stopping criteria: question limit, precision threshold (SE < 0.3)

### Frontend — Integrated with Real Backend
- Login/Register → real JWT auth
- Dashboard → fetches presets from API
- TestPage → adaptive loop (submit answer → get next question → repeat)
- Results → displays theta-derived score with level breakdown
- Question counter shows progress (e.g., "Question 7 of 25")

### Knowledge Graph — 50 Questions Across 6 Concepts
| Concept | Questions |
|---------|-----------|
| What is an LLM | 10 |
| Tokenization | 6 |
| Prompt Engineering | 11 |
| Few-shot / Zero-shot | 6 |
| Temperature & Sampling | 7 |
| Context Windows | 10 |

**Graph stats**: 84 prerequisite edges, 60 CONTAINS edges, 6 resources

---

## Key Files Map

```
IKAS/
├── docker-compose.yml          # 4 containers: backend, frontend, neo4j, postgres
├── project.md                  # Architectural decisions (AD-001 through AD-006)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py         # App factory — model import before db.create_all()
│   │   ├── config.py           # Flask config from env vars
│   │   ├── extensions.py       # db, jwt, cors, neo4j_ext
│   │   ├── api/v1/
│   │   │   ├── __init__.py     # Blueprint + api_response helper
│   │   │   ├── auth.py         # Register/login/refresh/logout
│   │   │   ├── tests.py        # Sessions/next/answer/complete/presets
│   │   │   ├── questions.py    # Question CRUD
│   │   │   └── reports.py      # Report generation
│   │   ├── models/
│   │   │   ├── db_models.py    # User, Organization, TestSession, Response
│   │   │   └── dtos.py         # Pydantic v2 DTOs
│   │   ├── repositories/
│   │   │   ├── question_repo.py  # Neo4j queries + _clean_cypher_json helper
│   │   │   ├── graph_repo.py     # Prerequisite maps, edges
│   │   │   └── user_repo.py      # User CRUD
│   │   └── services/
│   │       ├── adaptive_engine.py  # THE CORE: IRT + BKT + Graph + Selection
│   │       ├── grading_service.py  # MCQ partial credit grading
│   │       ├── session_service.py  # Session lifecycle + engine integration
│   │       ├── report_service.py   # Report generation
│   │       ├── math_utils.py       # IRT probability, Fisher info, EAP, BKT
│   │       └── llm_provider.py     # ABC + Gemini + Ollama factory
│   └── tests/                  # 42 unit tests passing
├── frontend/
│   ├── Dockerfile              # Multi-stage: npm build → nginx serve
│   ├── nginx.conf              # Proxy /api/* → backend:5000
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts       # Axios with JWT interceptor
│   │   │   ├── auth.ts         # Real login/register/logout
│   │   │   └── tests.ts        # Real session/question/answer/complete
│   │   ├── store/
│   │   │   ├── authStore.ts    # Zustand auth state
│   │   │   └── testStore.ts    # Zustand test session + questionNumber
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx / RegisterPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── TestPage.tsx    # Adaptive loop
│   │   │   ├── ResultsPage.tsx # Radar + bar charts
│   │   │   └── ProgressPage.tsx
│   │   └── router.tsx
│   └── package.json
├── knowledge-graph/schema/
│   ├── constraints.cypher
│   └── seed_data.cypher        # 50 questions + concept hierarchy
└── docs/
    └── adaptive_engine_theory.md
```

---

## Known Issues & Technical Debt

| Issue | Details |
|-------|---------|
| **Cypher quote escaping** | Seed data uses Unicode curly quotes. Backend `_clean_cypher_json()` handles this. |
| **Results page** | `levelBreakdown` and `masteryGrid` approximated from theta — backend doesn't return per-level data yet. |
| **Time tracking** | Frontend sends hardcoded `time_taken_seconds: 30`. Should track real time. |
| **Error handling** | No user-visible error toasts. |
| **Port mapping** | Backend on 5001 externally (macOS AirPlay conflict on 5000). |

---

## Environment

```bash
cd /Users/dantepilla/Documents/Antigravity/IKAS
docker compose up -d                           # Start all
docker compose up -d --build backend           # Rebuild after code changes
docker compose up -d --build frontend          # Rebuild frontend
# Frontend: http://localhost:5173
# Backend: http://localhost:5001/api/v1
# Neo4j Browser: http://localhost:7474 (neo4j/ikas_dev_password)
```

---

## User Preferences

- **Monorepo** — no microservices
- **LLM abstraction** — configurable provider, never hardcoded
- **Multi-select checkboxes** — never radio buttons
- **Deployment** — Oracle Cloud (OCI) Always Free Tier
- **Core intent** — competitive exam gap identification

---

## Phase 2 Roadmap (Next)

| Component | Changes |
|-----------|---------|
| **Grading Service** | 4-tier hybrid: Sanity → SBERT → LLM rubric → Confidence |
| **Question Types** | Free-text, image upload, code link |
| **Frontend** | Rich text editor, file upload, error toasts, real time tracking |
| **Reports** | D3.js knowledge gap graph, per-level breakdown, exportable PDF |
| **More Questions** | Add topics: AI Agents, AI Tools & Frameworks, RAG |
| **Test Config** | Admin panel for blueprints |

## Phase 3 & 4 (Future)
- Phase 3: Shadow testing, exposure control, recalibration agent, multi-subject, ontology
- Phase 4: Agentic orchestration, continuous question gen, automated QA, Jira
