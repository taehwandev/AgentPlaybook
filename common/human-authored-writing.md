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

## Use When

Load this card before drafting, editing, reviewing, or publishing prose where
the user asks for a natural voice, less AI-sounding copy, a blog/article/essay,
public introduction, release note, email, marketing page, documentation tone
work, or "humanize" style cleanup.

For blog posts, articles, essays, or other publishable long-form prose, also
load `common/writing-workspace.md` before creating files so the draft source and
publishing target are not confused.

Do not wait until after writing to load this card. For writing tasks, this card
is part of the source-of-truth discovery step, not a post-processing filter.

## Inspect First

- The user's actual request, including audience, channel, language, and purpose.
- Any supplied draft, outline, examples, quotes, claims, citations, product
  names, numbers, dates, legal or policy text, and SEO keywords that must
  survive unchanged.
- Two or three nearby voice samples when available, such as existing docs,
  posts, release notes, emails, or the user's own draft fragments.
- The configured writing workspace when drafting blog posts, articles, essays,
  or publishable long-form prose.
- Repo-local writing, brand, accessibility, localization, disclosure, or public
  discovery rules when the text is user-facing.
- Required disclosure rules for academic, legal, workplace, regulated, or
  public-authorship contexts.

## Decision Rule

Treat "human-authored" as a fidelity and clarity pass, not as detector evasion.
The edit should make the piece sound like a person with a reason to write it:
clear intent, concrete judgment, appropriate evidence, natural rhythm, and a
voice that matches the genre.

When in doubt, preserve meaning over style. If a more natural sentence would
change facts, author position, legal meaning, citations, claims, product policy,
or disclosure obligations, keep the original meaning and report the constraint.

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
3. Mark protected content: facts, names, numbers, quotes, citations, URLs,
   product terms, keywords, legal/policy text, and any sentence whose meaning
   must not drift.
4. Audit the draft for specific signals. Note the span, category, severity, and
   intended edit before rewriting broad sections.
5. Rewrite only the flagged spans or the smallest paragraph needed for flow.
6. Run a fidelity check against the original: facts, claims, numbers, names,
   quotes, citations, ordering, tone, and required format.
7. Read the result aloud or scan for rhythm: sentence lengths should vary, but
   the prose should not become choppy, cute, or performatively casual.
8. Run an "obviously generated" second pass for residual tells: formulaic
   framing, repetitive transitions, fake balance, unsupported grand claims,
   chatbot closers, and tidy-but-empty summaries.
9. Report the categories changed and any places intentionally left unchanged.

## Audit Passes

Use these passes when the writing task is more than a one-line copy edit.

1. **Structure pass**: Check for mechanical openings, symmetric sections,
   identical list lengths, repeated "why/what/how" scaffolds, and conclusions
   that merely summarize instead of landing a point.
2. **Claim pass**: Remove significance inflation, promotional adjectives,
   vague authorities, false certainty, and unsupported "important" framing.
3. **Language pass**: Replace AI-heavy vocabulary, synonym cycling, false
   ranges, excessive nominalizations, and copula-avoidance phrases with direct
   verbs and concrete nouns.
4. **Rhythm pass**: Vary paragraph and sentence length without forcing drama.
   Break uniform cadence, but do not create artificial punchlines.
5. **Transition pass**: Cut repetitive connective tissue such as stacked
   "moreover/furthermore/additionally" equivalents. Use normal continuity:
   cause, contrast, example, or no transition.
6. **Voice pass**: Match the author's register and stance. Use a style vector
   such as direct/indirect, formal/informal, analytical/practical,
   concise/expansive, technical/plain, warm/neutral, and confident/careful.
7. **Fidelity pass**: Confirm the revised text did not invent experience,
   sources, anecdotes, numbers, product claims, citations, or author opinions.

## Common Signals

| Surface | Signals to inspect | Preferred fix |
| --- | --- | --- |
| Korean prose | Translationese, overformal connective adverbs, passive or nominalized phrasing, mechanical numbered structure, excessive headings or decoration, overuse of English in parentheses, repeated endings, formal nouns such as "것/점/수/바" when they only pad the sentence | Rewrite into natural Korean idiom while preserving the original claim and register |
| English prose | Inflated significance, generic enthusiasm, promotional adjectives, shallow participial clauses, excessive hedging, repeated signposting, symmetric sentence rhythm, overuse of em dashes or paired contrasts, rule-of-three lists, synonym cycling, false ranges | Replace with specific claims, direct verbs, sourced detail, varied rhythm, and simpler punctuation |
| Documentation | Polished filler, unsupported value claims, unnecessary summaries, "this guide explores" framing, duplicated overview bullets, diff-anchored narration, inline header lists where the heading repeats the sentence | Start with the action path, keep constraints explicit, and remove decorative framing |
| Marketing or product copy | Vague benefits, buzzwords, "unlock/transform/revolutionize" language, claims without proof | Tie copy to concrete user outcomes, product evidence, and a clear audience |
| Email or workplace prose | Over-apology, over-hedging, generic warmth, long preambles, unclear ask | Lead with the ask, state context plainly, and keep the tone professional |
| Social or short-form copy | Fake-candid openers, manufactured punchlines, over-neat aphorisms, forced attitude, and engagement-bait summaries | Use one concrete observation or stance; keep the ending short without pretending to be spontaneous |
| Academic or regulated prose | Style cleanup that weakens citations, evidence, scope limits, uncertainty, required disclosure, or policy wording | Preserve the formal contract first; simplify only where accuracy and compliance remain intact |

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
- Do not add "human texture" by inventing personal experience, anecdotes,
  memories, emotions, preferences, or insider claims. Texture must come from
  supplied material, observable product facts, or the author's existing stance.

