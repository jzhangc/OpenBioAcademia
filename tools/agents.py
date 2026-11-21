#!/usr/bin/env python3
"""
OpenBioAcademia: render and install the 25 OpenCode agents.

Model selection comes from config/agent-config.json: each agent's "model",
else "default_model". --default-model (set by the install.sh interview)
replaces the default and keeps per-agent customizations. LLM_PROVIDER (from
.env or the environment) or --model overrides every agent at once. Model strings
use the provider/model form, so any provider OpenCode knows works: anthropic/..., openai/..., or an
OpenAI-compatible endpoint configured in opencode.json.

Placeholders {{OPENBIOACADEMIA_DIR}}, {{OPENCODE_CONFIG}} and {{OPENCODE_DATA}} in the
agent files are replaced with real paths at install time.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

try:
    from . import settings
except ImportError:  # run as a script: python3 tools/agents.py
    import settings

AGENT_DIRS = ("orchestrator", "subagents", "novelty-engines", "reviewers")
EXPECTED_AGENTS = 25


def agent_files(repo: Optional[Path] = None) -> List[Path]:
    repo = repo or settings.repo_dir()
    return [f for d in AGENT_DIRS for f in sorted((repo / d).glob("*.md"))]


def model_for(
    name: str, config: Dict, override: Optional[str] = None, default_model: Optional[str] = None
) -> str:
    """Model for one agent: override > agent model > default.

    default_model replaces config's default_model, including agents whose
    model equals the old default, so per-agent customizations survive.
    """
    if override:
        return override
    agent = (config.get("agents") or {}).get(name) or {}
    old_default = config.get("default_model")
    model = agent.get("model") or old_default
    if default_model and model == old_default:
        model = default_model
    if not model:
        raise ValueError(
            f"no model for agent {name!r}: set agents.{name}.model or default_model "
            "in config/agent-config.json"
        )
    return model


# --- OpenCode V2 permission transform ---------------------------------------
# V1 'permission:' block -> V2 'permissions:' array. The renames below map V1
# actions onto their V2 Core names; everything else (read, webfetch, websearch,
# glob, grep, skill, question, external_directory, "*") keeps its name.
_ACTION_RENAMES = {
    "bash": "shell",
    "task": "subagent",
    "write": "edit",
    "patch": "edit",
}

# oh-my-openagent-only actions are not native OpenCode V2 Core permissions;
# they are emitted as a comment instead of a rule.
_OMO_ACTIONS = frozenset(
    {
        "call_omo_agent",
        "doom_loop",
        "plan_enter",
        "plan_exit",
        "repo_clone",
        "repo_overview",
    }
)

_OMO_COMMENT = "oh-my-openagent-only; omitted in native OpenCode V2"

_BARE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _indent(line: str) -> int:
    """Leading spaces. Indentation is space-based; tab-indented frontmatter is
    not supported (all agent files use spaces)."""
    return len(line) - len(line.lstrip(" "))


def _split_kv(s: str):
    """Split a stripped 'key: value' line into (key, value).

    A 'key:' map header yields value ''. A quoted key is located by its closing
    quote so a colon inside the quoted key is not mistaken for the separator.
    Note: a quoted key is located by the first quote char, so it may not contain an escaped quote (e.g. "a\\"b").
    """
    if s and s[0] in ("\"", "'"):
        quote = s[0]
        end = s.find(quote, 1)
        if end == -1:
            key, _, value = s.partition(":")
            return key.strip(), value.strip()
        key = s[: end + 1]
        _, _, value = s[end + 1 :].partition(":")
        return key.strip(), value.strip()
    key, _, value = s.partition(":")
    return key.strip(), value.strip()


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("\"", "'"):
        return s[1:-1]
    return s


def _fmt(value: str) -> str:
    """Quote (escaping \\ and ") a value unless it is a bare identifier."""
    if _BARE_RE.match(value):
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + escaped + '"'


def _transform_permissions(front: str) -> str:
    """Replace the V1 indent-0 'permission:' block with a V2 'permissions:'
    array, preserving rule order. Only that block is touched; skills,
    description, mode and the (later-stripped) model line are left intact.
    Returns the front unchanged when there is no 'permission:' block.
    """
    lines = front.split("\n")
    perm_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^permission:\s*$", line):
            perm_idx = i
            break
    if perm_idx is None:
        return front
    block_end = perm_idx + 1
    while block_end < len(lines):
        entry = lines[block_end]
        if entry.strip() == "" or entry[0] in (" ", "\t"):
            block_end += 1
        else:
            break
    block = lines[perm_idx + 1 : block_end]
    non_blank = [entry for entry in block if entry.strip() != ""]
    if not non_blank:
        return "\n".join(lines[:perm_idx] + ["permissions: []"] + lines[block_end:])
    base_indent = min(_indent(entry) for entry in non_blank)
    out = ["permissions:"]
    current_map = None
    for line in block:
        if line.strip() == "":
            continue
        key, value = _split_kv(line.strip())
        name = _unquote(key)
        if value.lstrip().startswith("{"):
            raise ValueError(
                f"flow-style map {line.strip()!r} is not supported in the "
                "'permission' block; use block style (one 'key: value' per line)"
            )
        if _indent(line) > base_indent:
            if current_map is None:
                continue
            action = _ACTION_RENAMES.get(current_map, current_map)
            out.append(f"  - action: {_fmt(action)}")
            out.append(f"    resource: {_fmt(name)}")
            out.append(f"    effect: {_fmt(_unquote(value))}")
        elif value == "":
            if name in _OMO_ACTIONS:
                out.append(f"  # {name}: {_OMO_COMMENT}")
            current_map = None if name in _OMO_ACTIONS else name
        else:
            if name in _OMO_ACTIONS:
                out.append(f"  # {name}: {_OMO_COMMENT}")
            else:
                action = _ACTION_RENAMES.get(name, name)
                out.append(f"  - action: {_fmt(action)}")
                out.append(f"    resource: {_fmt('*')}")
                out.append(f"    effect: {_fmt(_unquote(value))}")
            current_map = None
    return "\n".join(lines[:perm_idx] + out + lines[block_end:])


def _strip_v1_skills(front: str) -> str:
    """Replace the V1-only 'skills:' block with a comment.

    V2 agent definitions have no per-agent skills field, so the block is
    dropped in v2 output. Skill discovery is global (~/.config/opencode/skills)
    or project (.opencode/skills) in both versions. The comment keeps the
    intended skills visible in the rendered file.
    """
    lines = front.split("\n")
    idx = None
    header_value = ""
    for i, line in enumerate(lines):
        m = re.match(r"^skills:\s*(\S.*)?$", line)
        if m:
            idx = i
            header_value = (m.group(1) or "").strip()
            break
    if idx is None:
        return front
    if header_value.startswith("[") and header_value.endswith("]"):
        # Inline flow list: occupies its header line only.
        inner = header_value[1:-1]
        names = [_unquote(part.strip()) for part in inner.split(",") if part.strip()]
        block_end = idx + 1
    else:
        block_end = idx + 1
        while block_end < len(lines) and (
            lines[block_end].strip() == "" or lines[block_end][0] in (" ", "\t")
        ):
            block_end += 1
        names = [
            _unquote(entry.strip().lstrip("-").strip())
            for entry in lines[idx + 1 : block_end]
            if entry.strip().startswith("-")
        ]
    note = "# skills: (V1-only field; V2 discovers skills globally or under .opencode/skills)"
    if names:
        note = f"# skills: {', '.join(names)} (V1-only field; see docs/opencode-v1-v2.md)"
    return "\n".join(lines[:idx] + [note] + lines[block_end:])


def render(text: str, model: str, paths: Dict[str, str], fmt: str = "v1") -> str:
    for placeholder, value in paths.items():
        text = text.replace("{{" + placeholder + "}}", value)
    if not text.startswith("---\n"):
        raise ValueError("agent file must start with YAML frontmatter")
    end = text.index("\n---", 4)
    front, body = text[4:end], text[end:]
    if fmt == "v2":
        front = _transform_permissions(front)
        front = _strip_v1_skills(front)
    front = re.sub(r"^model:.*\n?", "", front, flags=re.M).rstrip("\n")
    return f"---\n{front}\nmodel: {model}{body}"


def install(
    dest: Path,
    override: Optional[str] = None,
    opencode_config: Optional[Path] = None,
    config_path: Optional[Path] = None,
    default_model: Optional[str] = None,
    fmt: str = "v1",
) -> List[Path]:
    settings.ensure_env()
    override = override or os.environ.get("LLM_PROVIDER") or None
    config = settings.load_agent_config(config_path)
    home = Path.home()
    paths = {
        "OPENBIOACADEMIA_DIR": str(settings.repo_dir()),
        "OPENCODE_CONFIG": str(opencode_config or home / ".config" / "opencode"),
        "OPENCODE_DATA": str(home / ".local" / "share" / "opencode"),
    }
    dest.mkdir(parents=True, exist_ok=True)
    written = []
    for src in agent_files():
        name = src.stem
        out = dest / src.name
        model = model_for(name, config, override, default_model)
        out.write_text(
            render(src.read_text(encoding="utf-8"), model, paths, fmt),
            encoding="utf-8",
        )
        written.append(out)
    return written


def check(dest: Path) -> List[str]:
    """Problems with an installed agent directory."""
    problems = []
    for src in agent_files():
        out = dest / src.name
        if not out.exists():
            problems.append(f"missing {out}")
            continue
        text = out.read_text(encoding="utf-8")
        if "{{" in text:
            problems.append(f"{out.name}: unreplaced placeholder")
        if not re.search(r"^model: \S+", text, re.M):
            problems.append(f"{out.name}: no model line")
    return problems


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Install OpenBioAcademia agents into OpenCode")
    parser.add_argument("--dest", default=str(Path.home() / ".config" / "opencode" / "agents"))
    parser.add_argument(
        "--opencode-config", help="OpenCode config dir (default ~/.config/opencode)"
    )
    parser.add_argument("--model", help="Use this provider/model for every agent")
    parser.add_argument(
        "--default-model", help="Replace default_model (agents with custom models keep them)"
    )
    parser.add_argument("--check", action="store_true", help="Validate an existing install")
    parser.add_argument(
        "--format",
        choices=["v1", "v2"],
        default="v1",
        help="OpenCode config format (v1 default, v2 = native permissions array)",
    )
    args = parser.parse_args(argv)
    dest = Path(args.dest).expanduser()
    if not args.check:
        written = install(
            dest,
            args.model,
            Path(args.opencode_config) if args.opencode_config else None,
            default_model=args.default_model,
            fmt=args.format,
        )
        print(f"  Installed {len(written)} agents into {dest}")
    problems = check(dest)
    count = len(agent_files())
    if count != EXPECTED_AGENTS:
        problems.append(f"repo has {count} agent files, expected {EXPECTED_AGENTS}")
    for p in problems:
        print(f"  ! {p}")
    if not problems:
        print(f"  All {count} agents present with models")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
