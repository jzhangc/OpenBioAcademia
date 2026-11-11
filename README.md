<div align="center">

# OpenBioAcademia — The Research Paper Writing Army

**20+ specialized agents. 6 novelty engines. 10 adversarial reviewers. Zero hallucinated citations. Zero AI-isms.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)
[![GitHub Stars](https://img.shields.io/github/stars/jzhangc/OpenBioAcademia?style=social)](https://github.com/jzhangc/OpenBioAcademia)
</div>

Not a writing assistant. Not a chatbot with a LaTeX plugin. A **self-coordinating swarm** of 20+ specialized agents that produces publication-ready research papers with **genuine novelty, zero hallucinated citations, and no detectable AI-written patterns.**

```bash
git clone https://github.com/jzhangc/OpenBioAcademia.git && cd OpenBioAcademia
bash install.sh
# Select "research-director" → "write a paper about [topic]"
```

---

## CLI Tools (No Agent Required)

The Python CLI works standalone — no OpenCode or agent platform needed, and no
dependencies beyond the Python 3.10+ standard library. It can be installed, or run
straight from a checkout via `bin/academica`:

```bash
git clone https://github.com/jzhangc/OpenBioAcademia.git && cd OpenBioAcademia
pip install -e .          # or run bin/academica without installing

academica demo              # Run all five quality gates on a bundled example (offline, no API keys)
academica search QUERY      # Search arXiv, Semantic Scholar, CrossRef and OpenAlex in parallel
academica verify FILE       # Verify citations in a paper JSON, .bib or .tex against 2+ APIs
academica bibtex DOI        # Generate BibTeX from a DOI
academica configure         # Set up API keys in .env
```

The same CLI drives the full paper pipeline. The Research Director agent calls these
commands at each stage, and you can call them yourself:

```bash
academica new "TOPIC" --venue arxiv        # create out/papers/<slug>/ for one paper, prints RUN
academica voice [samples...]               # build data/voice-profile.json from your writing
academica search "QUERY" -o RUN/literature/q1.json   # 4 academic APIs in parallel
academica corpus RUN                       # merge RUN/literature/*.json into a deduplicated corpus
academica novelty RUN                      # rank the six engines' hypotheses -> RUN/novelty/ranked.json
academica refs RUN c0003 c0017 ...         # copy corpus papers to references.json and verify them
academica check RUN STAGE                  # validate a stage's handoff files (literature, gaps, ...)
academica gate verify RUN                  # phase 6: citations + statistics + AI patterns
academica gate reviews RUN                 # phase 7: all 10 reviewers accept?
academica gate style RUN                   # phase 9: em dashes, pattern density, voice
academica status RUN                       # every stage and gate at a glance
academica build RUN                        # phase 10: LaTeX + BibTeX + PDF (refuses unless all gates pass)
```

Every command exits non-zero on failure. Read its output before deciding the next
step. See `orchestrator/research-director.md` for the full 11-phase workflow that
ties these commands together.

---

## Portable Agent Skills (Works with Any Agent)

The novelty engines and reviewer personas are packaged as **standalone agent skills** — drop them into any agent that reads SKILL.md (Claude Code, Codex, Cursor, Gemini CLI, OpenCode, and more):

```bash
git clone https://github.com/jzhangc/OpenBioAcademia.git
# Manual: copy individual skill directories
cp -r skills/contrarian ~/.claude/skills/
# Or use npx (see below)
```

Or install any skill with a single command:

```bash
npx skills add jzhangc/OpenBioAcademia          # Browse and select interactively
npx skills add jzhangc/OpenBioAcademia -s '*'   # Install all 17 skills
npx skills add jzhangc/OpenBioAcademia -s contrarian  # Install one skill
```

Then invoke directly in your agent:

```
/contrarian "The claim: 'Attention is all you need'"
/cross-pollinator "Problem: How to reduce LLM hallucination"
/heretic "Paper: 'Scaling Laws for Neural Language Models'"
```

**6 novelty engines + 10 reviewers + academic humanizer = 17 portable skills**.

> 💡 **Prefer a standalone repo?** The 6 novelty engines and 5 reviewer personas are also available as a dedicated skill pack at **[argahv/novelty-skills](https://github.com/argahv/novelty-skills)** — install via `npx skills add argahv/novelty-skills`.

---

## For Humans

**Strongly recommended: let an LLM agent install this for you.** The setup involves API key configuration, agent deployment across 25 specialized agents, voice profile calibration, and provider selection — humans fat-finger these. An LLM agent reads the full guide and walks every step correctly.

The agent will greet you with `oMoMoMoMo...` and ask **one question at a time**:
1. Which platform? (OpenCode recommended)
2. Do you have oh-my-openagent?
3. Claude subscription? (Pro / Max 20x / None)
4. OpenAI subscription? (Plus / None)
5. Semantic Scholar API key? (free — boosts rate limits)
6. LaTeX for PDF? (or Docker / skip for .tex only)
7. Writing sample for voice calibration? (optional)

Then it installs, configures, and verifies everything automatically.

Paste this prompt into Claude Code, AmpCode, Cursor, or any agent:

```
Install and configure OpenBioAcademia by following the instructions here:
https://raw.githubusercontent.com/jzhangc/OpenBioAcademia/main/docs/guide/installation.md
```

### Manual install — one line, no agent needed

If you prefer to run the installer yourself:

```bash
git clone https://github.com/jzhangc/OpenBioAcademia.git && cd OpenBioAcademia
bash install.sh
```

The installer will ask you the same 6 questions and configure everything automatically. Run with `--yes` to skip all prompts and use defaults:

```bash
bash install.sh --yes
```

---

## Setting Up with OpenCode

The 25 agents (1 orchestrator, 8 subagents, 6 novelty engines, 10 reviewers) are
Markdown files with YAML frontmatter. `tools/agents.py` renders each one for a
target OpenCode config directory, substituting the per-agent model from
`config/agent-config.json` and replacing the `{{...}}` path placeholders
(`{{OPENBIOACADEMIA_DIR}}`, `{{OPENCODE_CONFIG}}`, `{{OPENCODE_DATA}}`) with real
paths. The installer does this for you; the steps below are the manual equivalent.

### Agents and subagents

OpenCode discovers agents from two places. Global agents apply to every project;
project agents apply only inside that project and override globals:

| Scope | Agent files | Config |
|-------|-------------|--------|
| **Global** (all projects) | `~/.config/opencode/agents/<name>.md` | `~/.config/opencode/opencode.json` |
| **Project** (this repo only) | `.opencode/agents/<name>.md` | `.opencode/opencode.json` (or `opencode.json` at the repo root) |

Render the 25 agents into the global location (what `install.sh` does):

```bash
python3 tools/agents.py --dest ~/.config/opencode/agents \
  --opencode-config ~/.config/opencode
python3 tools/agents.py --check --dest ~/.config/opencode/agents   # validate an install
```

To scope them to this repo only, render into a project `.opencode` directory:

```bash
python3 tools/agents.py --dest .opencode/agents --opencode-config .opencode
```

Each rendered file keeps its frontmatter: `mode: primary` for the
`research-director` (the conductor) and `mode: subagent` for the other 24. The
permission block already uses the resolved `{{OPENBIOACADEMIA_DIR}}/bin/academica`
path, so a subagent may only call the `academica` commands it needs.

Select the primary agent with `default_agent` in `opencode.json`:

```jsonc
// .opencode/opencode.json  (project-level) — or ~/.config/opencode/opencode.json (global)
{
  "$schema": "https://opencode.ai/config.json",
  "default_agent": "research-director"
}
```

The installer also copies `config/agent-config.json` to
`~/.config/opencode/agent-config.json`, which holds each agent's model,
`fallback_models`, `variant`, `skills` and `permission`. Edit it to switch
providers; `--model` on `tools/agents.py` overrides every agent at once, and
`--default-model` replaces the default while keeping per-agent customizations.

### Skills

The 17 portable skills live in `skills/<name>/SKILL.md`. They are the same
prompts the agents use, packaged to drop into any agent that reads SKILL.md.
Install them into the global or project skills directory:

```bash
# global
cp -r skills/skill-academic-humanizer ~/.config/opencode/skills/
# or all of them
for d in skills/*/; do cp -r "$d" ~/.config/opencode/skills/; done
# project
cp -r skills/* .opencode/skills/
# any agent platform
npx skills add jzhangc/OpenBioAcademia -s '*'
```

OpenCode finds skills automatically under `~/.config/opencode/skills/` (global)
and `.opencode/skills/` (project), and also from any directories listed in the
`skills` array of `opencode.json`.

### Commands (optional slash commands)

You can expose the pipeline as slash commands in `commands/` (global) or
`.opencode/commands/` (project), or define them inline in `opencode.json`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "commands": {
    "paper": { "description": "Write a paper", "template": "Write a paper about $1 using the research-director." }
  }
}
```

### Precedence

OpenCode merges config from global to project (closest wins), and every
`.opencode` config overrides a direct config at the same level. So a project
`.opencode/opencode.json` can point `default_agent` at `research-director` for
just this repo without touching your global setup.

---

## The Numbers (Not Claims)

| Metric | GPT-4 / NotebookLM | OpenBioAcademia |
|---|---|---|
| Papers surveyed per run | 10-50 | **500+** (5 parallel scouts) |
| Citation hallucination rate | ~30-40% | **0%** (verified against 2+ APIs) |
| Novelty generation | None ("what's the gap?") | **6 engines × 50+ hypotheses** |
| Adversarial review | None | **10 distinct personas** |
| AI-text detection | Post-hoc (chatgpt.com paste) | **Generation-time (41 patterns)** |
| Voice calibration | None | **Learns from your writing samples** |
| Output format | Raw text / Google Doc | **LaTeX PDF with verified BibTeX** |
| Time to first draft | 5-20 min | **30 min - 4 hours** (reviewed) |

**Pipeline stats from our SIREN paper** ([view output](examples/siren-paper/)):
100+ papers surveyed → 6 novelty engines → 50+ hypotheses → 10 adversarial reviewers → 4 revision rounds → **13-page PDF, 26 verified citations, 3 publication-ready figures, 0 AI-pattern violations, 0 em dashes, 0 hallucinated references.**

---

## Quick Start

```bash
# 1. Clone + install
git clone https://github.com/jzhangc/OpenBioAcademia.git
cd OpenBioAcademia
bash install.sh

# 2. Configure API keys (free)
cp .env.example .env
# Add your Semantic Scholar API key + CrossRef email

# 3. Write a paper
# OpenCode → agent tab → select "research-director"
# → type: "write a paper about transformer efficiency"
```

**Prerequisites:** OpenCode (or compatible agent platform), Python 3.10+, LaTeX (optional, for PDF).

**Provider-agnostic** — works with any OpenAI-compatible or Anthropic API. Edit `config/agent-config.json` to switch models:

```json
{
  "agents": {
    "research-director": {
      "model": "anthropic/claude-opus-4",
      "fallback_models": [{"model": "anthropic/claude-sonnet-4"}]
    }
  }
}
```

---

## Architecture

```
                     ┌──────────────────────────────┐
                     │  Research Director            │
                     │  (orchestrator)               │
                     └────────┬─────────────────────┘
                              │
         ┌────────────────────┼─────────────────────────┐
         ▼                    ▼                          ▼
   ┌───────────┐    ┌────────────────┐    ┌──────────────────────┐
   │ Literature│    │ 6 Novelty      │    │ Gap Analyzer         │
   │ Scout ×5  │    │ Engines        │    │ + Methodology        │
   └───────────┘    └────────────────┘    └──────────────────────┘
                              │
         ┌────────────────────┼─────────────────────────┐
         ▼                    ▼                          ▼
   ┌─────────────────────────────────────────────────────────────┐
   │  Parallel Writing Swarm (5 agents + 41 Humanizer patterns)   │
   └──────────────────────────┬──────────────────────────────────┘
                              │
   ┌─────────────────────────────────────────────────────────────┐
   │  Verifier: Citations × Statistics × AI-Pattern Detection    │
   └──────────────────────────┬──────────────────────────────────┘
                              │
   ┌─────────────────────────────────────────────────────────────┐
   │  Adversarial Review: 10 reviewer personas (parallel)        │
   └──────────────────────────┬──────────────────────────────────┘
                              │
   ┌─────────────────────────────────────────────────────────────┐
   │  Style Auditor: Humanizer certification, em dash zero check │
   └──────────────────────────┬──────────────────────────────────┘
                              │
   ┌─────────────────────────────────────────────────────────────┐
   │  Formatter: LaTeX template, BibTeX, figures, PDF            │
   └─────────────────────────────────────────────────────────────┘
```

---

## The Novelty Engines (The Moat)

Six engines that think like no human can:

1. **The Contrarian** — Inverts every well-established claim in the field. Generates 10 counter-hypotheses.
2. **The Cross-Pollinator** — Imports solutions from 15 distant fields (astrodynamics, epidemiology, music theory, immunology, 15th-century shipbuilding...).
3. **The Assumption Excavator** — Finds unstated assumptions and tests what breaks if they're false.
4. **The Counterfactual Generator** — Rewrites the field's history without the most-cited papers.
5. **The Paradox Sifter** — Cross-references every "Limitations" section to find ignored contradictions.
6. **The Heretic** — **Crown jewel.** Generates 50 wild hypotheses from title+abstract alone, scores each against the actual paper, and finds the "haunting idea" — what the paper *should have been*.

---

## The Adversarial Reviewers

Each paper is independently reviewed by 10 distinct personas running in parallel. All 10 must pass before formatting.

| Persona | Focus | Typical Critique |
|---------|-------|-----------------|
| **Theorist** | Formal proofs, mathematical rigor | "Where's the formal proof?" |
| **Empiricist** | Experimental design, baselines | "Your baseline is wrong" |
| **Pragmatist** | Practical applicability | "Does this matter in practice?" |
| **Skeptic** | Default: results are wrong | "Show me error bars" |
| **Historian** | Prior art, citation accuracy | "This was done in 1972" |
| **Methodologist** | Statistical methodology | "Your test assumes normality" |
| **Ethicist** | Societal implications | "What are the downsides?" |
| **Competitor** | Novelty relative to existing work | "Minor mod of our 2023 paper" |
| **Student** | Clarity and accessibility | "I don't understand section 3" |
| **Dreamer** | "What if you went further?" | "You stopped too early" |

---

## Quality Gates (Code-Enforced)

Every paper passes through 5 hard gates. **The gates are code, not opinions** — they
run through the `academica` toolchain and record their result (with a hash of the
draft they ran on) in `RUN/gates.json`. `academica build` refuses to format a draft
unless all five passed on that exact draft. If any gate fails, the paper goes back
to revision.

| Gate | `academica` command | Enforced by | Rule |
|------|---------------------|-------------|------|
| **Citations** | `gate citations RUN` | `tools/citation_verifier.py` | Every cited reference found in 2+ APIs. No exceptions. |
| **Statistics** | `gate statistics RUN` | `tools/stats_audit.py` | Recomputes p from t/F/chi/z/r; flags p-hacking, multiple-comparison errors, impossible values. |
| **Patterns** | `gate patterns RUN` | `tools/patterns.py` | 41 Humanizer patterns; density < 2 per 1000 words and zero em dashes. |
| **Style** | `gate style RUN` | `tools/patterns.py` + `tools/voice.py` | Zero em dashes, density < 1/2000 words, voice matches the author profile. |
| **Reviews** | `gate reviews RUN` | `tools/reviews.py` | All 10 reviewer personas accept (score ≥ 6, no must-fix items). |

Convenience groupings: `gate verify RUN` runs the first three (phase 6);
`gate all RUN` runs all five. `gate <name> <file>` runs any single gate on a
`.tex`, `.bib` or JSON file directly.

---

## Live Example: SIREN Paper

The pipeline was run to produce a full paper on **Intent-Based Blockchain Execution via Agentic RAG and Swarm Consensus**. Complete output in [`examples/siren-paper/`](examples/siren-paper/):

| File | Description |
|------|-------------|
| `siren-paper.pdf` | 13-page compiled paper |
| `siren-paper.tex` | LaTeX source (504 lines, 26 references) |
| `figures/*.pdf` | 3 publication-ready figures |
| `README.md` | Pipeline summary with review scores |

**Review scores progressed from Avg 4.6/10 → 8/10 across 4 revision rounds.**

---

## FAQ

**Q: Does this require a specific LLM provider?**  
No. Edit `config/agent-config.json` to use any OpenAI-compatible or Anthropic API.

**Q: Can I add my own LaTeX template?**  
Yes. Add a folder under `templates/` with `.tex`, `.sty`, and `.cls` files, then update `subagents/formatter.md`.

**Q: How long does a paper take?**  
30 minutes to 4 hours depending on LLM speed, literature volume, and revision rounds.

**Q: The output sounds too AI-like. What do I do?**  
Provide 2-3 paragraphs of your published writing in `data/voice-profile/`. The writers will match your voice at the sentence level.

**Q: Can I use this without OpenCode?**  
The agents are OpenCode-compatible, but the Python CLI toolchain (`tools/`) works standalone — run `bin/academica` or `pip install -e .` and use `academica` with no agent platform and no dependencies beyond the Python 3.10+ standard library.

**Q: How do I contribute?**  
See [CONTRIBUTING.md](CONTRIBUTING.md). Good first issues are tagged. Template stubs need filling, the PyPI package needs publishing, and more reviewer personas are welcome.

---

## Directory Structure

```
OpenBioAcademia/
├── orchestrator/          # Research Director agent (the conductor)
├── subagents/             # 8 core writing pipeline agents (writer, verifier, etc.)
├── novelty-engines/       # 6 novelty generation agents
├── reviewers/             # 10 adversarial reviewer personas
├── skills/                # 17 portable skill files (also available as standalone [novelty-skills](https://github.com/argahv/novelty-skills) repo)
├── tools/                 # Python CLI toolchain (stdlib only, 14 modules)
│   ├── literature_client.py   # Multi-source lit search (arXiv, S2, CrossRef, OpenAlex)
│   ├── citation_verifier.py   # Citation verification + BibTeX
│   ├── gates.py               # The 5 code-enforced quality gates
│   ├── stats_audit.py         # Statistical audit (p-value recomputation, CIs)
│   ├── patterns.py            # 41 Humanizer AI-pattern detector + em dash count
│   ├── reviews.py             # 10-reviewer adversarial gate
│   ├── voice.py               # Author voice calibration
│   ├── novelty.py             # Merges and ranks the 6 engines' hypotheses
│   ├── workspace.py           # Run workspace + stage handoff contracts
│   ├── agents.py              # Renders the 25 agents into an OpenCode config dir
│   ├── build.py               # Formatter: LaTeX + BibTeX + PDF
│   ├── settings.py            # .env loading + path resolution
│   ├── net.py / textutil.py   # HTTP retry helper + LaTeX-to-text
├── bin/academica          # Zero-install launcher for the CLI
├── templates/             # LaTeX venue templates (arxiv, neurips, icml, iclr, nature)
├── config/                # Agent configuration (agent-config.json)
├── examples/siren-paper/  # Full pipeline output (13-page paper)
├── data/                  # Research memory + voice profiles
├── tests/                 # Python unit tests (offline)
├── docs/                  # GitHub Pages documentation
├── docker-compose.yml     # LaTeX + dev environments
└── pyproject.toml         # Package metadata
```

---

## Development

```bash
pip install -e ".[dev]"       # pytest, pytest-mock, flake8, requests, pre-commit
python -m pytest tests/ -v    # all tests run offline; network is mocked
flake8 tools/ --max-line-length=100 --ignore=E501,W291

# Render the 25 agents into an OpenCode config dir
python3 tools/agents.py --dest ~/.config/opencode/agents
python3 tools/agents.py --check --dest ~/.config/opencode/agents

# LaTeX via Docker
docker compose --profile latex run latex pdflatex out/papers/paper.tex
```

---

## Acknowledgments

- **[Humanizer](https://github.com/blader/humanizer)** by blader — the 30-pattern AI-detection skill this system builds on
- **[Novelty Skills](https://github.com/argahv/novelty-skills)** — standalone thinking tools for AI agents (separate repo)
- **[OpenCode](https://opencode.ai/)** + **[OhMyOpenAgent](https://omo.dev/)** — agent orchestration platform
- All six novelty engines were inspired by cognitive diversity research

---

## License

MIT — see [LICENSE](LICENSE) for details.

⭐ **Star this repo if you write research papers — it helps others find it.**
