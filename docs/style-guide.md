# Style Guide

This guide covers writing conventions for the SpaceRisk Radar documentation. Follow it whenever you add or edit a page.

---

## Voice and tone

- Use **"you"** to address the reader. Not "the user" or "users".
- Write short sentences. One idea per sentence.
- Use active voice. *"The server propagates up to 2,000 objects per cycle"* not *"objects are propagated by the server"*.
- Define every technical term the first time it appears on a page, or link to [Concepts](concepts.md).
- Be specific. Say *"the backend clamps threshold values to 10–5000 km"* not *"the threshold has limits"*.
- Prefer plain English over jargon. *"close approach"* instead of *"conjunction event"* in user-facing text (but keep the precise term in technical pages).

---

## Terminology list

Use these exact names consistently. Do not abbreviate unless the abbreviation has been defined.

| Term | Use this | Not this |
|---|---|---|
| The project | SpaceRisk Radar | SpaceRisk-Radar, SRR, the app (except informally) |
| Orbital element set | TLE | tle, TLEs (plural is fine) |
| Propagation model | SGP4 | sgp4, SGP-4 |
| A close approach | conjunction | Conjunction Event, near-miss |
| The metric | collision probability | Pc (do not use Pc unless you define it first) |
| Ground stations | use the exact name from the code | do not call them "radar stations" |
| Probability of collision | heuristic score | operationally-certified Pc |
| The synthetic test object | TEST_DEBRIS_X | simulated debris, test debris |

---

## Do not invent numbers

If a threshold, count, or probability appears in the documentation, it must be traceable to a line of code or an external reference. If you cannot verify a number, write `TODO(author): <question>`.

---

## Headings

- Use sentence case for all headings: *"How it works"* not *"How It Works"* (MkDocs Material renders the nav from headings, so consistency matters).
- One `#` (H1) per page — the page title only.
- Use `##` for top-level sections and `###` for sub-sections.
- Do not skip levels (do not go from `##` to `####`).

---

## Screenshot captions

Every screenshot must have:

1. Descriptive alt text inside `![...]`. Describe what is visible, not just the feature name.
2. A caption immediately below the image (a line of italic text starting with `*`).

**Good example:**

```markdown
![Dashboard showing a globe with coloured dots for LEO satellites and a conjunction alert panel on the right](assets/SpaceRisk-Rader4.png)
*Conjunction alert panel showing a HIGH-risk event between ISS and TEST_DEBRIS_X.*
```

**Bad example:**

```markdown
![screenshot](assets/SpaceRisk-Rader4.png)
```

---

## Code blocks

- Always specify the language: ` ```bash `, ` ```json `, ` ```python `.
- Show the full command the reader must type, including the prompt character where it helps.
- Do not truncate responses — if a JSON response is long, trim it with `// ...` comments.

---

## Admonitions

Use sparingly. The available types are `note`, `tip`, `warning`, `danger`.

- `!!! note` — background context the reader should know.
- `!!! tip` — a helpful shortcut or best practice.
- `!!! warning` — something that might trip you up.
- `!!! danger` — could cause data loss or a security issue.

Do not use admonitions for every paragraph — they lose impact when overused.

---

## Running the docs site

```bash
pip install -r docs-requirements.txt
mkdocs serve        # live-reload dev server on http://127.0.0.1:8000
mkdocs build --strict   # build static site; fails on any warning or broken link
```

The `--strict` flag is mandatory in CI. Every broken link or missing image is a build failure.
