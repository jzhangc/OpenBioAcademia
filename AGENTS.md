# OpenBioAcademia — Agent Onboarding

You are working on an open-source research pipeline: a multi-agent swarm that
surveys the literature, generates novel hypotheses, verifies citations, and
produces human-readable academic prose. This AGENTS.md tells AI coding agents
how the repo is laid out and the conventions to keep.

## Quick Start

```bash
pip install -e ".[dev]"          # install with dev deps (pytest, flake8, mock)
python -m pytest tests/ -v      # all tests run offline; network is mocked
flake8 tools/ --max-line-length=100 --ignore=E501,W291
```

The pip entry point is `academica` (defined in `pyproject.toml`):

```bash
academica demo                        # offline pipeline demo, no API keys
academica search "transformer efficiency"   # 4 academic APIs in parallel
academica verify PATH_TO_PAPER.json  # check citations in a paper JSON
academica bibtex 10.1234/xyz        # BibTeX from a DOI
academica configure                 # set API keys interactively
```

## Repository Layout

| Path | What is in it |
|------|---------------|
| `orchestrator/research-director.md` | Primary agent. The conductor that dispatches the others. |
| `subagents/` (8) | Writing-pipeline agents: `literature-scout`, `gap-analyzer`, `methodology-designer`, `data-engineer`, `writer`, `verifier`, `style-auditor`, `formatter`. |
| `novelty-engines/` (6) | `contrarian`, `cross-pollinator`, `assumption-excavator`, `counterfactual-generator`, `paradox-sifter`, `heretic` (crown jewel). |
| `reviewers/` (10) | Adversarial personas: theorist, empiricist, pragmatist, skeptic, historian, methodologist, ethicist, competitor, student, dreamer. All 10 must pass before formatting. |
| `skills/` (17) | Portable `SKILL.md` skills. Each subdirectory holds one skill, e.g. `skills/heretic/SKILL.md`, `skills/skill-academic-humanizer/SKILL.md`. |
| `tools/` | Stdlib-only Python CLI: `literature_client.py` (4-source search), `citation_verifier.py` (verify + BibTeX). |
| `src/openbioacademia/` | The `academica` CLI package: `cli.py`, `configure.py`, `demo.py`. `pyproject.toml` maps `openbioacademia.tools` package-dir to `tools/`. |
| `templates/` | LaTeX venue templates: `arxiv`, `iclr`, `icml`, `nature`, `neurips`. |
| `config/agent-config.json` | Per-agent model + fallback config (provider-agnostic). |
| `data/` | `voice-profile/` (author voice calibration, ships with `sample.txt`). `research-memory.json` (cross-paper memory) is created at runtime by the orchestrator — see `orchestrator/research-director.md`. |
| `examples/siren-paper/` | Reference end-to-end pipeline output (13-page paper). |
| `tests/` | `test_citation_verifier.py`, `test_literature_client.py`, `test_cli.py`, plus `conftest.py`. |
| `launch-kit/` | Launch copy (Reddit, HN, Dev.to, Twitter, newsletter). Not part of the pipeline. |

## Conventions

- **Python tools use stdlib only.** `tools/literature_client.py` and
  `tools/citation_verifier.py` rely on `urllib`, `json`, `xml`, and `re`. No
  third-party imports in the CLI tools.
- **Unit tests never hit the network.** `tests/` mock every HTTP call. A test
  that reaches out to an API is a bug.
- **Agent prompts carry YAML frontmatter:** `mode` (subagent / skill),
  `description`, `skills`, and `permission` blocks.
- **No hardcoded absolute paths in code.** Use relative paths or the
   `OPENBIOACADEMIA_DIR` env var.
- **Em dash is a quality gate.** Generated prose must contain zero em dashes.
  The style auditor enforces this.

## Changing Things

- **Tool changes.** Keep the CLI backward compatible and add a test under
   `tests/`. Run flake8 before committing.
- **Agent prompt changes.** Preserve the JSON output contract described in the
  matching frontmatter and in `examples/`.
- **README is the product.** Frame it cleanly; one-line install, no gatekeeping.
- **Adding a LaTeX venue.** Drop `.tex` / `.sty` / `.cls` files under
   `templates/<venue>/`, then reference it from `subagents/formatter.md`.

## Where to Look for Context

- `CLAUDE.md` holds companion notes (architecture summary + key constraints).
- `docs/guide/installation.md` is the step-by-step install guide.
- `CONTRIBUTING.md` covers contribution flow and good-first-issue tags.
- `README.md` is the public-facing documentation; pipeline numbers live here.
