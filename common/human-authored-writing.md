---
keyflow_id: sys_human_authored_writing
status: review
type: human-reviewed-needed
---

# Human-Authored Writing

Use when drafting or editing user-facing prose, documentation, release notes,
marketing copy, emails, essays, or other text where the goal is to preserve the
author's meaning and voice while reducing generic AI-writing signals.

This card is for writing quality and voice fidelity. It is not an instruction to
deceive reviewers, bypass AI detectors, evade academic or workplace disclosure
rules, or hide generated text where disclosure is required.

## Core Principles

- Preserve meaning first. Keep facts, claims, numbers, dates, names, direct
  quotes, citations, and technical terms intact unless the user explicitly asks
  to correct them.
- Edit from evidence. Change concrete spans that show a pattern; leave clean
  text alone.
- Preserve genre and audience. Do not turn a report into a personal essay, a
  release note into marketing copy, or a technical explanation into casual
  chatter.
- Prefer the user's voice over a generic "human" voice. Use supplied writing
  samples, nearby repo docs, or the draft's strongest natural passages as the
  style source.
- Keep edits conservative. If a rewrite would change more than roughly one
  third of the text, report the risk and offer a focused pass instead of silently
  replacing the piece.
- Make uncertainty visible. If the draft lacks substance, sources, or a real
  point of view, say that style cleanup cannot fix the underlying gap.

## Workflow

1. Identify the language, audience, genre, and source of truth for the content.
2. If available, inspect two or three paragraphs of the author's own writing for
   sentence rhythm, formality, contractions, transitions, punctuation habits,
   and vocabulary preferences.
3. Audit the draft for specific signals. Note the span, category, severity, and
   intended edit before rewriting broad sections.
4. Rewrite only the flagged spans or the smallest paragraph needed for flow.
5. Run a fidelity check against the original: facts, claims, numbers, names,
   quotes, citations, ordering, tone, and required format.
6. Read the result aloud or scan for rhythm: sentence lengths should vary, but
   the prose should not become choppy, cute, or performatively casual.
7. Report the categories changed and any places intentionally left unchanged.

## Common Signals

| Surface | Signals to inspect | Preferred fix |
| --- | --- | --- |
| Korean prose | Translationese, overformal connective adverbs, passive or nominalized phrasing, mechanical numbered structure, excessive headings or decoration, overuse of English in parentheses | Rewrite into natural Korean idiom while preserving the original claim and register |
| English prose | Inflated significance, generic enthusiasm, promotional adjectives, shallow participial clauses, excessive hedging, repeated signposting, symmetric sentence rhythm, overuse of em dashes or paired contrasts | Replace with specific claims, direct verbs, sourced detail, varied rhythm, and simpler punctuation |
| Documentation | Polished filler, unsupported value claims, unnecessary summaries, "this guide explores" framing, duplicated overview bullets | Start with the action path, keep constraints explicit, and remove decorative framing |
| Marketing or product copy | Vague benefits, buzzwords, "unlock/transform/revolutionize" language, claims without proof | Tie copy to concrete user outcomes, product evidence, and a clear audience |
| Email or workplace prose | Over-apology, over-hedging, generic warmth, long preambles, unclear ask | Lead with the ask, state context plainly, and keep the tone professional |

## Voice Calibration

- Use only samples the user provided or material the repo treats as an approved
  voice source.
- Extract broad traits, not private identity. If asked to imitate a third party,
  use high-level descriptors such as direct, analytical, warm, concise, or
  technical instead of impersonation.
- Keep intentional quirks only when they improve recognizability and clarity.
  Do not preserve typos, unclear phrasing, or inaccessible wording by default.
- If no sample exists, use the draft's purpose and audience as the style target
  and state the assumption.

## Do Not

- Promise that text will pass an AI detector or be "undetectable."
- Add personal anecdotes, citations, sources, numbers, or product claims that
  were not provided.
- Rewrite direct quotes, legal language, regulated claims, or policy text unless
  the task explicitly authorizes that scope.
- Remove nuance only to sound more confident.
- Replace every formal phrase with slang. Human-authored prose can be formal,
  technical, restrained, or institutional.
- Let formatting changes carry the edit. Fewer bullets, headings, emojis, or
  bold phrases can help, but the actual sentences still need to be clear.

## Check

- Does the revised text preserve every factual commitment from the original?
- Can each material change be tied to a specific writing signal?
- Does the piece still match its genre, audience, and distribution channel?
- Is the voice specific enough to avoid generic AI polish, without becoming a
  caricature?
- Are disclosure, academic integrity, compliance, legal, or workplace rules still
  respected?
- For UI text, forms, localized copy, or accessibility-sensitive text, also load
  `common/accessibility-i18n.md`.

## External References

These references informed this card and were checked on 2026-05-30. Use them as
inspiration, not as vendored source material or a replacement for this card.

- Korean-focused reference: `epoko77-ai/im-not-ai`
  (`https://github.com/epoko77-ai/im-not-ai`) for meaning preservation,
  span-based edits, genre preservation, over-edit limits, and Korean-specific
  AI-writing signals.
- English-focused reference: `blader/humanizer`
  (`https://github.com/blader/humanizer`) for English AI-writing patterns,
  voice calibration, and final audit passes.
- Agent-agnostic reference: `harshaneel/humanize`
  (`https://harshaneel.github.io/humanize/`) for separating humanization from
  checking and for documenting rule-based limitations.
