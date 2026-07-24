// Uniqueness constraints
CREATE CONSTRAINT subject_id IF NOT EXISTS FOR (s:Subject) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT question_id IF NOT EXISTS FOR (q:Question) REQUIRE q.id IS UNIQUE;
CREATE CONSTRAINT resource_id IF NOT EXISTS FOR (r:Resource) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT conceptclass_id IF NOT EXISTS FOR (cc:ConceptClass) REQUIRE cc.id IS UNIQUE;

// Performance indexes
CREATE INDEX question_level IF NOT EXISTS FOR (q:Question) ON (q.level);
CREATE INDEX question_difficulty IF NOT EXISTS FOR (q:Question) ON (q.difficulty);
CREATE INDEX subject_name IF NOT EXISTS FOR (s:Subject) ON (s.name);
