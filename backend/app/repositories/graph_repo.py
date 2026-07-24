"""
Graph Repository — Neo4j queries for graph traversal, prerequisite maps,
and belief propagation data.

Schema relationships:
  (:Question)-[:IS_PREREQUISITE_FOR {p_pass_given_pass, p_pass_given_fail}]->(:Question)
  (:Concept)-[:IS_PREREQUISITE_FOR {p_pass_given_pass, p_pass_given_fail}]->(:Concept)
  (:Topic)-[:CONTAINS]->(:Concept)
"""

from typing import Dict, Any, List
from app.extensions import get_neo4j_session


def get_prerequisite_map(topic_id: str) -> Dict[str, List[str]]:
    """
    Get question-level prerequisite map for a topic.
    Returns {question_id: [prerequisite_question_ids]}
    """
    query = '''
    MATCH (t:Topic {id: $topic_id})-[:CONTAINS]->(c:Concept)-[:CONTAINS]->(q:Question)
    OPTIONAL MATCH (prereq:Question)-[:IS_PREREQUISITE_FOR]->(q)
    RETURN q.id AS question_id, collect(prereq.id) AS prereq_ids
    '''
    with get_neo4j_session() as session:
        result = session.run(query, topic_id=topic_id)
        return {
            r['question_id']: [pid for pid in r['prereq_ids'] if pid is not None]
            for r in result
        }


def get_prerequisite_edges(question_id: str) -> List[Dict[str, Any]]:
    """
    Get outgoing prerequisite edges from a question with conditional probabilities.
    Used for graph belief propagation after answering a question.
    """
    query = '''
    MATCH (q:Question {id: $question_id})-[r:IS_PREREQUISITE_FOR]->(target:Question)
    RETURN q.id AS source, target.id AS dest,
           r.p_pass_given_pass AS p_pass_pass,
           r.p_pass_given_fail AS p_pass_fail
    '''
    with get_neo4j_session() as session:
        result = session.run(query, question_id=question_id)
        return [dict(r) for r in result]


def get_concept_prerequisites(topic_id: str) -> Dict[str, List[str]]:
    """
    Get concept-level prerequisite map for a topic.
    Returns {concept_id: [prerequisite_concept_ids]}
    """
    query = '''
    MATCH (t:Topic {id: $topic_id})-[:CONTAINS]->(c:Concept)
    OPTIONAL MATCH (prereq:Concept)-[:IS_PREREQUISITE_FOR]->(c)
    RETURN c.id AS concept_id, collect(prereq.id) AS prereq_ids
    '''
    with get_neo4j_session() as session:
        result = session.run(query, topic_id=topic_id)
        return {
            r['concept_id']: [pid for pid in r['prereq_ids'] if pid is not None]
            for r in result
        }


def get_concept_ids_for_topic(topic_id: str) -> List[str]:
    """Get all concept IDs for a topic."""
    query = '''
    MATCH (t:Topic {id: $topic_id})-[:CONTAINS]->(c:Concept)
    RETURN c.id AS concept_id
    ORDER BY c.id
    '''
    with get_neo4j_session() as session:
        result = session.run(query, topic_id=topic_id)
        return [r['concept_id'] for r in result]


def update_edge_probability(
    source_id: str,
    target_id: str,
    p_pass_pass: float,
    p_pass_fail: float,
) -> None:
    """Update conditional probabilities on a prerequisite edge (for recalibration)."""
    query = '''
    MATCH (src:Question {id: $source_id})-[r:IS_PREREQUISITE_FOR]->(tgt:Question {id: $target_id})
    SET r.p_pass_given_pass = $p_pass_pass,
        r.p_pass_given_fail = $p_pass_fail
    '''
    with get_neo4j_session() as session:
        session.run(query,
                    source_id=source_id,
                    target_id=target_id,
                    p_pass_pass=p_pass_pass,
                    p_pass_fail=p_pass_fail)
