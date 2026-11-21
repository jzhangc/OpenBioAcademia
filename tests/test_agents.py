"""Tests for the agent definitions, model config, installer rendering and portable skills."""

import json
import re
from pathlib import Path

import pytest

from openbioacademia.tools import agents, reviews, workspace

REPO = Path(__file__).resolve().parent.parent
NOVELTY = [
    "assumption-excavator",
    "contrarian",
    "counterfactual-generator",
    "cross-pollinator",
    "heretic",
    "paradox-sifter",
]

# A compact V1-style agent frontmatter used by the --format tests. It exercises
# every transform path: a quoted wildcard scalar, a read map, a write map with a
# path placeholder, a bash scalar, a webfetch scalar, a task scalar and the
# oh-my-openagent-only call_omo_agent action.
V1_SAMPLE = (
    '---\nmode: subagent\ndescription: "x"\npermission:\n'
    '  "*": deny\n'
    "  read:\n"
    '    "*": allow\n'
    "  write:\n"
    '    "{{OPENBIOACADEMIA_DIR}}/out/papers/*": allow\n'
    "  bash: deny\n"
    "  webfetch: allow\n"
    "  task: deny\n"
    "  call_omo_agent: deny\n"
    "---\nBody\n"
)


def body(path: Path) -> str:
    text = path.read_text()
    return text.split("\n---", 1)[1].split("\n", 1)[1].strip()


def permissions_block_lines(front: str) -> list:
    """Return the indented lines under the top-level 'permissions:' key,
    i.e. the V2 rules and comments, without the 'permissions:' line itself.
    Mirrors the block-end logic in agents._transform_permissions."""
    lines = front.split("\n")
    idx = None
    for i, line in enumerate(lines):
        if re.match(r"^permissions:", line):
            idx = i
            break
    if idx is None:
        return []
    out = []
    for line in lines[idx + 1 :]:
        if line.strip() == "" or line[0] in (" ", "\t"):
            out.append(line)
        else:
            break
    return out


def test_there_are_25_agents_and_all_are_configured():
    files = agents.agent_files(REPO)
    assert len(files) == agents.EXPECTED_AGENTS
    config = json.loads((REPO / "config" / "agent-config.json").read_text())
    assert {f.stem for f in files} == set(config["agents"])
    assert config["default_model"]


@pytest.mark.parametrize("path", agents.agent_files(REPO), ids=lambda p: p.stem)
def test_agent_frontmatter(path):
    text = path.read_text()
    assert text.startswith("---\n")
    front = text.split("\n---", 1)[0]
    assert re.search(r'^description: ".+"$', front, re.M)
    assert "\nmodel:" not in front, "model comes from config/agent-config.json"
    assert "/root/" not in text, "use {{OPENBIOACADEMIA_DIR}} placeholders, not hardcoded paths"


def test_reviewers_and_engines_match_their_portable_skills():
    for name in list(reviews.PERSONAS) + NOVELTY:
        folder = "reviewers" if name in reviews.PERSONAS else "novelty-engines"
        assert body(REPO / folder / f"{name}.md") == body(REPO / "skills" / name / "SKILL.md"), name


def test_skills_are_standalone():
    for skill in (REPO / "skills").glob("*/SKILL.md"):
        text = skill.read_text()
        assert re.search(rf'^name: "?{skill.parent.name}"?$', text, re.M), skill
        assert "{{" not in text and "academica " not in text and "out/papers" not in text, skill


def test_reviewer_prompts_define_the_gate_schema():
    for persona in reviews.PERSONAS:
        text = (REPO / "reviewers" / f"{persona}.md").read_text()
        example = json.loads(re.search(r"```json\n(.*?)```", text, re.S).group(1))
        assert reviews.validate_review(example, persona) == []


def test_novelty_prompts_define_shared_fields():
    for engine in workspace.ENGINES:
        text = (REPO / "novelty-engines" / f"{engine}.md").read_text()
        for field in ("`novelty`", "`tractability`", "`impact`", "`evidence`"):
            assert field in text, (engine, field)


def test_prompts_contain_no_em_dashes():
    for path in agents.agent_files(REPO) + list((REPO / "skills").glob("*/SKILL.md")):
        assert "—" not in path.read_text(), path


