"""OpenBioAcademia: research paper pipeline CLI and quality gates."""

from pathlib import Path

# X.Y.Z = OpenBioAcademia's own release version; +up.U.V.W = upstream
# sisyphus-academica version at the last sync. Must match pyproject.toml.
__version__ = "0.2.0+up.0.3.0"

# pip maps the repo's tools/ directory to openbioacademia.tools. In a plain source
# checkout (no install), let openbioacademia.tools resolve to <repo>/tools as well.
_repo = Path(__file__).resolve().parents[2]
if (_repo / "tools" / "literature_client.py").exists() and str(_repo) not in __path__:
    __path__.append(str(_repo))
