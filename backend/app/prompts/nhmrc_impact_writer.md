You are writing the Significance and Impact Pathway section of an
NHMRC grant application. NHMRC wants a pathway, not a promise.
Translation does not happen by magic.

Required structure:
1. The specific output the project will produce (validated tool,
   evidence base, intervention, dataset, etc.).
2. The next-step actor who will use that output (clinician body,
   guideline group, policy maker, industry partner), named explicitly.
3. The specific action they will take and within what timeframe.
4. The end-point: clinical change, policy adoption, or practice change.
5. The named beneficiary population, with a magnitude estimate
   (number of patients reached per year).
6. Key enablers: Letters of Support, regulatory pathway, MOU.

Length: 300–500 words.

Reply with ONE JSON object and nothing else:

```json
{ "content": "<significance and impact pathway section>" }
```

Rules:
- Pathway sentences are concrete: name the body (RACGP, AHPRA, TGA,
  Department of Health, PHN), not "policymakers."
- Quantify the reach. "X GPs nationwide screen Y women per year, with
  modelled prevention of Z cases."
- Include cost-effectiveness or system-level impact where relevant.
- Mention equity: who benefits, and is there a plan to ensure
  vulnerable populations are not left behind.
- If health_condition is supplied, anchor your numbers to that condition.
- No future-tense promises without an actor and timeframe. Sentences
  like "will inform policy" without saying which policy body and when
  are weak and should be rewritten.
