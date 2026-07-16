---
name: verification-before-completion
version: "0.1.0"
description: Use before claiming any work is done, correct, fixed, or accurate — in this framework that means before asserting a fact about an account, a count, a file's contents, an audit finding, or that a skill/script works. Requires fresh evidence (re-read the file, run the script, check the source, grep the count) before the claim, not confidence. Applies to BD outputs and to framework/meta work alike. Adapted from obra/superpowers verification-before-completion for a research + markdown framework, not just code/tests.
origin: verification-before-completion (obra/superpowers), adapted for the BD framework
---

# Verification Before Completion

## Overview

Claiming something is true or done without checking is dishonesty, not efficiency — and in BD it's worse than in code, because a fabricated fact about a prospect or a wrong number in a report goes out under the BDOwner's name.

**Core principle: evidence before claims, always.**

This framework's work is mostly research and markdown, not compiling code — so "verification" rarely means a test suite. It means going back to the source. The principle is identical; only the proof changes.

## The Iron Law

```
NO CLAIM WITHOUT FRESH EVIDENCE GATHERED IN THIS MESSAGE
```

If you haven't re-checked it *in this message*, you can't assert it.

## The Gate Function

```
BEFORE stating a fact, a count, a finding, or "this is done/correct":

1. IDENTIFY  — what would prove this claim? (the file, the source, the script, the grep)
2. GET IT    — re-read the file / re-run the script / re-fetch the source / count it
3. READ IT   — the actual output, fully, not a remembered version
4. COMPARE   — does the evidence match the claim?
                 NO  → state the real finding, with the evidence
                 YES → state the claim, with the evidence attached
5. ONLY THEN — make the claim
```

Skip a step and you're guessing, not verifying.

## What counts as evidence here

| Claim | Requires | Not sufficient |
|---|---|---|
| A fact about an account/contact | the dossier, CallNote, or a cited source | memory of the conversation |
| "X occurrences / N skills / the file says Y" | an actual grep / re-read of the file | an estimate or earlier glance |
| An audit / review finding | re-reading the specific lines it's about | a subagent's summary taken on trust |
| "This skill/script works" | running it (e.g. `bd validate-card`) and reading the output | "it should work" |
| "The fact checks out" | the source quote + URL (per `docs/decisions.md` Decision 2) | confidence |
| A summary from a subagent | spot-checking it against the underlying file | the subagent said so |

## Red flags — STOP

- "should", "probably", "I'm fairly sure", "seems to"
- Expressing satisfaction before checking ("Great!", "Done!", "Confirmed!")
- About to put a finding in a report or an output without re-reading the source
- Trusting a subagent's summary without spot-checking it
- "Just this once" / "I'm confident" / tired and wanting it finished

## Why this is in the framework

This isn't theoretical. In this project an automated audit shipped a "SPICED is defined wrong" finding that was simply false — SPICED is five dimensions (Situation, Pain, Impact, Critical Event, Decision), and a subagent's letter-count was passed through without re-reading the glossary. One re-read would have caught it. That is exactly the failure this skill exists to prevent: a confident claim, from a plausible source, never checked against ground truth.

Trust is the asset. In BD a wrong fact loses a deal; in the framework a wrong finding sends a refactor the wrong way. Both are avoidable by re-reading before asserting.

## When to apply

Always, before: any factual claim about an account or the repo; any count or quote; any audit/review finding; any "done/correct/works/passing"; committing or presenting an output; trusting a subagent's report.

## Bottom line

Re-read the file. Run the script. Check the source. **Then** make the claim. No shortcuts.

## Composes with

- **bd-skill-evolution** — an unverified claim that slips through is itself a trigger: capture the gap so the framework tightens.
- **improve-framework-architecture** — verify each finding against the files before it enters the report.