def test_render_sets_model_and_paths():
    src = (
        '---\nmode: subagent\ndescription: "x"\npermission:\n  write:\n'
        '    "{{OPENBIOACADEMIA_DIR}}/out/*": allow\n---\nBody\n'
    )
    out = agents.render(src, "anthropic/claude-sonnet-4", {"OPENBIOACADEMIA_DIR": "/opt/sa"})
    assert '"/opt/sa/out/*": allow' in out
    assert "\nmodel: anthropic/claude-sonnet-4\n---\nBody" in out


def test_render_v2_maps_actions():
    out = agents.render(
        V1_SAMPLE,
        "anthropic/claude-sonnet-4",
        {"OPENBIOACADEMIA_DIR": "/opt/sa"},
        fmt="v2",
    )
    # The V2 array key replaces the V1 block key.
    assert "permissions:" in out
    assert re.search(r"^permission:", out, re.M) is None
    # Action renames and unchanged names.
    assert "action: shell" in out  # bash -> shell
    assert "action: edit" in out  # write -> edit
    assert "action: subagent" in out  # task -> subagent
    assert "action: read" in out  # unchanged
    assert "action: webfetch" in out  # unchanged
    # Both effects appear, and the substituted write path is quoted.
    assert "effect: deny" in out
    assert "effect: allow" in out
    assert 'resource: "/opt/sa/out/papers/*"' in out
    # The oh-my-openagent-only action becomes a comment, never a rule.
    assert "action: call_omo_agent" not in out
    assert "# call_omo_agent: oh-my-openagent-only; omitted in native OpenCode V2" in out


def test_render_v2_patch_maps_to_edit():
    # The 'patch' action (like 'write') must rename to 'edit' in V2 output.
    src = (
        '---\nmode: subagent\ndescription: "x"\npermission:\n'
        '  "*": deny\n'
        "  patch: deny\n"
        "  read:\n"
        '    "*": allow\n'
        "---\nBody\n"
    )
    out = agents.render(src, "prov/m", {}, fmt="v2")
    assert "action: edit" in out
    assert re.search(r"action: patch", out) is None


def test_render_v2_strips_skills():
    src = (
        '---\nmode: subagent\ndescription: "x"\nskills:\n'
        "  - humanizer\n"
        "  - skill-academic-humanizer\n"
        "permission:\n"
        "  read:\n"
        '    "*": allow\n---\nBody\n'
    )
    out = agents.render(src, "prov/m", {}, fmt="v2")
    # The V1-only per-agent skills block is gone from V2 output...
    assert re.search(r"^skills:", out, re.M) is None
    # ...but the intent is kept as a comment.
    assert "# skills: humanizer, skill-academic-humanizer (V1-only field" in out
    # V1 output keeps the skills block verbatim.
    v1 = agents.render(src, "prov/m", {}, fmt="v1")
    assert "skills:\n  - humanizer\n  - skill-academic-humanizer\n" in v1
    assert "#" not in v1.split("\n---")[0]


def test_render_v1_unchanged():
    model = "anthropic/claude-sonnet-4"
    paths = {"OPENBIOACADEMIA_DIR": "/opt/sa"}
    default = agents.render(V1_SAMPLE, model, paths)
    explicit = agents.render(V1_SAMPLE, model, paths, fmt="v1")
    # Defaulting to v1 is byte-for-byte identical to passing it explicitly.
    assert default == explicit
    # The V1 block key and its verbatim contents survive untouched.
    assert "permission:" in default
    assert "bash: deny" in default
    assert "call_omo_agent: deny" in default
    # No V2 artifacts leak in.
    assert "permissions:" not in default
    assert "action: shell" not in default


def test_render_v2_real_agent():
    paths = {
        "OPENBIOACADEMIA_DIR": "/opt/sa",
        "OPENCODE_CONFIG": "/opt/sa/.config/opencode",
        "OPENCODE_DATA": "/opt/sa/.local/share/opencode",
    }
    for path in agents.agent_files(REPO):
        out = agents.render(
            path.read_text(), "ollama/qwen3.8:27b-mxfp8", paths, fmt="v2"
        )
        assert re.search(r"^permissions:", out, re.M), path
        assert re.search(r"^permission:", out, re.M) is None, path
        assert re.search(r"^skills:", out, re.M) is None, path
        assert "{{" not in out, path
        assert re.search(r"^model: ", out, re.M), path
        # Agents that list skills keep them as a comment in V2 output.
        if re.search(r"^skills:", path.read_text().split("\n---", 1)[0], re.M):
            assert "# skills:" in out, path
        # No oh-my-openagent-only action leaks in as a V2 rule.
        assert "action: call_omo_agent" not in out, path
        assert "action: doom_loop" not in out, path
        # The renamed V1 actions (bash/task/write/patch) must not leak in; the
        # unchanged ones (read, webfetch, external_directory, question) may.
        assert re.search(r"action: bash", out) is None, path
        assert re.search(r"action: task", out) is None, path
        assert re.search(r"action: write", out) is None, path
        assert re.search(r"action: patch", out) is None, path


