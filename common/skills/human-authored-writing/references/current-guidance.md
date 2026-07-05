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
- The requested writing mode: explanatory guide, personal stance, build log,
  announcement, tutorial, reference note, retrospective, or another genre. If
  the mode is not explicit and changing it would reshape the draft, ask before
  rewriting.
- Two or three nearby voice samples when available, such as existing docs,
  posts, release notes, emails, or the user's own draft fragments.
- For Korean author voice work, inspect phrase-level habits as well as endings:
  connective frames, concrete maintenance wording, preferred technical nouns,
  translation-like metaphors, and phrases the user explicitly rejected.
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

Do not infer the genre from one surface cue. A user saying they prefer plain
endings such as "I did X" or "X is Y" may be asking for a non-honorific
explanatory style, not a retrospective, diary, marketing story, or first-person
confession. If several valid modes fit, present a small choice set and wait for
the user's selection before rewriting the draft.

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
- For Korean prose, once the author's samples or the draft's own passages
  establish plain declarative endings (`다`, `했다`, `이다`), keep that register
  through the whole piece. Do not drift into honorific explanatory endings
  (`합니다`, `됩니다`, `보입니다`) partway through; an unrequested honorific
  shift is a register change, not a fidelity edit.
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
3. If the user asks for "my style", "not honorific", "less AI-sounding",
   "rewrite this", or similar direction but the genre or point of view is
   unclear, ask a choice-framed style question before broad rewriting. Offer
   concrete modes with consequences, such as plain explanatory, first-person
   technical note, opinion/stance article, or retrospective, and do not continue
   until the selected mode is known or the user explicitly accepts a safe
   default.
4. Mark protected content: facts, names, numbers, quotes, citations, URLs,
   product terms, keywords, legal/policy text, and any sentence whose meaning
   must not drift.
5. Audit the draft for specific signals. Note the span, category, severity, and
   intended edit before rewriting broad sections.
6. For Korean prose, run a phrase-level voice pass. Check not only honorific
   endings, but also plausible phrases that the author would not naturally use,
   such as abstract metaphors, stock AI transitions, or wording the user already
   flagged as unnatural.
7. Rewrite only the flagged spans or the smallest paragraph needed for flow.
8. Run a fidelity check against the original: facts, claims, numbers, names,
   quotes, citations, ordering, tone, and required format.
9. Read the result aloud or scan for rhythm: sentence lengths should vary, but
   the prose should not become choppy, cute, or performatively casual.
10. Run an "obviously generated" second pass for residual tells: formulaic
   framing, repetitive transitions, fake balance, unsupported grand claims,
   chatbot closers, and tidy-but-empty summaries.
11. Report the categories changed and any places intentionally left unchanged.

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
| Korean prose | Translationese, overformal connective adverbs, passive or nominalized phrasing, mechanical numbered structure, excessive headings or decoration, overuse of English in parentheses, repeated endings, an honorific-ending drift (`합니다`/`됩니다`/`보입니다`) away from the author's established plain declarative register (`다`/`했다`/`이다`), formal nouns such as "것/점/수/바" when they only pad the sentence, stock connective frames such as "핵심은", "중요한 점은", "반대로", or "이 글에서는" when the author's style would be more direct, and plausible but non-authorial metaphors such as "금방 갈라진다" when concrete maintenance wording fits better | Rewrite into natural Korean idiom while preserving the original claim and register |
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
| "The user gave first-person or plain-ending examples, so the piece should become a retrospective." | Treat those examples as style evidence only. Ask the user to choose the writing mode before changing genre, point of view, or article structure. |
| "The Korean sentence is grammatical, so it matches the author." | Check whether the phrase belongs to the author's observed wording. Replace plausible but non-authorial phrases with concrete wording from the draft, samples, or user feedback. |
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
- A Korean draft passes honorific-ending checks but still contains generic AI
  frames, translated metaphors, or phrases the user has already rejected.
- The agent labels the target as retrospective, essay, announcement, tutorial,
  or marketing copy when the user only described sentence endings, honorific
  level, or broad "my style" cues.
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
- Convert an article into a retrospective, build log, marketing page, tutorial,
  or opinion piece unless the user explicitly requested that mode or selected it
  from a clarification choice.
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
- The requested voice/style could reasonably produce multiple genres or points
  of view, and the choice would change the outline, opening, or author stance.
  Ask a choice-framed question before rewriting.
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
