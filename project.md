# IKAS — Intelligent Knowledge Assessment System

## Project Reference Document

> This document serves as the canonical reference for the IKAS project. It captures all architectural decisions, answered questions, technology choices, and conventions. Future sessions should read this file first for context.

---

## Project Identity

| Field | Value |
|-------|-------|
| **Project Name** | IKAS (Intelligent Knowledge Assessment System) |
| **Repository** | Monorepo at `/Users/dantepilla/Documents/Antigravity/IKAS` |
| **Structure** | `backend/` (Flask) · `frontend/` (React) · `knowledge-graph/` (agents, schema, seed data) |
| **Jira** | [Atlassian Home](https://home.atlassian.com/o/13965868-fbd6-41c0-8189-1730ef64c427/?cloudId=e3eb6984-92f7-4415-a8f6-475be69f24a6) — new project to be created |
| **Confluence** | To be set up — will store implementation plan, architecture docs, and decision log |

---

## Core Philosophy

IKAS assesses learners across **four cognitive knowledge levels** (adapted from Bloom's Taxonomy):

| Level | Description | Question Style | Answer Style |
|-------|------------|----------------|--------------|
| **Repeat** | Memorized facts, definitions, rules — absorbed AS IS | Direct factual recall | Multi-select MCQ (straightforward options, never radio buttons) |
| **Summary** | Comprehension, ability to explain and synthesize | Broad questions requiring concept association | Free-text narrative, or image upload (drawing/diagram) |
| **Intuitive Understanding** | Deep clarity — connected to prior knowledge, "aha moment" | Confusing/tricky options, rephrased with subtle omissions, multiple correct answers needed | Multi-select MCQ (deliberately confusing distractors) |
| **Apply** | Problem-solving with real-world application | Scenario-based situations | Free-text, GitHub link, image upload, or combination |

**Key Principle**: Questions always use multi-select checkboxes — never radio buttons anywhere in the system.

---

## Technology Stack

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| **Knowledge Graph DB** | Neo4j Community Edition | 5.x | Single database, subject-level partitioning via labels. Ontology-ready design. |
| **Relational DB** | PostgreSQL | 16.x | User profiles, session history, response logs, aggregated data |
| **Backend** | Flask | 3.x | Python 3.12+, REST API, Pydantic v2 DTOs |
| **Frontend** | React + TypeScript + Vite | React 19, Vite 6 | Zustand state, React Router v7 |
| **Auth** | JWT (flask-jwt-extended) | — | Access tokens in memory, refresh in HttpOnly cookies |
| **LLM Integration** | Configurable provider abstraction | — | Supports Gemini, OpenAI, Anthropic, Ollama (local). Default: Gemini. |
| **Answer Evaluation** | Hybrid pipeline | — | Auto-grade MCQ + LLM rubric grading (configurable model) |
| **Question Generation** | Agentic skills (not full agents) | — | Per-level generator skills + review agent + graph populator |
| **Visualization** | Recharts (charts) + D3.js (knowledge graphs) | — | Progress reports, knowledge maps |
| **Containerization** | Docker + Docker Compose | — | Local dev: Neo4j, PostgreSQL, Flask, React containers |

### LLM Provider Abstraction

All LLM calls go through a configurable provider interface:

```python
# Conceptual interface — actual implementation in backend/app/services/llm_provider.py
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str, **kwargs) -> str: ...
    @abstractmethod  
    def generate_structured(self, prompt: str, schema: dict, **kwargs) -> dict: ...

# Implementations:
# - GeminiProvider (default)
# - OpenAIProvider
# - AnthropicProvider
# - OllamaProvider (local, free)
```

Configuration via environment variable:
```env
LLM_PROVIDER=gemini          # or: openai, anthropic, ollama
LLM_MODEL=gemini-2.5-flash   # model name within provider
LLM_API_KEY=...              # provider-specific key
LLM_BASE_URL=...             # for Ollama: http://localhost:11434
```

---

## Adaptive Engine — Bayesian Inference Architecture

The Adaptive Engine is the core intelligence of IKAS. It combines three complementary mathematical techniques to select optimal questions and track learner mastery in real-time.

### 1. Item Response Theory (IRT) — 3-Parameter Logistic Model

IRT models the probability of a student answering question $j$ correctly given their latent ability $\theta$:

$$P_j(\theta) = c_j + \frac{1 - c_j}{1 + \exp\left(-a_j (\theta - b_j)\right)}$$

| Parameter | Symbol | Description | Range |
|-----------|--------|-------------|-------|
| **Ability** | $\theta$ | Student's latent ability estimate | -3.0 to +3.0 (normalized) |
| **Difficulty** | $b_j$ | Question difficulty | -3.0 to +3.0 |
| **Discrimination** | $a_j$ | How sharply the question differentiates ability levels (slope at inflection) | 0.1 to 3.0 |
| **Guessing** | $c_j$ | Probability of guessing correctly (lower asymptote, e.g., 0.25 for 4-option MCQ) | 0.0 to 0.25 |

**Ability Estimation**: We use Expected A Posteriori (EAP) estimation via Gauss-Legendre quadrature (30 nodes) to compute the student's posterior ability after each answer. EAP is more stable than Maximum Likelihood Estimation (MLE) in early test stages when few responses are available.

**Fisher Information** for item selection (how much information a question provides at the current ability estimate):

$$I_j(\theta) = a_j^2 \cdot \frac{1 - P_j(\theta)}{P_j(\theta)} \cdot \left[\frac{P_j(\theta) - c_j}{1 - c_j}\right]^2$$

### 2. Bayesian Knowledge Tracing (BKT)

BKT is a Hidden Markov Model tracking binary mastery state per concept per cognitive level. Each concept-level pair (e.g., "Prompt Engineering at Repeat level") has an independent BKT tracker.

**Core Parameters**:

| Parameter | Symbol | Description | Default |
|-----------|--------|-------------|---------|
| **Prior mastery** | $P(L_0)$ | Initial probability the student has mastered this concept-level | 0.5 (uniform prior) |
| **Transition** | $P(T)$ | Probability of transitioning from unmastered to mastered after a learning opportunity | 0.1 |
| **Guess** | $P(G)$ | Probability of guessing correctly when unmastered | 0.2 |
| **Slip** | $P(S)$ | Probability of answering incorrectly when mastered | 0.1 |

**Posterior Update** (after observing a correct or incorrect answer):

If correct:
$$P(L_t \mid \text{correct}) = \frac{P(L_t) \cdot (1 - P(S))}{P(L_t) \cdot (1 - P(S)) + (1 - P(L_t)) \cdot P(G)}$$

If incorrect:
$$P(L_t \mid \text{incorrect}) = \frac{P(L_t) \cdot P(S)}{P(L_t) \cdot P(S) + (1 - P(L_t)) \cdot (1 - P(G))}$$

**State Transition** (learning opportunity):
$$P(L_{t+1}) = P(L_t \mid O_t) + (1 - P(L_t \mid O_t)) \cdot P(T)$$

### 3. Graph Belief Propagation

When a student answers question $Q_A$, we propagate updated beliefs to connected questions $Q_B$ via the prerequisite edges in the knowledge graph:

$$P(Q_B = 1) = P(Q_B = 1 \mid Q_A = 1) \cdot P(Q_A = 1) + P(Q_B = 1 \mid Q_A = 0) \cdot (1 - P(Q_A = 1))$$

- `p_pass_given_pass` and `p_pass_given_fail` are stored as edge properties in Neo4j
- Initialized at 0.5 (uniform prior) and recalibrated over time from accumulated student response data
- Propagation uses dampened updates (50% blend with current state) to prevent oscillation

### 4. Multi-Objective Item Selection

The next question is NOT selected purely by Fisher Information. Instead, we maximize a composite score that accounts for the knowledge graph structure:

$$\text{Score}(q) = \alpha \cdot I_q(\hat{\theta}) + \beta \cdot \text{GraphEntropy}(q) + \gamma \cdot \text{PrereqReadiness}(q) + \delta \cdot \text{LevelProgression}(q)$$

| Component | Weight | Description |
|-----------|--------|-------------|
| **Fisher Information** | $\alpha$ | Classic IRT — how much info this question provides at current ability |
| **Graph Entropy** | $\beta$ | Information gain — how much answering this reduces uncertainty across the graph |
| **Prerequisite Readiness** | $\gamma$ | Proportion of prerequisite questions already answered correctly (avoids asking questions the student isn't ready for) |
| **Level Progression** | $\delta$ | Bonus for testing the next cognitive level up from current demonstrated mastery (drives upward through Repeat → Summary → Intuitive → Apply) |

**Concept Frontier**: The candidate question pool is filtered to the "frontier" — concepts whose prerequisites have been mastered ($P(mastery) \geq \tau$) but which themselves are not yet mastered ($P(mastery) < \tau$). This mirrors the Zone of Proximal Development in educational theory.

### 5. Adaptive Test Flow

1. **Session Start**: Student selects topic and test preset (or custom config). Engine initializes BKT state for all concepts in that topic at uniform priors.
2. **First Question**: Engine starts with a Repeat-level question on a foundational concept (no prerequisites needed).
3. **Answer Submitted**: Engine grades the answer, stores response in PostgreSQL, updates IRT θ estimate (EAP), updates BKT mastery for the concept-level, and propagates beliefs through prerequisite edges.
4. **Next Question Selection**: Engine computes the composite score for all candidate questions on the concept frontier and selects the highest-scoring question.
5. **Adaptive Behavior**:
   - Correct answers on Repeat → engine moves to Summary questions for that concept
   - Correct on Summary → engine tests Intuitive Understanding
   - Correct on Intuitive → engine poses Apply-level scenario
   - Incorrect answers → engine probes prerequisite concepts to locate the gap
6. **Stopping Criteria**: Test ends when question limit is reached, time limit expires, or the standard error of θ falls below a threshold (ability is precisely estimated).
7. **Report Generation**: Engine produces a per-level, per-concept mastery report with resource recommendations targeted at the specific knowledge level where gaps exist.

### 6. Probability Recalibration (Scheduled Agent)

Over time, as more students take tests, the system accumulates response data that enables better probability estimates:

- **Edge Probabilities**: The recalibration agent queries the `responses` table for all student answers to connected question pairs $(Q_A, Q_B)$, computes empirical conditional probabilities, and blends them with priors using Bayesian smoothing.
- **IRT Parameters**: Item difficulty ($b$), discrimination ($a$), and guessing ($c$) are re-estimated via Expectation-Maximization (EM) on accumulated response data.
- **BKT Parameters**: Per-concept transition, guess, and slip rates are updated from observed patterns.
- **Frequency**: Initially manual/on-demand; later automated via scheduled agent at configurable intervals (e.g., weekly).

---

## Architectural Decisions

### AD-001: Single Knowledge Graph for All Subjects

**Decision**: Use a **single Neo4j database** with subject-level partitioning through node labels and a `(:Subject)` hierarchy — NOT separate databases per subject.

**Rationale**:
- **Cross-subject connections**: Concepts like "Statistics" appear in AI, Data Science, and Finance. A single graph allows shared nodes with edges crossing subject boundaries.
- **Infrastructure simplicity**: One Neo4j instance to manage, monitor, and back up.
- **Neo4j 5+ capability**: If isolation is ever needed, Neo4j 5+ supports multiple databases within the same instance — we can split later without changing infrastructure.
- **Ontology readiness**: A unified graph is essential for ontology-based reasoning across domains.

**Partitioning strategy**:
```
(:Subject {name: "Artificial Intelligence"})
  └── (:Topic {name: "LLMs & Prompting"})
       └── (:Concept {name: "Prompt Engineering"})
            └── (:Question {level: "Repeat", ...})
```
Every query scopes by Subject/Topic to maintain performance.

### AD-002: Ontology-Ready Design

**Decision**: Design the knowledge graph schema to be **ontology-compatible from Day 1**, enabling future OWL/RDF integration.

**Approach**:
- Use the **neosemantics (n10s)** Neo4j plugin for future RDF/OWL import/export
- Model concepts with `rdf:type`-compatible labels and properties
- Use typed, named relationships (not generic "RELATED_TO") — e.g., `IS_PREREQUISITE_FOR`, `REQUIRES_CLARITY_ON`
- Maintain a `(:ConceptClass)` meta-layer for ontological classification (e.g., "Technique", "Tool", "Theory", "Framework")
- Future: Import standard ontologies (e.g., ACM Computing Classification System) and map our concepts to them

**Schema readiness**:
```cypher
// Future ontology nodes
(:ConceptClass {uri: "ikas:Technique", label: "Technique"})
(:ConceptClass {uri: "ikas:Tool", label: "Tool"})

// Concepts linked to their ontological class
(:Concept {name: "RAG"})-[:INSTANCE_OF]->(:ConceptClass {label: "Technique"})
(:Concept {name: "LangChain"})-[:INSTANCE_OF]->(:ConceptClass {label: "Framework"})
```

### AD-003: Response Storage for Probability Recalibration

**Decision**: Store **every individual student response** to every question in PostgreSQL for aggregated analysis and probability recalibration.

**Schema**:
```sql
CREATE TABLE responses (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES test_sessions(id),
    user_id UUID REFERENCES users(id),
    question_id VARCHAR(100) NOT NULL,     -- Neo4j question node ID
    question_level VARCHAR(20) NOT NULL,    -- Repeat|Summary|Intuitive|Apply
    user_answer JSONB NOT NULL,             -- Flexible: MCQ selections, free text, links
    is_correct BOOLEAN,
    partial_score FLOAT,                    -- 0.0 to 1.0 for partial credit
    grading_details JSONB,                  -- LLM rubric output, breakdown
    time_taken_seconds INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for aggregation queries
CREATE INDEX idx_responses_question ON responses(question_id);
CREATE INDEX idx_responses_user ON responses(user_id);
CREATE INDEX idx_responses_level ON responses(question_level);
```

**Recalibration agent** (scheduled, runs periodically):
1. Queries `responses` table for all answers to connected question pairs (Q_A, Q_B)
2. Computes empirical `P(Q_B correct | Q_A correct)` and `P(Q_B correct | Q_A incorrect)`
3. Updates edge properties in Neo4j using Bayesian smoothing (blended with prior uniform distribution)
4. Updates IRT item parameters (difficulty, discrimination) via EM algorithm on accumulated data
5. Logs all changes for audit trail

### AD-004: Configurable Test Parameters with Pre-defined Combos

**Decision**: Both test duration and question count are configurable, with system-suggested presets.

**Pre-defined combinations**:

| Preset | Questions | Duration | Best For |
|--------|-----------|----------|----------|
| **Quick Check** | 10 | 15 min | Fast knowledge pulse check on a single level |
| **Standard Assessment** | 25 | 45 min | Balanced assessment across all 4 levels |
| **Comprehensive Exam** | 50 | 90 min | Deep evaluation with thorough level coverage |
| **Custom** | User-defined | User-defined | Full flexibility |

**Level distribution for Standard Assessment**:
- Repeat: ~30% (7-8 questions)
- Summary: ~25% (6-7 questions)
- Intuitive: ~25% (6-7 questions)
- Apply: ~20% (5 questions)

### AD-005: Deployment Strategy (Free/Minimal Cost, No AWS)

**Decision**: Use **Oracle Cloud Infrastructure (OCI) Always Free Tier** for deployment.

**Rationale**:
| Option | Free Tier | Why Chosen/Rejected |
|--------|-----------|-------------------|
| **Oracle Cloud (OCI)** | **2 ARM VMs (4 OCPU, 24GB RAM each), 200GB block storage, 10TB egress** | Exceptionally generous free tier — enough to run Neo4j + PostgreSQL + Flask + React. Truly free indefinitely. |
| GCP | e2-micro (0.25 vCPU, 1GB RAM) | Too small for Neo4j. Would need paid tier quickly. |
| Azure | B1s VM (1 vCPU, 1GB RAM) for 12 months | Time-limited, small for Neo4j. |
| Fly.io | 3 shared-cpu VMs, 256MB each | Too small for Neo4j. |
| Railway | $5/month after trial | Not free. |
| Local Docker | Unlimited | Not accessible to others; good for dev only. |

**Deployment architecture on OCI Free Tier**:
- **VM 1** (ARM, 2 OCPU, 12GB RAM): Neo4j + PostgreSQL
- **VM 2** (ARM, 2 OCPU, 12GB RAM): Flask backend + React (Nginx-served static build)
- **Block Storage**: 100GB for Neo4j data, 50GB for PostgreSQL

**For development**: Docker Compose locally (free, immediate).

### AD-006: User Roles & Grouping

**Decision**: Support three roles and organization-level grouping.

| Role | Capabilities |
|------|-------------|
| **Student** | Take tests, view own results/progress, access recommended resources |
| **Instructor/Admin** | All student capabilities + view cohort progress, configure tests, manage users in their organization |
| **Question Author** | Submit questions for review, view question analytics, manage resources |

**Grouping**: Organizations → Cohorts → Students. An instructor belongs to an organization and can view all cohorts within it.

---

## Conventions & Standards

### Code Style
- **Python**: PEP 8, type hints everywhere, Pydantic v2 for DTOs
- **TypeScript**: Strict mode, ESLint + Prettier
- **Git**: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`)
- **Branching**: `main` (stable), `develop` (integration), `feature/*`, `fix/*`

### API Design
- Base URL: `/api/v1/`
- JSON responses: `{ "success": bool, "data": {...}, "error": string|null, "meta": {...} }`
- Pagination: cursor-based for lists
- Error codes: Standard HTTP + custom error codes in response body

### Neo4j Conventions
- Node IDs: `{type}-{subject_code}-{sequential}` (e.g., `q-ai-001`, `c-ai-llm-001`)
- All nodes have `created_at`, `updated_at` timestamps
- Edge probabilities initialized at 0.5 (uniform prior) until calibrated with data

### Environment Variables
- All secrets in `.env` (git-ignored)
- `.env.example` committed with placeholder values
- Prefixed by service: `NEO4J_`, `PG_`, `JWT_`, `LLM_`, `FLASK_`

---

## First Subject: Artificial Intelligence

### Initial Topic Hierarchy

```
Subject: Artificial Intelligence
├── Topic: LLMs & Prompting
│   ├── Concept: What is an LLM
│   ├── Concept: Tokenization
│   ├── Concept: Prompt Engineering
│   ├── Concept: Few-shot / Zero-shot Learning
│   ├── Concept: Temperature & Sampling
│   └── Concept: Context Windows
├── Topic: AI Agents & Orchestration
│   ├── Concept: What is an AI Agent
│   ├── Concept: Agent vs Skill vs Tool
│   ├── Concept: Autonomous vs Semi-autonomous
│   ├── Concept: Multi-agent Systems
│   ├── Concept: Agent Frameworks (LangChain, CrewAI, etc.)
│   └── Concept: Agent Evaluation & Validation
├── Topic: AI Tools & Frameworks
│   ├── Concept: Popular AI Tools Overview
│   ├── Concept: Model Selection (Text, Image, Code)
│   ├── Concept: API Integration Patterns
│   ├── Concept: MCP Servers
│   └── Concept: Vector Databases
└── Topic: RAG (Retrieval Augmented Generation)
    ├── Concept: What is RAG
    ├── Concept: Embedding Models
    ├── Concept: Chunking Strategies
    ├── Concept: Retrieval Methods
    └── Concept: RAG Evaluation
```

---

## Phase Summary

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 1** | Core adaptive loop: MCQ questions, Bayesian engine, basic UI, reports | Next |
| **Phase 2** | Free-form answers, LLM grading, enhanced UX, image/code submissions | Planned |
| **Phase 3** | Shadow testing, exposure control, probability recalibration agent, multi-subject | Planned |
| **Phase 4** | Agentic orchestration, continuous question generation, Jira integration | Planned |

---

## Session Log

| Date | Session | Key Decisions |
|------|---------|--------------|
| 2026-07-22 | Initial Planning | Architecture designed, tech stack confirmed, 4-phase plan created. Monorepo structure. Neo4j + PostgreSQL dual-DB. Oracle Cloud for deployment. LLM abstraction layer for model switching. Ontology-ready schema. Single knowledge graph with subject partitioning. |
