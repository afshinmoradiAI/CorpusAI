You are writing the Aims and Hypotheses section of an NHMRC grant
application.

Structure:
- Open with a single overarching aim sentence (1 line).
- Then 2–4 specific aims. Each specific aim MUST have:
  1. A verb-led aim sentence (determine, quantify, develop, test,
     characterise — never "investigate," "explore," "study," "examine").
  2. A hypothesis that predicts a specific result with a magnitude.
  3. Tie to a measurable outcome.

Length: 250–400 words.

Reply with ONE JSON object and nothing else:

```json
{ "content": "<aims and hypotheses, formatted as numbered list>" }
```

Format each specific aim as:

```
**Aim N: <verb-led statement of what will be determined>.**
Hypothesis: <prediction with specific effect size or threshold>.
Outcome measure: <named primary outcome, validated instrument or assay>.
```

Rules:
- Every hypothesis predicts a number, a direction, or a binary outcome.
  Vague hypotheses invite reviewers to imagine your study failing.
- Aims must be answerable yes/no or by a measurable quantity.
- Stay consistent with the burden of disease and the synopsis if provided.
- For clinical studies, name the primary outcome and time-point.
- For lab studies, include sex as a biological variable in at least one aim.
- Do not list activities ("we will perform Western blots"). Those go in
  the Methods section.
