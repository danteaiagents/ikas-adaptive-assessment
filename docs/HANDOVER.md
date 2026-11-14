# IKAS — Handover Document

> **For**: New conversation window to continue development  
> **Updated**: September 28, 2026 — Sprint 2 complete + bug fixes, Sprint 3 next  
> **Previous conversation**: [87ffccdd](conversation://87ffccdd-5028-46c9-af1f-28eb84517c2a)

---

## What is IKAS?

**Intelligent Knowledge Assessment System** — an adaptive assessment platform that evaluates learners across 4 cognitive levels (Repeat → Summary → Intuitive → Apply) using:

- **Neo4j knowledge graph** for concept relationships and question storage
- **Bayesian adaptive engine** (IRT 3PL + BKT + Graph Belief Propagation) for optimal question selection
- **Flask REST API** backend with JWT auth
- **React + TypeScript + Vite** frontend with glassmorphism dark UI

**Core Intent**: Solve the "what to study / where are my gaps" problem for competitive exam preparation.

---

## Current Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 (E2E adaptive MCQ system) | ✅ Complete | 83 tests passing |
| Phase 2 Sprint 0 — Code | ✅ Complete | AnthropicProvider, OCI deploy files, config |
| Phase 2 Sprint 0 — OCI Deployment | 🔄 In Progress | Blocked on ARM capacity in Toronto (see below) |
| Phase 2 Sprint 1 — Reports & Toasts | ✅ Complete | Real reports, heatmap, progress, toasts |
| Phase 2 Sprint 2 — 3 new topics + dynamic UI | ✅ **Complete** | 200 questions / 4 topics; dynamic dashboard; multi-select topic checkboxes |
| Phase 2 Sprint 2 — Bug fixes (post-testing) | ✅ **Complete** | See "Sprint 2 Bug Fixes" section below |
| Phase 2 Sprint 3 — (see plan below) | ⏳ **Start Next** | |
| Phase 2 Sprint 4 — Admin panel + integration tests | ⏳ Pending | |

---

## OCI Deployment Status (Sprint 0)

All deployment **code and scripts are ready** in `deploy/oci/`. The blocker is OCI infrastructure:

### What's Done
- ✅ OCI account created (tenancy: `ikas-dev`, region: Canada Southeast / Toronto `ca-toronto-1`)
- ✅ VCN `ikas-vcn` created with public subnet and internet gateway
- ✅ All deploy files ready: `docker-compose.prod.yml`, `nginx.conf`, `setup.sh`, `seed.sh`, `README.md`
- ✅ `AnthropicProvider` added to `llm_provider.py`
- ✅ `anthropic>=0.40.0` and `oci>=2.120.0` added to `requirements.txt`
- ✅ OCI config vars added to `config.py`

### Current Blocker
OCI Toronto (ca-toronto-1) has **only 1 Availability Domain** and ARM capacity (`VM.Standard.A1.Flex` — 4 OCPU, 24GB) is currently exhausted. Free Tier accounts are capped at 1 region so cannot switch to Ashburn.

**Resolution options (user is handling):**
1. **Keep retrying** — try creating the VM during off-peak hours (midnight–6am). Capacity frees up as other users terminate instances.
2. **Contact Oracle support** — request ARM capacity reservation or region limit increase.
3. **Alternative deployment** — Railway + Neo4j AuraDB + Supabase (all free tiers) if OCI remains blocked.

> [!NOTE]
> OCI deployment is **NOT blocking Sprint 1, 2, or 3**. All development runs locally on Docker. Come back to OCI deployment whenever capacity opens up.

### Once OCI VM is Available
Follow [`deploy/oci/README.md`](file:///Users/dantepilla/Documents/Antigravity/IKAS/deploy/oci/README.md) — full step-by-step guide. Key commands:
```bash
# On OCI VM
./setup.sh                                                    # One-time VM setup
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
export NEO4J_PASSWORD=your_password && ./seed.sh             # Seed knowledge graph
```

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Frontend   │────▶│    Nginx     │────▶│  Flask Backend   │────▶│   Neo4j     │
│  React/TS   │     │  :80 (prod)  │     │    :5000         │     │  :7687      │
│  Vite build │     │  :5173 (dev) │     │  Adaptive Engine │     │  50 questions│
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

## Local Development Environment

```bash
cd /Users/dantepilla/Documents/Antigravity/IKAS

# Start all containers
docker compose up -d

# Rebuild backend (after Python changes or new dependencies)
docker compose up -d --build backend

# Run tests
docker compose exec backend python -m pytest tests/ -v
# Expected: 83 passed

# URLs
# Frontend:    http://localhost:5173
# Backend API: http://localhost:5001/api/v1
# Neo4j UI:    http://localhost:7474  (neo4j / ikas_dev_password)
# Postgres:    localhost:5432         (ikas_user / ikas_dev_password)
```

> [!IMPORTANT]
> Backend is on port **5001** externally (macOS AirPlay conflict on 5000). Port 5000 is used inside Docker.

---

## LLM Provider

**Default: Anthropic Claude** (`claude-sonnet-4-20250514`)

```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
LLM_API_KEY=sk-ant-...
```

Supported providers: `anthropic` | `gemini` | `ollama`  
Implementation: [`backend/app/services/llm_provider.py`](file:///Users/dantepilla/Documents/Antigravity/IKAS/backend/app/services/llm_provider.py)

> [!NOTE]
> The LLM provider is NOT called by anything yet — it's wired up and ready but only used starting Sprint 3 (free-text grading). For Sprints 1 & 2, no API key is needed.

---

## What's Working (Phase 1 ✅)

### Backend Endpoints
| Endpoint | Status |
|----------|--------|
| `POST /api/v1/register` | ✅ |
| `POST /api/v1/login` | ✅ Returns JWT |
| `POST /api/v1/sessions` | ✅ Creates adaptive engine, respects presets |
| `GET /api/v1/sessions/:id/next` | ✅ Adaptive question selection |
| `POST /api/v1/sessions/:id/answer` | ✅ Grades, updates theta + BKT |
| `POST /api/v1/sessions/:id/complete` | ✅ Returns real BKT mastery data |
| `GET /api/v1/presets` | ✅ quick (10q/15min), standard (25q/45min), comprehensive (50q/90min) |

### Adaptive Engine
- ✅ IRT 3PL + EAP theta estimation
- ✅ BKT mastery tracking per concept/level
- ✅ Graph belief propagation across prerequisites
- ✅ Multi-objective selection (Fisher info × entropy × prereq × level)
- ✅ Concept frontier filtering (Zone of Proximal Development)
- ✅ Stopping: question limit, precision (SE < 0.3)

### Knowledge Graph
- ✅ 50 questions, 6 concepts, topic `t-ai-llm` (LLMs & Prompting)
- ✅ 84 prerequisite edges, 4 cognitive levels per concept

### Tests
```bash
docker compose exec backend python -m pytest tests/ -v
# 83 passed (test_adaptive_engine.py: 42, test_behavioral_fixes.py: 40, test_api.py: 1 placeholder)
```

---

## Key Files Map

```
IKAS/
├── .gitignore                          # Includes .env.production, oci_account_details.md
├── docker-compose.yml                  # Local dev: 4 containers
├── project.md                          # Architectural decisions AD-001–AD-006
├── deploy/
│   └── oci/
│       ├── README.md                   # Step-by-step OCI deployment guide ✅
│       ├── docker-compose.prod.yml     # Production compose ✅
│       ├── nginx.conf                  # Production nginx (rate limiting, HTTPS-ready) ✅
│       ├── .env.production.example     # Template — copy to .env.production ✅
│       ├── setup.sh                    # One-time VM setup script ✅
│       ├── seed.sh                     # Neo4j seeder script ✅
│       └── oci_account_details.md      # Personal OCI account info (gitignored) ✅
├── backend/
│   ├── requirements.txt                # anthropic>=0.40.0, oci>=2.120.0 added
│   └── app/
│       ├── config.py                   # OCI_* vars added, LLM defaults to Anthropic
│       ├── api/v1/
│       │   ├── auth.py
│       │   ├── tests.py                # Sessions/next/answer/complete/presets
│       │   ├── questions.py
│       │   └── reports.py              # ⚠️ STUB — Sprint 1 wires this up
│       ├── models/
│       │   ├── db_models.py
│       │   └── dtos.py                 # SessionStart uses Optional[int] (preset bug fixed)
│       └── services/
│           ├── adaptive_engine.py      # Core engine
│           ├── grading_service.py      # MCQ only — Sprint 3 adds free_text/image
│           ├── session_service.py      # Session lifecycle
│           ├── report_service.py       # ⚠️ STUB — Sprint 1 enhances
│           ├── math_utils.py
│           └── llm_provider.py         # ✅ Anthropic + Gemini + Ollama
├── frontend/
│   └── src/
│       ├── api/
│       │   ├── client.ts               # Axios + JWT interceptor (no error toasts yet)
│       │   ├── auth.ts
│       │   ├── tests.ts                # Real API integration
│       │   └── reports.ts              # ⚠️ getProgress() HARDCODED — Sprint 1 fix
│       ├── store/
│       │   ├── authStore.ts
│       │   └── testStore.ts            # questionStartTime for real time tracking
│       └── pages/
│           ├── DashboardPage.tsx       # ⚠️ HARDCODED "LLMs & Prompting" — Sprint 2 fix
│           ├── TestPage.tsx
│           ├── ResultsPage.tsx         # ✅ Shows real BKT mastery data
│           └── ProgressPage.tsx        # ⚠️ HARDCODED session history — Sprint 1 fix
└── knowledge-graph/schema/
    ├── constraints.cypher
    └── seed_data.cypher                # 50 questions, t-ai-llm topic
```

---

## Known Issues / Tech Debt

| Item | Sprint | File |
|------|--------|------|
| ~~`getProgress()` returns hardcoded data~~ | ✅ Sprint 1 done | `frontend/src/api/reports.ts` |
| ~~ProgressPage uses hardcoded session history~~ | ✅ Sprint 1 done | `frontend/src/pages/ProgressPage.tsx` |
| ~~ResultsPage recommendations always `[]`~~ | ✅ Sprint 1 done | `frontend/src/pages/ResultsPage.tsx` |
| ~~No error toasts on network failures~~ | ✅ Sprint 1 done | `frontend/src/api/client.ts` |
| Dashboard hardcodes "LLMs & Prompting" | Sprint 2 | `frontend/src/pages/DashboardPage.tsx` |
| `test_api.py` is a placeholder | Sprint 4 | `backend/tests/test_api.py` |
| ProgressPage hardcodes topic_id `'t-ai-llm'` | Sprint 2 | `frontend/src/pages/ProgressPage.tsx` |

---

## Future Backlog — Adaptive Engine Calibration

> These are **not immediate** — add to the Sprint 4+ backlog once real response data is collected (~1,000+ sessions).

### Backlog Item 1: Periodic BKT / Mastery Threshold Calibration

**Trigger:** Quarterly (or after every 1,000 completed sessions)

The mastery threshold (`ENGINE_MASTERY_THRESHOLD`, default 0.70) and BKT transition parameters (`BKT_P_TRANSIT`, `BKT_P_GUESS`, `BKT_P_SLIP`) are currently expert-derived priors. Once real data is available:

1. Export all `Response` rows from PostgreSQL → compute empirical guess rates per question/level
2. Run EM (Expectation-Maximisation) on BKT params to fit observed pass/fail sequences
3. Validate mastery threshold by checking: do students who cross 0.70 actually perform well on the next level? (i.e., does the Summary pass rate correlate with Repeat mastery ≥ 0.70?)
4. Update env vars in `docker-compose.yml` (no code change needed):
   ```
   ENGINE_MASTERY_THRESHOLD=0.68
   BKT_P_TRANSIT=0.12
   ```

### Backlog Item 2: Multi-Objective Weight Optimisation

**Trigger:** After ~5,000 sessions

The scoring weights (`ALPHA=0.35 Fisher, BETA=0.25 Graph, GAMMA=0.20 Prereq, DELTA=0.20 Level`) were set using domain expertise from the CAT literature. To validate and improve:

1. **A/B test**: Run two engine configurations (e.g. higher Fisher weight vs higher Level weight) on different user cohorts
2. **Metric**: Measure learning gain — compare pre/post theta improvement across sessions per weight configuration
3. **Optimise**: Use Bayesian optimisation (e.g. `scikit-optimize`) over the 4-dimensional weight simplex (α+β+γ+δ=1) to find the combination maximising learning gain
4. Update via env vars — no code changes required:
   ```
   ENGINE_WEIGHT_ALPHA=0.30
   ENGINE_WEIGHT_BETA=0.30
   ENGINE_WEIGHT_GAMMA=0.20
   ENGINE_WEIGHT_DELTA=0.20
   ```

**Note:** Both calibration processes are purely data + env-var changes. The engine architecture already supports this — all parameters are read from Flask config at session start.


## Phase 2 Sprint Plan

| Sprint | Focus | Status |
|--------|-------|--------|
| **Sprint 0** | OCI Deployment + AnthropicProvider | ✅ Code done / 🔄 OCI pending |
| **Sprint 1** | Reports, Progress, Error Toasts | ⏳ **START HERE** |
| **Sprint 2** | 3 new topics (~150 questions via Claude) | ⏳ |
| **Sprint 3** | Free-text/image/code questions + Claude grading | ⏳ |
| **Sprint 4** | Admin panel + integration tests | ⏳ |

**Full plan**: See [`implementation_plan.md`](file:///Users/dantepilla/.gemini/antigravity/brain/a1c9d38c-6910-4879-9944-3e96c70d19b2/implementation_plan.md)

---

## Sprint 1 Scope (What to Build Next)

### Backend
1. Enhance `report_service.py` — per-concept mastery with human-readable names (query Neo4j), recommended resources for weak concepts, time analysis
2. Wire `GET /api/v1/progress` in `reports.py` → `get_user_progress()`
3. Wire `GET /api/v1/sessions/:id/report` in `reports.py` → `generate_session_report()`

### Frontend
4. Replace hardcoded `getProgress()` in `reports.ts` with real API call
5. Update `ResultsPage.tsx` — human-readable concept names, real recommendations, per-concept × per-level heatmap
6. Update `ProgressPage.tsx` — real data, session history table, stats cards
7. Create `Toast.tsx` + Zustand toast store
8. Add Axios error interceptor in `client.ts` → trigger toasts on 4xx/5xx

---

## User Preferences

- **Monorepo** — no microservices
- **LLM abstraction** — configurable provider, never hardcoded. Default: Anthropic Claude
- **Multi-select checkboxes** — never radio buttons anywhere in the system
- **Deployment** — Oracle Cloud (OCI) Always Free Tier
- **Core intent** — competitive exam gap identification
- **Question generation** — LLM-generated (hybrid: human-in-the-loop curation planned for future)
- **Backend port** — 5001 externally on Mac (AirPlay conflict on 5000)
- **Topic flexibility** — 4-tier model (Overall → User-selected → Themes → Baskets); see backlog below

---

## Future Backlog — Topic Flexibility (4-Tier Model)

> **Safe to defer.** No breaking design changes needed now. All 4 options are additive layers on top of the current `topic_id` field. The engine, question repo, and session service are unchanged — they just receive a resolved list of `topic_ids` at session start.

### User Clarifications (2026-09-22)

- **Concept count per topic**: Allow variable 5–8 per topic for natural fit (not locked at 6).
- **Dashboard layout**: 2-column grid with **checkbox-style multi-select** (no radio buttons). ✅ **Done** — DashboardPage updated in Sprint 2.
- **Progress page topic switching**: Dropdown for now; upgrade to tab bar when >4 topics. ✅ **Done** — Sprint 2.
- **Multi-topic benchmarks**: When a student combines topics, the system must use **different mastery thresholds and scoring weights** vs. single-topic mode. This is a key design constraint — see "Multi-Topic Benchmark Design" below.

### Multi-Topic Benchmark Design (Required before Option 2 goes live)

When `len(topic_ids) > 1`, the current single-topic thresholds (`MASTERY_THRESHOLD=0.70`, Fisher/GraphEntropy weights) are no longer appropriate because:

1. **Question difficulty spread** is wider across topics (IRT `b` params span more range)
2. **Graph entropy** of a merged concept graph is higher by default (more nodes, more edges)
3. **Prerequisite readiness** score loses meaning when concepts across topics are not prerequisite to each other

**Proposed approach (to be implemented with Option 2):**

```python
# In adaptive_engine.py _get_engine_config()
def _get_engine_config(multi_topic: bool = False):
    if multi_topic:
        return {
            # Slightly more lenient mastery threshold for combined tests
            'mastery_threshold': float(os.environ.get('ENGINE_MASTERY_THRESHOLD_MULTI', '0.65')),
            # Downweight GraphEntropy (meaningless across disconnected topic graphs)
            'weight_graph_entropy': float(os.environ.get('ENGINE_WEIGHT_GRAPH_ENTROPY_MULTI', '0.10')),
            # Upweight Fisher (pure IRT discrimination, topic-agnostic)
            'weight_fisher': float(os.environ.get('ENGINE_WEIGHT_FISHER_MULTI', '0.45')),
            'weight_prereq': float(os.environ.get('ENGINE_WEIGHT_PREREQ_MULTI', '0.25')),
            'weight_level_bonus': float(os.environ.get('ENGINE_WEIGHT_LEVEL_BONUS_MULTI', '0.20')),
            # BKT unchanged — per-concept state is still valid
        }
    else:
        return _single_topic_config()  # existing logic
```

**DB migration needed:**
```sql
ALTER TABLE test_sessions ADD COLUMN topic_ids JSONB;   -- array of topic IDs
ALTER TABLE test_sessions ADD COLUMN is_multi_topic BOOLEAN DEFAULT FALSE;
```

**Progress page**: When `is_multi_topic=True`, group history by subject, not individual topic.

---

### The 4 Options (in implementation order)

| Option | Name | Who controls | Effort | Status |
|--------|------|-------------|--------|--------|
| 1 | **Overall** | System | XS | Backlog — Sprint 3 |
| 2 | **User selects topics** | Student | S | UI done ✅ · Backend pending · Sprint 3 |
| 3 | **Themes** (system-grouped) | Admin (static) | M | Sprint 4 |
| 4 | **Baskets** (custom combinations) | Admin (dynamic) | L | Sprint 5 |

---

### Option 1 — Overall (All Topics)

Add a virtual `topic_id = 'all'` that resolves to every topic under a subject.

**Backend change:** In `session_service.start_session()`, if `topic_id == 'all'`, fetch all topic IDs for the subject and pass the full question pool to the engine. Single-line change.

**Frontend change:** Add \"Overall — All Topics\" as the first checkbox option in the topic selector (already multi-select capable after Sprint 2).

**DB change:** None.

---

### Option 2 — User Selects Topics (Multi-select)

Student checks which topics they want included before starting a test.

**Frontend:** ✅ **Done** — Multi-select checkboxes on DashboardPage. Currently shows a "coming soon" notice when >1 topic selected; test still runs on first topic only.

**Remaining backend work:** Pass `topic_ids: List[str]` to `POST /sessions`, merge question pools, use multi-topic engine config. See "Multi-Topic Benchmark Design" above.

**Backend — `SessionStart` DTO:**
```python
class SessionStart(BaseModel):
    topic_ids: List[str]          # replaces single topic_id
    preset: str = 'standard'
    total_questions: Optional[int] = None
    time_limit_minutes: Optional[int] = None
```

**Backend — `TestSession` migration:**
```sql
-- Additive: keep topic_id for single-topic sessions, add topic_ids for multi
ALTER TABLE test_sessions ADD COLUMN topic_ids JSONB;
ALTER TABLE test_sessions ADD COLUMN is_multi_topic BOOLEAN DEFAULT FALSE;
```

**Engine:** No change to selection logic — `get_candidate_questions` already accepts a list; just pass all topics' question pools merged.

**Progress tracking:** Group by subject (not individual topic) when `is_multi_topic=True`.

---

### Option 3 — Themes (System-Grouped Topics)

Admin defines a named grouping of topics that the system presents as a single selectable option. Themes are static (defined in Neo4j or seed data, not user-editable).

**Neo4j schema addition:**
```cypher
CREATE (:Theme {id: 'theme-llm-foundations', name: 'LLM Foundations', description: 'Core concepts of language models and prompting'});
MATCH (th:Theme {id: 'theme-llm-foundations'}), (t:Topic) WHERE t.id IN ['t-ai-llm', 't-ai-agents']
CREATE (th)-[:INCLUDES]->(t);
```

**New API endpoint:**
```
GET /api/v1/themes          → list all themes with their topics
GET /api/v1/themes/:id      → single theme detail
```

**Session creation:** Client passes `theme_id` instead of `topic_ids`; backend resolves to topic list via Neo4j query before starting session.

**DB change:** Add nullable `theme_id VARCHAR` to `test_sessions`. No migration needed until Sprint 3.

---

### Option 4 — Baskets (Admin-Created Custom Combinations)

Admin or super-admin creates named sets of topics. Baskets are global (visible to all students). Students pick from a basket the same way they pick a topic.

**PostgreSQL schema (new tables):**
```sql
CREATE TABLE baskets (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(120) NOT NULL,
    description TEXT,
    created_by  UUID REFERENCES users(id),
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE basket_topics (
    basket_id   UUID REFERENCES baskets(id) ON DELETE CASCADE,
    topic_id    VARCHAR(80) NOT NULL,
    PRIMARY KEY (basket_id, topic_id)
);
```

**New API endpoints (admin-gated with `role='instructor'` check):**
```
GET    /api/v1/baskets              → list all active baskets
POST   /api/v1/baskets              → create basket {name, description, topic_ids}
PUT    /api/v1/baskets/:id          → update basket
DELETE /api/v1/baskets/:id          → soft-delete (is_active=false)
GET    /api/v1/baskets/:id/topics   → get topics in basket
```

**Session creation:** Client passes `basket_id`; backend resolves to `topic_ids` via basket_topics join before starting session.

**DB change:** Add nullable `basket_id UUID` to `test_sessions`.

---

### Unified Resolution Pattern (Backend)

All 4 options converge to the same engine call. In `session_service.start_session()`:

```python
def _resolve_topic_ids(topic_id=None, topic_ids=None, theme_id=None, basket_id=None) -> List[str]:
    if basket_id:
        return [bt.topic_id for bt in BasketTopic.query.filter_by(basket_id=basket_id).all()]
    if theme_id:
        return get_topic_ids_for_theme(theme_id)   # Neo4j query
    if topic_ids:
        return topic_ids
    if topic_id == 'all':
        return get_all_topic_ids()                 # Neo4j query
    return [topic_id]                              # current behaviour — unchanged
```

The engine always sees a flat list of question candidates regardless of which option was used. **Zero engine changes required.**

---

### Implementation Notes

- Options 1 & 2 should land in **Sprint 2** alongside topic seeding (they share the same DashboardPage work)
- Options 3 & 4 should land in **Sprint 4** alongside the Admin panel
- The `basket_topics` table is the only new PostgreSQL table; use Alembic migration
- Baskets are global by design — no per-user baskets. This matches the stated requirement.
- All basket CRUD endpoints require `role IN ('instructor', 'admin')` guard
