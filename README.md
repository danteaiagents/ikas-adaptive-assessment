# IKAS — Intelligent Knowledge Assessment System

An adaptive assessment platform that evaluates learners across four cognitive knowledge levels (Repeat, Summary, Intuitive Understanding, Apply) using a Neo4j knowledge graph, Bayesian inference engine, and modern React frontend.

## Architecture

- **Backend**: Flask 3.x + Python 3.12 (REST API)
- **Frontend**: React 19 + TypeScript + Vite
- **Knowledge Graph**: Neo4j 5.x (questions, concepts, prerequisites)
- **Relational DB**: PostgreSQL 16 (users, sessions, responses)
- **Adaptive Engine**: IRT (3PL) + BKT + Graph Belief Propagation

## Quick Start

```bash
# Start all services
docker compose up -d

# Backend
cd backend && pip install -r requirements.txt && flask run

# Frontend
cd frontend && npm install && npm run dev
```

## Project Structure

```
├── backend/          # Flask REST API
├── frontend/         # React + TypeScript SPA
├── knowledge-graph/  # Neo4j schema, question generators, seed data
├── docker-compose.yml
└── project.md        # Project reference document
```

## Documentation

- [Project Reference](project.md) — Architecture decisions, conventions, tech stack
