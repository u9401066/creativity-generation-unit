# Creativity Generation Unit (CGU)

> An honest creativity scaffold for LLM agents, shipped as an MCP server (SDK 2) plus a portable Agent Plugin.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![MCP SDK](https://img.shields.io/badge/MCP_SDK-2.x-green.svg)](https://modelcontextprotocol.io/)

🌐 [繁體中文](README.zh-TW.md)

> **v0.8.0 is a breaking rewrite.** The old 24-tool server (`generate_ideas`, `spark_collision`, `deep_think`, …) is gone, with no aliases. See [Migrating from 0.6](#migrating-from-06).

**v0.9.0** adds opt-in inquiry memory and caller-model distillation of creative material. Install sources are pinned to `v0.9.0`; [release notes and packages](https://github.com/u9401066/creativity-generation-unit/releases/tag/v0.9.0).

## Why

An LLM can already brainstorm. What it cannot do alone is the part around brainstorming:

| LLMs are weak at | CGU supplies |
|---|---|
| Noticing the assumptions inside its own question | **Frame objects** and 11 philosophical operators (bracket, negate, re-explicate, genealogize, …) with consent for restricted elements |
| Escaping the typical answer | **Anti-typical divergence**: write the typical set first, then generate away from it |
| Independence between "parallel" ideas | **Fan-out work orders**: each idea is generated in a separate context, not a role-play in one |
| Knowing whether an idea is new | **Measurement with a reference set**: novelty is always relative, reported with method and `reference_size`, or `null` when unmeasured |
| Judging without bias | **Blinded pairwise judging with A/B and B/A order**, Wilson intervals, position-bias reporting |
| Remembering across a long session | **State**: SQLite sessions, frame lineage, idea archive, verdicts, feedback |
| Telling you what it did not do | **Provenance on every result**: engine, degraded flags, warnings, seed, version |

CGU **does not pretend to be creative**. By default (`CGU_PROVIDER=passthrough`) it never calls an LLM: it returns *work orders* for the model you are already using, then validates, stores, measures and fences what comes back. Numbers are produced only by code, and every float travels inside a `Measurement` that names its method.

**No additional local LLM is required.** Default `CGU_EMBEDDING=ngram` also avoids probing Ollama. The calling agent's model performs reasoning, naming, semantic review and creative judgment; that agent may use a local or cloud model. Optional semantic embeddings improve comparisons, not reasoning.

With inquiry memory enabled, a hook can collect user prompts. `cgu_status` reports pending reviews; after 20 prompts by default, the agent uses `cgu_inquiry(organize)` and submits `distill` to store reusable questions, constraints, assumptions, analogies, observations and ideas with source IDs and hashes. `materials` retrieves them across sessions. Storage defaults to `~/.cgu`, shared across clients. Without an active agent, prompts accumulate until the next review. See the [contract](docs/inquiry-memory-design.md).

## Install

Requirements: [`uv`](https://docs.astral.sh/uv/) (for `uvx`), `git`, network access to GitHub on first start. The first start builds the package from git and takes about a minute; later starts are cached.

### GitHub Copilot CLI

```shell
copilot plugin marketplace add u9401066/creativity-generation-unit
copilot plugin install cgu@creativity-generation-unit
```

Verify with `copilot plugin list` and, in a session, ask for `cgu_status`. Installing from a local clone also works: `copilot plugin install ./plugins/cgu` (Copilot CLI marks direct local-path installs as deprecated in favor of marketplaces).

### VS Code (GitHub Copilot) and Codex

**Codex CLI** (verified install and MCP registration on Codex CLI 0.160.0; a full model session was *not* verified because it needs a login):

```shell
codex plugin marketplace add u9401066/creativity-generation-unit
codex plugin add cgu@creativity-generation-unit
codex mcp list    # shows the cgu server
```

**VS Code** implements the same [Agent Plugins 1.0](https://agent-plugins.org) standard (Copilot reads `.github/plugin/marketplace.json`). Add this repository as a plugin marketplace and install `cgu`; menu names vary by client version. **VS Code is not yet verified by us.** Details: [plugins/cgu/README.md](plugins/cgu/README.md).

### Any MCP client (server only, no skills)

```json
{
  "mcpServers": {
    "cgu": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--from", "git+https://github.com/u9401066/creativity-generation-unit@v0.9.0", "cgu-server"],
      "env": { "CGU_PROVIDER": "passthrough" }
    }
  }
}
```

From a clone: `uv sync` then `uv run cgu-server`; `uv run cgu doctor` prints what is available.

## What is inside the plugin

| Skill | Use it when |
|---|---|
| `creative-ideation` | "Help me find ideas", "we are stuck": frame → typical set → operators → diverge → measure → judge → idea cards |
| `frame-audit` | "Are we asking the right question?": hidden assumptions, concept boundaries, criterion genealogy, question-quality gate |
| `maieutic-session` | "Don't give me answers, guide me": the human produces, the AI only asks |
| `idea-triage` | "Compare these ideas": measurement + blinded pairwise judging + idea cards |
| `inquiry-mining` | "What do I keep asking?": themes, framing habits, bridges and reusable creative material from your history |

Copilot also gets four thin agents (`creative-facilitator`, `frame-auditor`, `independent-ideator`, `adversarial-critic`). The plugin does not automatically install hooks; the optional Copilot collector is installed separately by the user.

## The 11 tools

| Tool | Actions | Purpose |
|---|---|---|
| `cgu_status` | | What is available now (provider, embedding `semantic` or not, maturity per tool) |
| `cgu_session` | open, get, list, export, delete | Session lifecycle; `delete` needs `confirm=true` and leaves no residue |
| `cgu_frame` | create, get, operators, operate, commit, doubt | Frame objects, 11 operators, lineage, economy of doubt |
| `cgu_material` | search, add, list | Prior art and fragments; untrusted text is fenced and instruction-like patterns stripped |
| `cgu_diverge` | typical_set, anti_typical, fanout, collide | Work orders for divergence; independence is stated, not assumed |
| `cgu_ideas` | add, list, measure | Idea archive, duplicate detection, novelty / diversity with reference sets |
| `cgu_judge` | plan, record, rank | Pairwise judging in both orders, Wilson intervals, Pareto front |
| `cgu_evolve` | map, next, submit, resolve | Niche map and mutation work orders with A/B order control |
| `cgu_feedback` | record, summary, export, delete | What the human actually did with the ideas |
| `cgu_question_gate` | check, record | Question-quality gate before spending effort |
| `cgu_inquiry` | settings, capture, list, themes, label, mine, related, organize, distill, materials, export, delete | Cross-session inquiry and creative material memory; agent performs semantic review |

Every tool returns `ToolResult{ok, data, work_order, work_orders, provenance, error}`. Domain errors are `ok=false`, never exceptions. Also exposed: 5 resources (`cgu://methods/*`, `cgu://operators`, rubrics, triggers) and 4 prompts for clients without skills. Full contract: [docs/architecture.md](docs/architecture.md).

### Example (medical product development)

> "We are an 8-person startup building a home-care product to cut 30-day readmissions. Not another SpO2 wearable plus app."

With the plugin, a mid-tier model opens a session, writes the 8 typical answers, extracts the shared hidden assumptions (home sensing → alert → someone acts), and rewrites three of them with operators. For example, it negates "the alert is the product" into "the product is who receives the alert, under an SLA". It then fans each rewrite out as an independent idea card with payer vs. user, regulatory class (marked as a guess to confirm with the regulator), required validation and the cheapest MVP. Each card carries its derivation path (typical answer → assumption → operator → frame id).

## Inquiry memory and the optional hook

Recording starts off. The portable path is for the agent to forward selected prompts through `capture`. To collect Copilot CLI prompts continuously, install the pinned CLI, inspect the hook and enable recording:

```shell
uv tool install git+https://github.com/u9401066/creativity-generation-unit@v0.9.0
cgu inquiry install-hook --print
cgu inquiry settings --enable --yes
cgu inquiry install-hook
```

Restart Copilot CLI after installation. The hook records user prompt text, timestamps, channel and the final project-directory name. It does not capture assistant replies or full transcripts. Installing the CLI first keeps the hook command local. Hook payload and installation were tested for Copilot CLI; Codex and VS Code hooks have not been verified.

Ask your agent to organize accumulated material. `cgu_status.inquiry.maintenance` reports `pending` and `due` (20 pending prompts by default; change this through `cgu_inquiry(action=settings, organize_after=...)`). The agent gets a batch with `organize`, interprets it using its own model, and submits `distill` with evidence IDs and stored-text SHA-256 hashes. `materials` retrieves questions, constraints, assumptions, analogies, observations and ideas; `fragments_payload` can be added to an ideation session. Without an active agent, prompts accumulate until the next review.

Manage records with `cgu inquiry settings --disable`, `cgu inquiry settings --exclude PROJECT`, `cgu inquiry export`, `cgu inquiry delete --all --yes`, or `cgu inquiry install-hook --remove`. Removing the hook leaves existing records in place. Deleting a source also deletes material that depends on it. De-identification is best effort; the agent's model and data policies are controlled by your client. Full [contract and limits](docs/inquiry-memory-design.md).

## Upgrading from 0.8

Storage defaults to `~/.cgu` and ignores `PLUGIN_DATA`. For an existing plugin-specific database, stop the server and back it up before moving `cgu.sqlite3` to `~/.cgu`, or set `CGU_DATA_DIR` to the existing directory. There is no automatic move or merge. Ensure all database connections are closed before moving a WAL database. Schema migrations preserve existing sessions.

Default embeddings change from `auto` to `ngram`: similarity is lexical (`semantic=false`) and no model is contacted. Explicit `CGU_EMBEDDING=auto` or `ollama` opts into the configured embedding backend. Embeddings improve comparison; the agent's model still performs reasoning.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `CGU_PROVIDER` | `passthrough` | `passthrough` returns work orders; `ollama` enables optional execute mode for `cgu_diverge` |
| `CGU_DATA_DIR` | `~/.cgu` | SQLite location (`cgu.sqlite3`, WAL); ignores `PLUGIN_DATA` |
| `CGU_EMBEDDING` | `ngram` | No model connection by default; novelty is **lexical** (`semantic=false`). Explicit `auto` / `ollama` enables optional embeddings |
| `CGU_OLLAMA_URL` | `http://localhost:11434` | Do not append `/v1` |
| `CGU_OLLAMA_MODEL` | `qwen2.5:3b` | Execute mode only |
| `CGU_EMBED_MODEL` | `nomic-embed-text` | |
| `CGU_NETWORK` | `on` | `off` disables `cgu_material(search)` (reports `degraded`) |
| `CGU_LOG_LEVEL` | `INFO` | Logs go to stderr only; stdout is reserved for MCP stdio |

## Architecture

```
src/cgu/
├── domain/          pure rules: Measurement, frames, operators, doubt, fence, judge (no I/O)
├── application/     ports (Protocols) + services per tool
├── infrastructure/  SQLite archive, embeddings, retrieval, optional LLM, Settings
└── interfaces/      mcp/ (SDK 2 server, tools, resources, prompts) and cli
```

Dependency direction is enforced by a test (domain imports nothing from other layers, nor `httpx`/`sqlite3`).

## Honest limits

- Novelty is **relative to an explicit reference set**, and with the n-gram fallback it cannot detect a paraphrase.
- Heuristic numbers (priority, diversity, win rate) are **uncalibrated**. LLM judges inherit judge-model bias; order disagreement is reported.
- "Philosophical frame audit improves creativity" and "maieutic mode preserves human originality" are **hypotheses under test**, not conclusions.
- Skill effectiveness depends on the host model following the procedure; mid-tier models can skip steps.
- Creativity is not given an ethics gate here by design; downstream regulation (medical devices, privacy, hospital rules) is surfaced as a *risk field on each idea card*, not as a filter.

## Evidence

<!-- EVIDENCE:START -->
We ran an isolated Copilot CLI experiment (plugin installed for real; mid-tier models `claude-sonnet-5.5` and `gpt-6-luna`; research, medical-product and admin-process tasks; blinded pairwise judging by `gpt-6-sol` and `claude-sonnet-5.5`, both orders). Full write-up: [evals/reports/SUMMARY.md](evals/reports/SUMMARY.md).

**What we can and cannot claim**

- The plugin **does not demonstrably beat plain prompting overall.** Cell-level win rate vs. baseline was 27% (exp1, v1), 25% (exp2, v2) and 50% (exp3, v3: 1 win / 1 loss / 4 ties). Every 95% CI spans 50%, so the honest reading is "indistinguishable", with the point estimate unfavorable for v1 and v2.
- It **reliably changes what answers look like**: strongly preferred on novelty (75–96%) and problem reframing (75–96%) in all three rounds.
- v1 and v2 were disliked on practicality and decidability (17–38%). The judges' own reasons: tool jargon leaking into the answer, and go/no-go thresholds left as "待估". v3 fixed those two things (plain-language output, concrete adjustable thresholds) and moved decidability from ~36% to 79% and practicality from ~19% to 38%, at the cost of a smaller novelty edge. **v3 rests on only 6 cells with unstable judge order agreement.**
- One of our hypotheses was falsified: adding a constraint ledger and feasibility gate (v2) did not recover practicality.
- Cost: about 2–5× the wall time and 4–40× the input tokens (mostly cached).
- Auto-triggering is unreliable: with an unmodified prompt the skill led to substantial CGU tool use in 9 of 12 cells (Sonnet 3/6, luna 6/6).
- LLM judges only, no human calibration, tiny n, and the v2/v3 changes were tuned from judge reasons, so they may partly be tuned to LLM judges. Not a claim about SOTA models.
<!-- EVIDENCE:END -->

## Development

```shell
uv sync --extra dev
uv run pytest
uv run ruff check src tests evals && uv run ruff format --check src tests evals
uv run mypy src
```

On Windows, a running `cgu-server.exe` (for example one started by an editor) locks `.venv`. Use a separate environment: `$env:UV_PROJECT_ENVIRONMENT = "$env:TEMP\cgu-venv"`.

## Documents

| Document | Content |
|---|---|
| [docs/architecture.md](docs/architecture.md) | v0.9.0 contract: 11 tools, types, persistence, SDK 2 notes |
| [docs/inquiry-memory-design.md](docs/inquiry-memory-design.md) | Hook collection, agent review, creative material, evidence and management |
| [docs/critical-review-and-improvement-plan.md](docs/critical-review-and-improvement-plan.md) | 40 defects found in 0.6 and the improvement plan |
| [docs/philosophical-inquiry-and-creativity.md](docs/philosophical-inquiry-and-creativity.md) | Philosophy as meta-inquiry: frames, operators, economy of doubt |
| [docs/program-plan.md](docs/program-plan.md) | Phases, work packages, gates, decisions |
| [evals/README.md](evals/README.md) | Effect-experiment protocol |
| [plugins/cgu/README.md](plugins/cgu/README.md) | Plugin install, portability, privacy |
| [CHANGELOG.md](CHANGELOG.md) | Release notes |

## Migrating from 0.6

| 0.6 | 0.8 |
|---|---|
| `generate_ideas`, `deep_think`, `multi_agent_brainstorm`, `spark_soup_quick` | `cgu_diverge` + your model generates + `cgu_ideas` |
| `spark_collision`, `spark_collision_deep`, `find_connections`, `suggest_bridges` | `cgu_diverge(action=collide)` |
| `spark_soup_*`, `collect_creativity_fragments`, `explore_concept`, `random_concept`, `associative_expansion` | `cgu_material` |
| `check_novelty`, `evaluate_brainstorm_ideas` | `cgu_ideas(action=measure)`, `cgu_judge` |
| `evolve_idea_tool` | `cgu_evolve` |
| `creativity_session_*` | `cgu_session`, `cgu_ideas` |
| `apply_method`, `select_method`, `list_methods`, `brainstorm_protocol`, `get_trigger_words` | `cgu://methods/*` resources, prompts, skills |
| `CGU_LLM_PROVIDER`, `CGU_USE_LLM`, `OLLAMA_BASE_URL` | see [Configuration](#configuration) |

## License

Apache-2.0. Author: u9401066 <u9401066@gap.kmu.edu.tw>.