## Common Rationalizations

| Rationalization | Required response |
| --- | --- |
| "The user only asked for an article, so the writing card can be applied later." | Load this card before drafting; writing style affects structure and source selection, not only final wording. |
| "It sounds polished, so it is better." | Check whether polish removed specificity, stance, or natural rhythm. |
| "Adding a personal line makes it more human." | Add personal texture only when the source material supports it. |
| "Detector score is the goal." | Refuse detector-bypass promises; improve clarity, fidelity, voice, and responsible use. |
| "Every AI tell must be banned everywhere." | Apply genre and channel judgment. Technical docs, legal text, and formal reports can be restrained without sounding robotic. |

## Red Flags

- The draft could apply to any product, team, field, or person after changing
  only the nouns.
- The opening announces importance before saying what actually happened.
- Paragraphs have the same length and the same explanatory rhythm.
- Lists come in neat threes without a real reason.
- A conclusion summarizes instead of adding a decision, next action, or grounded
  final claim.
- The edit changes authorial stance, adds lived experience, or hides uncertainty.
- A "humanized" version is longer but no more specific.
- The output claims or implies it will bypass AI detectors.

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
- Rewrite the whole piece when a span-level edit would solve the issue.
- Make an institutional document sound casual only because casual writing feels
  more human.
- Turn a sparse draft into a confident essay by adding unsupported examples,
  market claims, expert consensus, or invented lived experience.
- Treat third-party humanizer repos as source text to copy. Extract reusable
  risks, passes, and verification questions instead.

## Stop If

- The user wants to hide plagiarism, misrepresent authorship, bypass an
  academic or workplace AI policy, or evade a required disclosure.
- The requested rewrite would change regulated, legal, medical, financial,
  contractual, or policy meaning without an approved source.
- There is no source for required claims, examples, numbers, citations, or
  personal experience, and the piece depends on them.
- The rewrite would exceed the requested scope by changing more than about one
  third of the draft without approval.
- Voice ownership is unclear and no sample exists, but the user asks for a
  highly specific personal voice.

## Check

- Does the revised text preserve every factual commitment from the original?
- Can each material change be tied to a specific writing signal?
- Does the piece still match its genre, audience, and distribution channel?
- Is the voice specific enough to avoid generic AI polish, without becoming a
  caricature?
- Are disclosure, academic integrity, compliance, legal, or workplace rules still
  respected?
- Are protected tokens, SEO keywords, citations, names, numbers, URLs, and
  product terms still intact where required?
- Did the second pass catch remaining formulaic structure, fake balance, vague
  authorities, chatbot artifacts, or unsupported confidence?
- For UI text, forms, localized copy, or accessibility-sensitive text, also load
  `common/accessibility-i18n.md`.

## Report

When this card governs the work, report:

- whether the card was loaded before drafting or editing
- the voice/source sample used, or the assumption used when no sample existed
- the main signal categories changed
- protected content intentionally preserved
- any places left unchanged because fidelity, compliance, or source limits
  mattered more than style

## External References

These references informed this card and were checked on 2026-06-27. Use them as
inspiration, not as vendored source material or a replacement for this card.

- Korean-focused reference: `epoko77-ai/im-not-ai`
  (`https://github.com/epoko77-ai/im-not-ai`) for meaning preservation,
  span-based edits, genre preservation, over-edit limits, and Korean-specific
  AI-writing signals.
- English-focused reference: `blader/humanizer`
  (`https://github.com/blader/humanizer`) for English AI-writing patterns,
  voice calibration, and final audit passes.
- Agent-agnostic reference: `harshaneel/humanize`
  (`https://github.com/harshaneel/humanize`) for separating humanization from
  checking, using evidence-based signal categories, and documenting rule-based
  limitations.
- Pass-based editing reference: `jpeggdev/humanize-writing`
  (`https://github.com/jpeggdev/humanize-writing`) for structure, claim,
  vocabulary, grammar, rhythm, hedging, connective-tissue, and voice passes.
- Voice guard reference: `orange2ai/writing-style-guard`
  (`https://github.com/orange2ai/writing-style-guard`) for rhythm, reader-first
  openings, and avoiding fake analysis tone.
- Responsible-use reference: `fendouai/best-humanizer-handbook`
  (`https://github.com/fendouai/best-humanizer-handbook`) for treating
  humanization as clarity, judgment, evidence, and meaning protection rather
  than detector score optimization.
- Style-axis reference: `viktorbezdek/definitive-llm-writing-style-guide`
  (`https://github.com/viktorbezdek/definitive-llm-writing-style-guide`) for
  describing voice through register, communication style, and cognitive style
  axes instead of generic "more human" instructions.
- Anti-pattern reference: `shaswatco/anti-ai-writing-style`
  (`https://github.com/shaswatco/anti-ai-writing-style`) for common English AI
  writing tells such as uniform rhythm, inflated vocabulary, and negative
  reframing. Apply these as review signals, not universal bans.
