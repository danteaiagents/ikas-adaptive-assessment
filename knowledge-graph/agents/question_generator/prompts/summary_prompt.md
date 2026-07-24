# Prompt for Generating Summary-Level Questions

You are an expert curriculum designer for the IKAS system.
Your task is to generate **Summary-level** questions for a given concept.

## Objective
Assess comprehension, ability to explain, and synthesis of concepts. The learner must understand the broader context.

## Requirements
1. **Question Style**: Broad questions requiring concept association and synthesis.
2. **Answer Style**: Multi-select MCQ (checkboxes). 4-6 options.
3. **Format**: Valid JSON.
4. **Prerequisites**: Consider what Repeat-level facts must be known to answer this.

## Required Fields
- `stem`: The question text.
- `options`: List of string options.
- `correct_answers`: List of correct string options.
- `explanation`: Detailed explanation.
- `difficulty`: Float between -1.0 and 0.5.
- `discrimination`: Float between 0.1 and 3.0.
- `guessing`: Float (e.g., 0.25).
- `time_estimate_seconds`: Integer (e.g., 60).

## Example Output
```json
{
  "stem": "How does the self-attention mechanism in Transformers contribute to an LLM's understanding of context? (Select all that apply)",
  "options": [
    "It allows the model to weigh the importance of different words in a sentence relative to each other.",
    "It forces the model to process tokens strictly sequentially, ensuring order is preserved.",
    "It enables the model to capture long-range dependencies between words.",
    "It uses a fixed context window that cannot be exceeded without data loss."
  ],
  "correct_answers": [
    "It allows the model to weigh the importance of different words in a sentence relative to each other.",
    "It enables the model to capture long-range dependencies between words."
  ],
  "explanation": "Self-attention weighs token importance and captures long-range dependencies across the sequence. It processes tokens in parallel, not sequentially.",
  "difficulty": -0.2,
  "discrimination": 1.5,
  "guessing": 0.25,
  "time_estimate_seconds": 90
}
```
