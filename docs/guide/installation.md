---
layout: default
title: Installation Guide
---

# Installation Guide

## Python CLI Tools

```bash
git clone https://github.com/jzhangc/OpenBioAcademia.git
cd OpenBioAcademia
pip install -e .

academica demo              # Interactive pipeline demo (no API keys needed)
academica search QUERY      # Search 4 academic APIs in parallel
academica verify FILE       # Verify citations in a paper JSON
academica bibtex DOI        # Generate BibTeX from a DOI
academica configure         # Set up API keys interactively
```

## Agent Skills (Any Agent)

Install via the standard skills CLI:

```bash
npx skills add jzhangc/OpenBioAcademia          # Browse and select
npx skills add jzhangc/OpenBioAcademia -s '*'   # Install all 17
npx skills add argahv/novelty-skills            # Standalone thinking tools
```

Or clone and copy manually:

```bash
git clone https://github.com/jzhangc/OpenBioAcademia
cp -r skills/contrarian ~/.claude/skills/
```

## Full Paper Pipeline (OpenCode)

Works with both OpenCode V1 and V2. The installer renders the agents in the
V1 format by default, which loads on both (V2 auto-translates it). See
[OpenCode V1 vs V2](../opencode-v1-v2.md) for the field mapping and the
native V2 option.

```bash
git clone https://github.com/jzhangc/OpenBioAcademia.git
cd OpenBioAcademia
bash install.sh
```

The installer asks a few questions (platform, Claude/OpenAI subscriptions,
Semantic Scholar API key, LaTeX, voice sample) and then:

1. Installs the `humanizer` and `skill-academic-humanizer` skills into
   `~/.config/opencode/skills/`.
2. Renders the 25 agents into `~/.config/opencode/agents/` with the per-agent
   models from `config/agent-config.json`.
3. Copies the agent config to `~/.config/opencode/agent-config.json` with the
   path placeholders rewritten to your machine.
4. Validates the install (`25 / 25` agents, launcher, CLI).

Select "research-director" from the agent tab and type:
`write a paper about [topic]`

### Choosing the OpenCode format

```bash
bash install.sh --yes                 # V1 format (default): loads on V1 and V2
OC_FORMAT=v2 bash install.sh --yes    # Native V2 format: warning-free on V2
python3 tools/agents.py --check --dest ~/.config/opencode/agents
```

- On OpenCode **V1**: use the default `OC_FORMAT=v1` (the installer warns if
  you combine `OC_FORMAT=v2` with a detected V1 binary).
- On OpenCode **V2**: either format works. `OC_FORMAT=v2` gives the native,
  warning-free `permissions:` array; the V1 render is auto-translated with a
  deprecation note. V2-specific differences (per-agent `skills:` and OMO-only
  permission actions are dropped as comments, `external_directory` is allowed
  by default) are covered in [OpenCode V1 vs V2](../opencode-v1-v2.md).

## Requirements

| Component | Requirement |
|-----------|-------------|
| Python CLI tools | Python 3.10+ |
| Full pipeline | OpenCode V1 or V2 (or compatible agent platform) |
| PDF output | LaTeX (optional: Docker image) |
| Literature search | Semantic Scholar API key (free, recommended) |

## Development

```bash
git clone https://github.com/jzhangc/OpenBioAcademia.git
cd OpenBioAcademia
pip install -e ".[dev]"
python -m pytest tests/ -v
flake8 tools/ --max-line-length=100 --ignore=E501,W291
```

<div class="button-group">
  <a href="https://github.com/jzhangc/OpenBioAcademia" class="btn-primary">GitHub Repository</a>
  <a href="https://github.com/argahv/novelty-skills" class="btn-secondary">Novelty Skills</a>
</div>
