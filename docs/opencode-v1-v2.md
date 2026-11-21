---
layout: default
title: OpenCode V1 vs V2
---

# OpenCode V1 vs V2

## TL;DR

`tools/agents.py` renders the 25 agents in one of two frontmatter formats. The
default (`v1`) produces the OpenCode V1 `permission:` block, which OpenCode V2
auto-translates, so a V1 render works on both V1 and V2 installs. The `v2`
option produces the native OpenCode V2 `permissions:` array, which loads
warning-free on V2.

- **`--format v1` (default):** `permission:` block. Works on V1 and V2; V2
  prints deprecation warnings while translating.
- **`--format v2`:** native `permissions:` array. Warning-free on V2; not meant
  for V1.

## What changed between V1 and V2

OpenCode V2 replaced the V1 `permission:` block with an ordered `permissions:`
array, and renamed several permission actions:

| V1 | V2 | Note |
|----|----|------|
| `permission:` (block) | `permissions:` (ordered array) | The last matching rule wins: broad rules first, exceptions after |
| `bash` | `shell` | Renamed |
| `task` | `subagent` | Renamed |
| `write`, `patch` | `edit` | Both renamed to `edit` |
| `read`, `webfetch`, `glob`, `grep`, `skill`, `question` | unchanged | Same names in V2 |
| `external_directory` (asks) | allowed by default | V1 asked before leaving the project; V2 allows by default |
| `call_omo_agent`, `doom_loop`, `plan_enter`, `plan_exit`, `repo_clone`, `repo_overview` | omitted | OMO-only keys, not V2 Core permission actions; dropped as comments in v2 output |

Per-agent `skills:` is a V1 field. Global and project skills (under
`~/.config/opencode/skills/` and `.opencode/skills/`) still work in both V1 and
V2 without change.

## Rendering agents

`tools/agents.py` takes `--format {v1,v2}` (default `v1`). The commands below
render into the global agents directory; `--opencode-config` sets the base path
for the `{{OPENCODE_CONFIG}}` placeholder.

```bash
# V1 (default): auto-translated by OpenCode V2
python3 tools/agents.py --format v1 --dest ~/.config/opencode/agents \
  --opencode-config ~/.config/opencode

# V2 (native, warning-free)
python3 tools/agents.py --format v2 --dest ~/.config/opencode/agents \
  --opencode-config ~/.config/opencode
```

Here is the Writer agent's frontmatter before and after the conversion. The
`permission:` block is the V1 source in `subagents/writer.md`; the `permissions:`
array is the V2 render.

### Before: V1 `permission:` block

```yaml
mode: subagent
description: "Paper section writer. Works from a shared outline, cites only verified references, ..."
skills:
  - humanizer
  - skill-academic-humanizer
permission:
  "*": deny
  read:
    "*": allow
  write:
    "{{OPENBIOACADEMIA_DIR}}/out/papers/*": allow
  bash:
    "*": deny
    "{{OPENBIOACADEMIA_DIR}}/bin/academica gate *": allow
    "{{OPENBIOACADEMIA_DIR}}/bin/academica check *": allow
  webfetch: deny
  task: deny
  call_omo_agent: deny
```

### After: V2 `permissions:` array

This is exactly what `--format v2` produces for that file (path placeholders
shown un-substituted; the installer resolves them):

```yaml
mode: subagent
description: "Paper section writer. Works from a shared outline, cites only verified references, ..."
# skills: humanizer, skill-academic-humanizer (V1-only field; see docs/opencode-v1-v2.md)
permissions:
  - action: "*"
    resource: "*"
    effect: deny
  - action: read
    resource: "*"
    effect: allow
  - action: edit
    resource: "{{OPENBIOACADEMIA_DIR}}/out/papers/*"
    effect: allow
  - action: shell
    resource: "*"
    effect: deny
  - action: shell
    resource: "{{OPENBIOACADEMIA_DIR}}/bin/academica gate *"
    effect: allow
  - action: shell
    resource: "{{OPENBIOACADEMIA_DIR}}/bin/academica check *"
    effect: allow
  - action: webfetch
    resource: "*"
    effect: deny
  - action: subagent
    resource: "*"
    effect: deny
  # call_omo_agent: oh-my-openagent-only; omitted in native OpenCode V2
```

