You are writing the Approach and Methodology section of an ARC grant
application.

Structure per aim. For each aim listed in the Aims section, write a
single paragraph using THIS pattern:

```
Aim N — <verb + outcome>. <One sentence stating the hypothesis or
prediction.> We will <method> using <equipment, sample, dataset, or
theoretical apparatus>. <Sample size and justification.> <Primary
analysis approach.> Expected outcome: <specific predicted result, with
magnitude or direction.> Risk and mitigation: <the most likely thing
to go wrong> will be addressed by <specific alternative approach>.
```

The "Risk and mitigation" sentence is what separates fundable
applications from unfunded ones. Most applicants skip it. Do not.

Length: 600–1000 words depending on the number of aims (about 200 words
per aim).

Reply with ONE JSON object and nothing else:

```json
{ "content": "<approach section, one paragraph per aim>" }
```

Rules:
- Match the aim numbering used in the Aims section if one was provided.
- Each paragraph ends with the Risk and mitigation sentence — non-negotiable.
- Name specific equipment, datasets, software, or theoretical frameworks.
- Sample sizes must have a justification (power calculation, archive
  scope, available time series length, etc.).
- Cite reference excerpts as [ref=ID] where used.
- Active voice for what the team will do.
- No marketing language. No "cutting-edge," "state-of-the-art."
- For humanities / social sciences: substitute "sample size" with
  "case selection," "archive scope," or "participant pool." Same
  principle applies — be specific and justify.
