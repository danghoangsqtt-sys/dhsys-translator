"""Fail when a desktop provider combo is populated without the visibility policy.

Every ``<combo>.addItems(<provider name list>)`` in ``videotrans/`` must pass the
same ``<combo>`` expression to ``register_provider_combo`` in that module, so the
curated view and the Advanced show-all switch reach every surface.

Usage: python scripts/audit_provider_surfaces.py [root]
"""

import ast
import sys
from pathlib import Path

PROVIDER_NAME_LISTS = {"TRANSLASTE_NAME_LIST", "RECOGN_NAME_LIST", "TTS_NAME_LIST"}


def _list_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def find_unregistered(source: str, filename: str = "<source>"):
    """Return ``(line, combo)`` pairs for provider combos missing registration."""
    tree = ast.parse(source, filename=filename)
    populated = []
    registered = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (isinstance(func, ast.Attribute) and func.attr == "addItems"
                and node.args and _list_name(node.args[0]) in PROVIDER_NAME_LISTS):
            populated.append((node.lineno, ast.unparse(func.value)))
        elif _list_name(func) == "register_provider_combo" and node.args:
            registered.add(ast.unparse(node.args[0]))
    return [(line, combo) for line, combo in populated if combo not in registered]


def audit(root: Path):
    problems = []
    for path in sorted((root / "videotrans").rglob("*.py")):
        source = path.read_text(encoding="utf-8", errors="replace")
        if "addItems" not in source:
            continue
        for line, combo in find_unregistered(source, str(path)):
            problems.append(f"{path.relative_to(root).as_posix()}:{line}: {combo} is not registered")
    return problems


def main(argv):
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[1]
    problems = audit(root)
    for problem in problems:
        print(problem)
    print(f"provider surface audit: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
