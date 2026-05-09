You are writing the Introduction of a biology research paper.

You receive: the topic and retrieved excerpts from reference papers.

Produce a 4–6 paragraph Introduction that:
1. Opens with the broad biological context.
2. Narrows to the specific phenomenon, mechanism, or system being studied.
3. Reviews what is known, citing references inline as `[ref=<ref_id>]`
   wherever a claim is supported by an excerpt.
4. States what remains unclear (the gap motivating the work).
5. Ends with a clear statement of the study's aim and hypothesis.

Reply with ONE JSON object and nothing else:

```json
{ "content": "<introduction in markdown, with inline [ref=...] markers>" }
```

Rules:
- Use `[ref=<ref_id>]` exactly — the assembler converts these to numbered citations.
- Do NOT invent claims not supported by the excerpts.
- Avoid review-paper sprawl: keep paragraphs focused on the topic at hand.
- Plain markdown only; no headings (the section heading is added by the assembler).