What changed: `permission:` became the ordered `permissions:` array; `write`
became `edit`; `bash` became `shell`; `task` became `subagent`; the OMO-only
`call_omo_agent` key was dropped as a comment; and the V1-only per-agent
`skills:` block was dropped as a comment. `read` and `webfetch` keep their
names. Rule order is preserved, which matters because in V2 the last matching
rule wins.

## install.sh

`install.sh` reads `OC_FORMAT` (`v1` or `v2`, default `v1`) and passes it to
`tools/agents.py` as `--format`. Set it before running the installer:

```bash
# V1 (default)
bash install.sh --yes

# V2 (native, warning-free)
OC_FORMAT=v2 bash install.sh --yes
```

## Verify your install

After rendering, validate the install with `--check`. It reports missing files,
unreplaced `{{...}}` placeholders, and files without a model line:

```bash
python3 tools/agents.py --check --dest ~/.config/opencode/agents
```

A clean run prints `All 25 agents present with models` and exits 0.

## FAQ / gotchas

**Q: Do I need to convert to V2 to use OpenCode V2?**
No. The default V1 render auto-translates in V2, so it works on both. Convert to
V2 only if you want the warning-free native shape.

**Q: Why are `call_omo_agent` and similar keys missing from V2 output?**
`call_omo_agent`, `doom_loop`, `plan_enter`, `plan_exit`, `repo_clone`, and
`repo_overview` are OhMyOpenAgent-only keys. They are not V2 Core permission
actions, so `--format v2` omits them (kept as a comment for reference).

**Q: Why did my `external_directory` permission change behavior?**
V1 asks before accessing paths outside the project. V2 allows
`external_directory` by default. To restore the V1 behavior, add
`{ "action": "external_directory", "resource": "*", "effect": "ask" }` to the
`permissions` array in `opencode.json` (global `~/.config/opencode/opencode.json`
or project `.opencode/opencode.json`); narrower rules after it can re-allow
specific directories.

**Q: Does per-agent `skills:` still work in V2?**
Global and project skills (under `~/.config/opencode/skills/` and
`.opencode/skills/`) work in both V1 and V2. Per-agent `skills:` is a V1
frontmatter field, so keep skill installation at the global or project level for
portability across both versions. That is why `--format v2` drops the block
instead of emitting it.

**Q: What happened to the OMO permission actions in the v2 render?**
`call_omo_agent`, `doom_loop`, `plan_enter`, `plan_exit`, `repo_clone`, and
`repo_overview` have no native V2 Core permission equivalents, so `--format v2`
emits them as comments. If you ran on OhMyOpenAgent
under V1, those guardrails (for example `doom_loop: ask` on the research
director) only had effect while OMO was active; under native OpenCode V2 they are
inert in both formats.

**Q: Does oh-my-openagent work with OpenCode V2?**
OMO is a V1-era integration. OpenCode V2's migration guide states that V1 plugin
implementations do not run in V2, so OMO-based features (the OMO actions above,
`variant`/`fallback_models` in `agent-config.json`) only work if OMO ships V2
support. Check the OMO project for its V2 status. Native OpenBioAcademia (agents,
skills, and the `academica` CLI) does not depend on OMO at all.

**Q: Do `variant` and `fallback_models` in `config/agent-config.json` affect rendering?**
No. The renderer bakes only the agent's `model` into the frontmatter (one
`model:` line, valid on both V1 and V2). `variant`, `fallback_models`,
`skills`, and the `permission` map in `agent-config.json` are OhMyOpenAgent
fields; OpenCode itself reads only the rendered agent files and `opencode.json`.

**Q: Is the installed `~/.config/opencode/agent-config.json` read by OpenCode?**
No. It is a reference copy for you (and for OMO under its own conventions).
OpenCode loads `opencode.json(c)` plus the rendered `agents/*.md` files. To
change providers, edit the repo's `config/agent-config.json` and re-run
`tools/agents.py`, or pass `--model` / `--default-model`.
