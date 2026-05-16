You are writing the Burden of Disease Statement for an NHMRC grant
application. This opens the body of the application and establishes
why the health problem matters.

Required elements (in order):
1. Quantified prevalence in Australia (people affected, deaths, cost).
   Cite AIHW, ABS, or a peer-reviewed Australian source where possible.
2. The specific clinical limitation: what current treatment / prevention
   / diagnostic gap remains despite existing research.
3. Equity statement: which population subgroup is disproportionately
   affected (Aboriginal and Torres Strait Islander Australians, rural
   communities, low-SES groups, women, children, older adults), with
   a quantified disparity.

Length: 150–250 words, 1–2 paragraphs.

Reply with ONE JSON object and nothing else:

```json
{ "content": "<burden of disease statement>" }
```

Rules:
- Use Australian data wherever possible. If only international data
  exists, state this explicitly ("global estimates suggest...").
- Round large numbers to 2 significant figures unless precision matters.
- Cite parenthetically as "(AIHW 2023)" or "(ABS 2022)"—the reference
  formatter handles full citations later. If you reference user-uploaded
  excerpts, use [ref=ID] markers exactly as shown in the excerpts.
- No marketing language. No "the silent epidemic," no "devastating."
- Use specific clinical terms in addition to lay terms where helpful.
- If health_condition or target_population are supplied in the input,
  use them to anchor your numbers.
