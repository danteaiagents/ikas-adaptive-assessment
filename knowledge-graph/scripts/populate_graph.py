"""
IKAS Knowledge Graph Population Script

Connects to Neo4j and executes the schema constraints and seed data Cypher files.
Run this after starting Neo4j via docker-compose.

Usage:
    python populate_graph.py [--neo4j-uri bolt://localhost:7687] [--neo4j-user neo4j] [--neo4j-password ikas_dev_password]
"""

import os
import sys
import argparse
import re
from neo4j import GraphDatabase


def load_cypher_statements(filepath: str) -> list[str]:
    """
    Load and parse Cypher statements from a .cypher file.
    
    Handles multi-line statements separated by semicolons.
    Strips comments (lines starting with //).
    """
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Remove single-line comments
    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
    
    # Split on semicolons
    statements = [s.strip() for s in content.split(';') if s.strip()]
    
    return statements


def execute_cypher_file(driver, filepath: str, database: str = 'neo4j') -> int:
    """Execute all Cypher statements from a file. Returns count of executed statements."""
    statements = load_cypher_statements(filepath)
    count = 0
    errors = 0
    
    with driver.session(database=database) as session:
        for i, stmt in enumerate(statements, 1):
            try:
                session.run(stmt)
                count += 1
                if count % 10 == 0:
                    print(f"  ... executed {count}/{len(statements)} statements")
            except Exception as e:
                errors += 1
                print(f"  [ERROR] Statement {i}: {str(e)[:200]}")
                print(f"  Statement: {stmt[:100]}...")
    
    return count, errors


def main():
    parser = argparse.ArgumentParser(description='Populate IKAS Neo4j knowledge graph')
    parser.add_argument('--neo4j-uri', default=os.environ.get('NEO4J_URI', 'bolt://localhost:7687'))
    parser.add_argument('--neo4j-user', default=os.environ.get('NEO4J_USER', 'neo4j'))
    parser.add_argument('--neo4j-password', default=os.environ.get('NEO4J_PASSWORD', 'ikas_dev_password'))
    parser.add_argument('--database', default=os.environ.get('NEO4J_DATABASE', 'neo4j'))
    parser.add_argument('--clean', action='store_true', help='Delete all existing data before populating')
    args = parser.parse_args()

    # Resolve file paths relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_dir = os.path.join(script_dir, '..', 'schema')
    
    constraints_file = os.path.join(schema_dir, 'constraints.cypher')
    seed_data_file = os.path.join(schema_dir, 'seed_data.cypher')

    # Verify files exist
    for f in [constraints_file, seed_data_file]:
        if not os.path.exists(f):
            print(f"[ERROR] File not found: {f}")
            sys.exit(1)

    print(f"Connecting to Neo4j at {args.neo4j_uri}...")
    driver = GraphDatabase.driver(args.neo4j_uri, auth=(args.neo4j_user, args.neo4j_password))
    
    try:
        # Verify connectivity
        driver.verify_connectivity()
        print("Connected successfully!\n")

        if args.clean:
            print("Cleaning existing data...")
            with driver.session(database=args.database) as session:
                result = session.run("MATCH (n) DETACH DELETE n")
                print(f"  Deleted all nodes and relationships.\n")

        # Step 1: Execute constraints
        print(f"Step 1: Applying constraints from {os.path.basename(constraints_file)}...")
        count, errors = execute_cypher_file(driver, constraints_file, args.database)
        print(f"  Completed: {count} statements executed, {errors} errors.\n")

        # Step 2: Execute seed data
        print(f"Step 2: Loading seed data from {os.path.basename(seed_data_file)}...")
        count, errors = execute_cypher_file(driver, seed_data_file, args.database)
        print(f"  Completed: {count} statements executed, {errors} errors.\n")

        # Step 3: Print summary
        print("Step 3: Verifying graph contents...")
        with driver.session(database=args.database) as session:
            counts = {}
            for label in ['Subject', 'Topic', 'Concept', 'ConceptClass', 'Question', 'Resource']:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as c")
                counts[label] = result.single()['c']
            
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as c").single()['c']
        
        print("\n" + "=" * 50)
        print("  IKAS Knowledge Graph Summary")
        print("=" * 50)
        for label, count in counts.items():
            print(f"  {label:15s}: {count:4d} nodes")
        print(f"  {'Relationships':15s}: {rel_count:4d} edges")
        print("=" * 50)
        print("\nGraph population complete!")

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        sys.exit(1)
    finally:
        driver.close()


if __name__ == '__main__':
    main()
