// Repair: Create NN Concepts (if missing) and CONTAINS links
// Ensure topic exists
MERGE (t:Topic {id: "t-ai-neural-networks"}) ON CREATE SET t.name = "Neural Networks & Deep Learning";
MATCH (s:Subject {id: "s-ai"}), (t:Topic {id: "t-ai-neural-networks"}) MERGE (s)-[:CONTAINS]->(t);

MERGE (c:Concept {id: "c-ai-nn-001"}) ON CREATE SET c.name = "Perceptrons & Activation Functions";
MERGE (c:Concept {id: "c-ai-nn-002"}) ON CREATE SET c.name = "Backpropagation & Gradient Descent";
MERGE (c:Concept {id: "c-ai-nn-003"}) ON CREATE SET c.name = "Convolutional Neural Networks (CNNs)";
MERGE (c:Concept {id: "c-ai-nn-004"}) ON CREATE SET c.name = "Recurrent Networks & LSTMs";
MERGE (c:Concept {id: "c-ai-nn-005"}) ON CREATE SET c.name = "Transformer Architecture";
MERGE (c:Concept {id: "c-ai-nn-006"}) ON CREATE SET c.name = "Transfer Learning & Fine-tuning";

// Link concepts to topic
MATCH (t:Topic {id: "t-ai-neural-networks"}), (c:Concept) WHERE c.id STARTS WITH 'c-ai-nn-' MERGE (t)-[:CONTAINS]->(c);

// Create CONTAINS links from Concepts to Questions
MATCH (c:Concept {id: "c-ai-nn-001"}), (q:Question) WHERE q.id IN ["q-ai-nn-001", "q-ai-nn-002", "q-ai-nn-003", "q-ai-nn-004", "q-ai-nn-005", "q-ai-nn-006", "q-ai-nn-007", "q-ai-nn-008"] MERGE (c)-[:CONTAINS]->(q);
MATCH (c:Concept {id: "c-ai-nn-002"}), (q:Question) WHERE q.id IN ["q-ai-nn-009", "q-ai-nn-010", "q-ai-nn-011", "q-ai-nn-012", "q-ai-nn-013", "q-ai-nn-014", "q-ai-nn-015", "q-ai-nn-016"] MERGE (c)-[:CONTAINS]->(q);
MATCH (c:Concept {id: "c-ai-nn-003"}), (q:Question) WHERE q.id IN ["q-ai-nn-017", "q-ai-nn-018", "q-ai-nn-019", "q-ai-nn-020", "q-ai-nn-021", "q-ai-nn-022", "q-ai-nn-023", "q-ai-nn-024"] MERGE (c)-[:CONTAINS]->(q);
MATCH (c:Concept {id: "c-ai-nn-004"}), (q:Question) WHERE q.id IN ["q-ai-nn-025", "q-ai-nn-026", "q-ai-nn-027", "q-ai-nn-028", "q-ai-nn-029", "q-ai-nn-030", "q-ai-nn-031", "q-ai-nn-032"] MERGE (c)-[:CONTAINS]->(q);
MATCH (c:Concept {id: "c-ai-nn-005"}), (q:Question) WHERE q.id IN ["q-ai-nn-033", "q-ai-nn-034", "q-ai-nn-035", "q-ai-nn-036", "q-ai-nn-037", "q-ai-nn-038", "q-ai-nn-039", "q-ai-nn-040"] MERGE (c)-[:CONTAINS]->(q);
MATCH (c:Concept {id: "c-ai-nn-006"}), (q:Question) WHERE q.id IN ["q-ai-nn-041", "q-ai-nn-042", "q-ai-nn-043", "q-ai-nn-044", "q-ai-nn-045", "q-ai-nn-046", "q-ai-nn-047", "q-ai-nn-048", "q-ai-nn-048", "q-ai-nn-049", "q-ai-nn-050"] MERGE (c)-[:CONTAINS]->(q);
