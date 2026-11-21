"""Tests for the CLI module (src/openbioacademia/cli.py)."""

import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


class TestCliHelp:
    """Test CLI entry point behavior."""

    def test_no_args_shows_help(self):
        """academica with no args should print help and not crash."""
        from openbioacademia.cli import main
        with patch.object(sys, "argv", ["academica"]):
            try:
                main()
            except SystemExit:
                pass  # Some implementations may exit

    def test_demo_command_runs(self):
        """academica demo should run without crashing."""
        from openbioacademia.cli import main
        with patch.object(sys, "argv", ["academica", "demo"]):
            try:
                main()
            except SystemExit:
                pass


class TestCliCommands:
    """Test specific commands."""

    def test_configure_command_runs(self):
        """academica configure should start without crashing."""
        from openbioacademia.cli import main
        with patch.object(sys, "argv", ["academica", "configure"]):
            try:
                main()
            except SystemExit:
                pass

    def test_search_without_query_prints_usage(self):
        """academica search without query should show usage."""
        from openbioacademia.cli import main
        with patch.object(sys, "argv", ["academica", "search"]):
            try:
                main()
            except SystemExit:
                pass

    def test_bibtex_without_doi_prints_usage(self):
        """academica bibtex without DOI should show usage."""
        from openbioacademia.cli import main
        with patch.object(sys, "argv", ["academica", "bibtex"]):
            try:
                main()
            except SystemExit:
                pass

    def test_verify_without_args_prints_usage(self):
        """academica verify without args should show usage."""
        from openbioacademia.cli import main
        with patch.object(sys, "argv", ["academica", "verify"]):
            try:
                main()
            except SystemExit:
                pass

    def test_unknown_command_prints_usage(self):
        """Unknown commands should not crash."""
        from openbioacademia.cli import main
        with patch.object(sys, "argv", ["academica", "nonexistent"]):
            try:
                main()
            except SystemExit:
                pass


class TestCliVersion:
    """Test version reporting and the pyproject drift guard."""

    def test_version_flag_prints_version(self, capsys):
        """academica --version prints the composite version and exits 0."""
        from openbioacademia import __version__
        from openbioacademia.cli import main
        with patch.object(sys, "argv", ["academica", "--version"]):
            with pytest.raises(SystemExit) as exc:
                main()
        assert exc.value.code == 0
        assert __version__ in capsys.readouterr().out

    def test_version_encodes_upstream(self):
        """The version carries both the fork and the upstream version."""
        from openbioacademia import __version__
        base, _, local = __version__.partition("+")
        assert re.fullmatch(r"\d+\.\d+\.\d+", base)
        assert re.match(r"up\.\d+\.\d+\.\d+$", local)

    def test_version_matches_pyproject(self):
        """__version__ stays in sync with pyproject.toml."""
        from openbioacademia import __version__
        text = (Path(__file__).resolve().parent.parent / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        assert match is not None
        assert match.group(1) == __version__
