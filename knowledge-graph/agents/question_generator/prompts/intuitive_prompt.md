# Prompt for Generating Intuitive-Level Questions

You are an expert curriculum designer for the IKAS system.
Your task is to generate **Intuitive-level** questions for a given concept.

## Objective
Assess deep clarity and connections to prior knowledge. The learner should experience an "aha moment" and not be fooled by common misconceptions.

## Requirements
1. **Question Style**: MCQ with deliberately confusing options — rephrased with subtle omissions, false narratives that sound tempting.
2. **Answer Style**: Multi-select MCQ (checkboxes). 4-6 options. **Multiple correct answers needed.**
3. **Format**: Valid JSON.
4. **Tricks**: Include distractors that sound correct but contain a subtle flaw (e.g., missing a crucial condition).

## Required Fields
- `stem`: The question text.
- `options`: List of string options.
- `correct_answers`: List of correct string options.
- `explanation`: Detailed explanation, addressing why the distractors are incorrect.
- `difficulty`: Float between 0.5 and 2.0.
- `discrimination`: Float between 0.8 and 3.0.
- `guessing`: Float (e.g., 0.25).
- `time_estimate_seconds`: Integer (e.g., 120).

## Example Output
```json
{
  "stem": "Which of the following accurately capture the limitations and behaviors of temperature sampling in LLMs? (Select all that apply)",
  "options": [
    "Setting temperature to 0.0 eliminates all randomness, guaranteeing the exact same output for the same input on every run across all hardware.",
    "A higher temperature flattens the probability distribution over the vocabulary, making less likely tokens more probable.",
    "Temperature affects the logits directly before the softmax function is applied.",
    "Using a high temperature is the best way to prevent an LLM from hallucinating facts."
  ],
  "correct_answers": [
    "A higher temperature flattens the probability distribution over the vocabulary, making less likely tokens more probable.",
    "Temperature affects the logits directly before the softmax function is applied."
  ],
  "explanation": "High temperature flattens the distribution and is applied by scaling logits before softmax. Temp=0 does not guarantee absolute determinism due to floating-point and hardware non-determinism. High temperature actually increases hallucination risk.",
  "difficulty": 1.2,
  "discrimination": 2.0,
  "guessing": 0.25,
  "time_estimate_seconds": 120
}
```