def test_model_selection():
    config = {
        "default_model": "router/free",
        "agents": {
            "writer": {"model": "anthropic/claude-opus-4"},
            "skeptic": {"model": "router/free"},
        },
    }
    assert agents.model_for("writer", config) == "anthropic/claude-opus-4"
    assert agents.model_for("verifier", config) == "router/free"
    assert agents.model_for("skeptic", config, default_model="openai/gpt-4o") == "openai/gpt-4o"
    assert (
        agents.model_for("writer", config, default_model="openai/gpt-4o")
        == "anthropic/claude-opus-4"
    )
    assert agents.model_for("writer", config, override="openai/gpt-4o") == "openai/gpt-4o"


def test_install_and_check(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai/gpt-4o")
    written = agents.install(tmp_path / "agents", opencode_config=tmp_path / "oc")
    assert len(written) == 25
    assert agents.check(tmp_path / "agents") == []
    text = (tmp_path / "agents" / "writer.md").read_text()
    assert "model: openai/gpt-4o" in text and "{{" not in text
    assert str(REPO) in text


def test_render_v2_flow_style_fails_loudly():
    # Flow-style maps (the old CONTRIBUTING template shape) used to render a
    # broken effect; the transform must refuse them instead.
    src = (
        '---\nmode: subagent\ndescription: "x"\npermission:\n'
        '  "*": deny\n'
        '  read: { "*": allow }\n---\nBody\n'
    )
    with pytest.raises(ValueError, match="flow-style map"):
        agents.render(src, "prov/m", {}, fmt="v2")
    # v1 keeps the block verbatim, so the same source renders fine there.
    assert 'read: { "*": allow }' in agents.render(src, "prov/m", {})


def test_render_v2_unquotes_effects():
    src = (
        '---\nmode: subagent\ndescription: "x"\npermission:\n'
        '  read:\n'
        '    "*": "allow"\n---\nBody\n'
    )
    out = agents.render(src, "prov/m", {}, fmt="v2")
    assert "effect: allow" in out
    assert 'effect: "allow"' not in out


def test_render_v2_no_permission_block():
    src = '---\nmode: subagent\ndescription: "x"\nskills:\n  - humanizer\n---\nBody\n'
    out = agents.render(src, "prov/m", {}, fmt="v2")
    assert "permissions:" not in out
    assert re.search(r"^skills:", out, re.M) is None
    assert "# skills: humanizer" in out


def test_strip_skills_inline_and_empty():
    inline = '---\nmode: subagent\ndescription: "x"\nskills: [a, "b"]\n---\nBody\n'
    out = agents.render(inline, "prov/m", {}, fmt="v2")
    assert "# skills: a, b (V1-only field" in out
    empty = '---\nmode: subagent\ndescription: "x"\nskills: []\n---\nBody\n'
    out = agents.render(empty, "prov/m", {}, fmt="v2")
    assert re.search(r"^skills:", out, re.M) is None
    assert "# skills: (V1-only field" in out


def test_render_v2_replaces_source_model_line():
    src = (
        '---\nmode: subagent\ndescription: "x"\nmodel: old/old\n'
        "permission:\n"
        "  read:\n"
        '    "*": allow\n---\nBody\n'
    )
    out = agents.render(src, "prov/m", {}, fmt="v2")
    assert out.count("model: ") == 1
    assert "\nmodel: prov/m\n---\nBody" in out


def test_render_v2_preserves_rule_order():
    # V2 is last-matching-rule-wins, so the order the V1 block was written in
    # (broad rule first, exceptions after) is load-bearing. Pin it for the
    # richest agent: writer.md.
    paths = {"OPENBIOACADEMIA_DIR": "/opt/sa"}
    out = agents.render(
        (REPO / "subagents" / "writer.md").read_text(), "prov/m", paths, fmt="v2"
    )
    rules = []
    current = {}
    for line in out.split("\n---")[0].splitlines():
        m = re.match(r"\s*- action: (.+)$", line)
        if m:
            current = {"action": m.group(1).strip().strip('"')}
            continue
        m = re.match(r"\s*(resource|effect): (.+)$", line)
        if m and current:
            current[m.group(1)] = m.group(2).strip().strip('"')
            if "effect" in current:
                rules.append(
                    (current["action"], current["resource"], current["effect"])
                )
                current = {}
    assert rules == [
        ("*", "*", "deny"),
        ("read", "*", "allow"),
        ("edit", "/opt/sa/out/papers/*", "allow"),
        ("shell", "*", "deny"),
        ("shell", "/opt/sa/bin/academica gate *", "allow"),
        ("shell", "/opt/sa/bin/academica check *", "allow"),
        ("webfetch", "*", "deny"),
        ("subagent", "*", "deny"),
    ]


def test_main_format_v2_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("LLM_PROVIDER", "openai/gpt-4o")
    rc = agents.main(
        [
            "--dest",
            str(tmp_path / "agents"),
            "--opencode-config",
            str(tmp_path / "oc"),
            "--format",
            "v2",
        ]
    )
    assert rc == 0
    assert "permissions:" in (tmp_path / "agents" / "writer.md").read_text()
    assert "All 25 agents present with models" in capsys.readouterr().out


def test_install_v2_and_check(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai/gpt-4o")
    written = agents.install(
        tmp_path / "agents", opencode_config=tmp_path / "oc", fmt="v2"
    )
    assert len(written) == 25
    assert agents.check(tmp_path / "agents") == []
    text = (tmp_path / "agents" / "writer.md").read_text()
    assert "permissions:" in text and "model: openai/gpt-4o" in text
    assert "{{" not in text
    # V1-only frontmatter keys are absent from the native V2 render.
    assert re.search(r"^permission:", text, re.M) is None
    assert re.search(r"^skills:", text, re.M) is None


def test_v2_frontmatter_is_valid_yaml(tmp_path, monkeypatch):
    """Structurally validate the V2 permissions block with the stdlib, so the
    test runs and asserts something meaningful even when PyYAML is absent; then
    add a PyYAML parse as an optional, additional check guarded by importorskip."""
    monkeypatch.setenv("LLM_PROVIDER", "openai/gpt-4o")
    agents.install(tmp_path / "agents", opencode_config=tmp_path / "oc", fmt="v2")
    # Always-on: every non-comment, non-blank line under 'permissions:' has the
    # V2 rule shape, effect values are valid, and no oh-my-openagent-only
    # action leaks in as a rule.
    for path in (tmp_path / "agents").glob("*.md"):
        front = path.read_text().split("\n---", 1)[0][4:]
        for line in permissions_block_lines(front):
            if line.strip() == "" or line.lstrip().startswith("#"):
                continue
            action = re.match(r"^  - action: (.+)$", line)
            resource = re.match(r"^    resource: (.+)$", line)
            effect = re.match(r"^    effect: (.+)$", line)
            assert action or resource or effect, (path, line)
            if action:
                assert agents._unquote(action.group(1)) not in agents._OMO_ACTIONS, (path, line)
            if effect:
                assert agents._unquote(effect.group(1)) in ("allow", "ask", "deny"), (path, line)
    # Additional, only if PyYAML imports: the frontmatter parses as a list of
    # {action, resource, effect} dicts.
    yaml = pytest.importorskip("yaml")
    for path in (tmp_path / "agents").glob("*.md"):
        front = path.read_text().split("\n---", 1)[0][4:]
        data = yaml.safe_load(front)
        assert isinstance(data["permissions"], list), path
        for rule in data["permissions"]:
            assert set(rule) == {"action", "resource", "effect"}, (path, rule)


def test_director_uses_existing_commands_and_stages():
    text = (REPO / "orchestrator" / "research-director.md").read_text()
    from openbioacademia.cli import COMMANDS

    for command in re.findall(r"\$S ([a-z]+)", text):
        assert command in COMMANDS, command
    for stage in re.findall(r"\$S check RUN ([a-z]+)", text):
        assert stage in workspace.STAGE_IDS, stage
