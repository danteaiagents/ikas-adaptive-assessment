#!/usr/bin/env bash
# =============================================================================
# IKAS — Neo4j Knowledge Graph Seeder
# Run after containers are up to load all Cypher seed files into Neo4j.
#
# Usage:
#   ./seed.sh                        # seeds all topics
#   ./seed.sh seed_agents.cypher     # seeds a specific file
# =============================================================================
set -euo pipefail

NEO4J_CONTAINER="${NEO4J_CONTAINER:-ikas-neo4j}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-}"
SCHEMA_DIR="${SCHEMA_DIR:-./knowledge-graph/schema}"

if [ -z "$NEO4J_PASSWORD" ]; then
    echo "ERROR: NEO4J_PASSWORD env var must be set."
    echo "  Export it: export NEO4J_PASSWORD=your_password"
    exit 1
fi

# Helper: run a Cypher file
run_cypher() {
    local file="$1"
    local filename
    filename=$(basename "$file")
    echo "▶ Seeding ${filename}..."
    docker exec -i "${NEO4J_CONTAINER}" \
        cypher-shell -u "${NEO4J_USER}" -p "${NEO4J_PASSWORD}" \
        --file - < "$file"
    echo "  ✅ ${filename} done"
}

# Run specific file if provided, otherwise run all seed files
if [ $# -ge 1 ]; then
    if [ -f "${SCHEMA_DIR}/$1" ]; then
        run_cypher "${SCHEMA_DIR}/$1"
    elif [ -f "$1" ]; then
        run_cypher "$1"
    else
        echo "ERROR: File not found: $1"
        exit 1
    fi
else
    echo "════════════════════════════════════════════════════════"
    echo "  IKAS — Seeding Neo4j Knowledge Graph"
    echo "════════════════════════════════════════════════════════"

    # Wait for Neo4j to be ready
    echo "▶ Waiting for Neo4j to be ready..."
    until docker exec "${NEO4J_CONTAINER}" \
        cypher-shell -u "${NEO4J_USER}" -p "${NEO4J_PASSWORD}" \
        "RETURN 1" &>/dev/null; do
        echo "  Neo4j not ready yet, retrying in 5s..."
        sleep 5
    done
    echo "  ✅ Neo4j is ready"

    # Seed schema constraints first
    if [ -f "${SCHEMA_DIR}/constraints.cypher" ]; then
        run_cypher "${SCHEMA_DIR}/constraints.cypher"
    fi

    # Seed all data files in order
    for seed_file in "${SCHEMA_DIR}"/seed_*.cypher; do
        if [ -f "$seed_file" ]; then
            run_cypher "$seed_file"
        fi
    done

    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  ✅ All seed files loaded!"
    echo ""
    # Verify counts
    echo "▶ Verifying question counts..."
    docker exec -i "${NEO4J_CONTAINER}" \
        cypher-shell -u "${NEO4J_USER}" -p "${NEO4J_PASSWORD}" \
        "MATCH (t:Topic)-[:CONTAINS]->(c:Concept)-[:CONTAINS]->(q:Question)
         RETURN t.id AS topic, count(q) AS questions
         ORDER BY t.id"
    echo "════════════════════════════════════════════════════════"
fi
