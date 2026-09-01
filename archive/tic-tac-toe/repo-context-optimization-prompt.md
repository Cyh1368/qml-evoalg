# Prompt: Repository Context Optimization for Agentic Workflows

You are an autonomous coding agent working inside an existing repository. Your task is to reorganize and instrument this repository so that **future agentic sessions are more effective and token-efficient**. You are not changing application behavior. You are building the context infrastructure that lets any future agent (you or a cheaper model) start a session already knowing this codebase, load only what's relevant, and verify its own work.

Work autonomously. Read before you write. Do not modify application source code except where explicitly listed below.

---

## Goal (definition of done)

The repository contains: a lean root `CLAUDE.md` (universal rules only, under ~500 words), a `/docs/context/` folder with one-page topical context files, a set of task-scoped skills in `.claude/skills/`, a self-updating memory/decision log, and verification entry points (test/lint/build commands documented and runnable). A fresh agent session should be able to answer "what is this repo, how do I run it, how do I verify a change, and what has been decided before" by reading fewer than ~3,000 tokens of context files.

**Failure path:** If any step is blocked (e.g., tests cannot run, structure is ambiguous), do not guess. Complete the remaining steps, then produce a `BLOCKERS.md` at repo root listing what was skipped and why. Stop after 3 failed attempts at any single step.

---

## Phase 1 — Audit (read-only)

1. Map the repository: languages, frameworks, package managers, entry points, directory structure, build/test/lint tooling, CI config, existing docs (`README`, `CLAUDE.md`, `CONTRIBUTING`, wikis, `/docs`).
2. Identify the 3–7 major functional areas of the codebase (e.g., API layer, data pipeline, frontend, infra).
3. Identify recurring task types an agent would perform here (inferred from commit history, TODOs, issue templates, scripts).
4. Note redundancy and bloat: duplicated docs, stale docs contradicting code, giant files an agent would waste tokens re-reading.
5. Write findings to a scratch file (do not commit it) before making changes.

## Phase 2 — Root `CLAUDE.md` (universal, always-on rules only)

Create or **trim** the root `CLAUDE.md` to contain only what applies to every task:

- One-paragraph repo purpose.
- How to install deps, run, test, lint, and build (exact commands).
- Coding conventions actually enforced (style, naming, commit format).
- Hard boundaries: files/dirs an agent must never modify (secrets, generated code, vendored deps, migrations already applied).
- Pointer index: one line per context file and skill ("For X, read `docs/context/x.md`" / "Skill: `weekly-report`").
- Instruction to read `docs/context/DECISIONS.md` before proposing architectural changes.

Anything task-specific gets moved OUT of `CLAUDE.md` into a skill or context file. Target under 500 words. If a `CLAUDE.md` over 1,000 words exists, treat it as the primary bloat to fix.

## Phase 3 — Context folder (`docs/context/`)

Create one-page markdown files, each under ~400 words, plain markdown, no fluff:

- `ARCHITECTURE.md` — components, data flow, key abstractions, where things live. Prefer a short text map over prose.
- `CONVENTIONS.md` — patterns to follow with one concrete in-repo example each (error handling, logging, testing style, module layout).
- `GOTCHAS.md` — known footguns: flaky tests, order-dependent setup, misleading names, legacy areas, env quirks.
- `DECISIONS.md` — decision log. Seed it from git history/existing docs where you can infer major decisions. Format: date, decision, why, status. Append-only.
- `TASKS.md` — the common task recipes: "to add an endpoint do X→Y→Z, verify with W". One recipe per recurring task type found in Phase 1.

Rule: if a fact exists in code and is trivially discoverable (a function signature), don't duplicate it. Context files hold what's expensive to rediscover.

## Phase 4 — Skills (`.claude/skills/<name>/SKILL.md`)

For each recurring task type (aim for 2–5 skills, not 20), create a skill folder:

```
---
name: <task-name>
description: Use this skill when the user asks to <trigger phrases>.
---
<Step-by-step instructions, file boundaries, verification command, output format.>
```

Each skill must include: scope (which dirs it may touch), the exact verification command to run when done, and an explicit "stop and report" failure condition. Skills load only when relevant — this is where task-specific detail lives instead of `CLAUDE.md`.

## Phase 5 — Memory

Create `docs/context/MEMORY.md` with a header instruction:

> Agents: when you learn durable facts about this repo (a fix for a recurring problem, a preference stated by the maintainer, a constraint discovered the hard way), append a date-stamped entry under 3 sentences. Never rewrite prior entries.

Add a line in `CLAUDE.md` instructing every session to read `MEMORY.md` and `DECISIONS.md` before starting, and to append to them when appropriate.

## Phase 6 — Verification infrastructure

1. Confirm the documented test/lint/build commands actually run. Fix the *documentation* if wrong; do not fix failing tests unless the failure is caused by your changes.
2. If no single "verify everything" entry point exists, add one (e.g., a `make check`, npm script, or `scripts/verify.sh`) that runs lint + tests, and document it in `CLAUDE.md`.
3. Ensure your own changes pass this verification before finishing.

## Phase 7 — Cleanup and report

1. Delete or archive (to `docs/archive/`) stale docs that contradict the code. Never delete anything ambiguous — archive instead.
2. Do not touch: application source, configs affecting runtime behavior, CI pipelines (beyond adding the verify script if appropriate), secrets, lockfiles.
3. Finish with a summary: files created/moved/archived, the new token cost of a cold-start context load (rough estimate), remaining recommendations, and anything needing human review. Commit in logical chunks with clear messages if the repo uses git; otherwise just report.

---

## Constraints

- Every file you author: concise, plain markdown, one topic per file, no marketing language.
- Optimize for an agent reading with a limited budget: front-load the most-used facts, use pointers instead of duplication.
- Preserve all existing information — move or archive, never silently destroy.
- Ask nothing; make reasonable choices and record them in `DECISIONS.md`.
