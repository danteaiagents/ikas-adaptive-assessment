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


def get_concept_names(concept_ids: List[str]) -> Dict[str, str]:
    """
    Batch-fetch concept display names from Neo4j.
    Returns {concept_id: concept_name} for each id in the input list.
    """
    if not concept_ids:
        return {}
    query = '''
    UNWIND $concept_ids AS cid
    MATCH (c:Concept {id: cid})
    RETURN c.id AS concept_id, c.name AS concept_name
    '''
    with get_neo4j_session() as session:
        result = session.run(query, concept_ids=concept_ids)
        return {r['concept_id']: r['concept_name'] for r in result}


def get_concepts_with_resources(topic_id: str) -> List[Dict[str, Any]]:
    """
    Get all concepts for a topic with their linked resources.
    Returns list of {id, name, resources: [{id, url, title, type, level}]}
    """
    query = '''
    MATCH (t:Topic {id: $topic_id})-[:CONTAINS]->(c:Concept)
    OPTIONAL MATCH (c)-[:LINKED_RESOURCE]->(r:Resource)
    WITH c, collect(DISTINCT {id: r.id, url: r.url, title: r.title, type: r.type, level: r.level}) AS resources
    RETURN c.id AS concept_id, c.name AS concept_name, resources
    ORDER BY c.name
    '''
    with get_neo4j_session() as session:
        result = session.run(query, topic_id=topic_id)
        out = []
        for r in result:
            row = dict(r)
            # Filter out null resource entries
            row['resources'] = [res for res in row.get('resources', []) if res.get('id')]
            out.append(row)
        return out


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


def get_all_topics() -> List[Dict[str, Any]]:
    """
    Return all topics with their question and concept counts.

    Returns list of:
      {id, name, description, subject_id, subject_name,
       question_count, concept_count}
    """
    query = '''
    MATCH (s:Subject)-[:CONTAINS]->(t:Topic)
    OPTIONAL MATCH (t)-[:CONTAINS]->(c:Concept)
    OPTIONAL MATCH (c)-[:CONTAINS]->(q:Question)
    WITH s, t, count(DISTINCT c) AS concept_count, count(DISTINCT q) AS question_count
    RETURN t.id          AS id,
           t.name        AS name,
           t.description AS description,
           s.id          AS subject_id,
           s.name        AS subject_name,
           concept_count,
           question_count
    ORDER BY s.id, t.name
    '''
    with get_neo4j_session() as session:
        result = session.run(query)
        return [dict(r) for r in result]


def get_subject_topics(subject_id: str) -> List[Dict[str, Any]]:
    """
    Return topics under a specific subject with counts.
    Useful for subject-scoped filtering.
    """
    query = '''
    MATCH (s:Subject {id: $subject_id})-[:CONTAINS]->(t:Topic)
    OPTIONAL MATCH (t)-[:CONTAINS]->(c:Concept)
    OPTIONAL MATCH (c)-[:CONTAINS]->(q:Question)
    WITH t, count(DISTINCT c) AS concept_count, count(DISTINCT q) AS question_count
    RETURN t.id          AS id,
           t.name        AS name,
           t.description AS description,
           concept_count,
           question_count
    ORDER BY t.name
    '''
    with get_neo4j_session() as session:
        result = session.run(query, subject_id=subject_id)
        return [dict(r) for r in result]
