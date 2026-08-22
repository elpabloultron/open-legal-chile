"""
Open Legal Chile — Script de Bump de Versión
Actualiza la versión del proyecto en todos los archivos de metadata.
Al hacer commit + push a main, el CI publica automáticamente en PyPI
y crea el GitHub Release (workflow publish-pypi.yml).

Uso:
  python scripts/bump_version.py patch            # 1.0.0 -> 1.0.1
  python scripts/bump_version.py minor            # 1.0.0 -> 1.1.0
  python scripts/bump_version.py major            # 1.0.0 -> 2.0.0
  python scripts/bump_version.py 1.2.3            # versión explícita
  python scripts/bump_version.py --check          # solo muestra la versión actual
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FILES = {
    "pyproject.toml": [
        r'(?m)^version = "([0-9]+\.[0-9]+\.[0-9]+)"'
    ],
    "setup.py": [
        r'(?m)^    version="([0-9]+\.[0-9]+\.[0-9]+)"'
    ],
    "openlegal.manifest.json": [
        r'"version": "([0-9]+\.[0-9]+\.[0-9]+)"'
    ],
    "mcp_server.py": [
        r'"version": "([0-9]+\.[0-9]+\.[0-9]+)"'
    ],
}

VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def current_version() -> str:
    txt = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for pattern in FILES["pyproject.toml"]:
        m = re.search(pattern, txt)
        if m:
            return m.group(1)
    raise SystemExit("No se pudo detectar la versión actual en pyproject.toml")


def apply_version(new_version: str) -> None:
    changed = 0
    for fname, patterns in FILES.items():
        path = ROOT / fname
        if not path.exists():
            continue
        txt = path.read_text(encoding="utf-8")
        original = txt
        for pattern in patterns:
            txt, n = re.subn(
                pattern,
                lambda m: m.group(0).replace(m.group(1), new_version),
                txt,
            )
            changed += n
        if txt != original:
            path.write_text(txt, encoding="utf-8")
            print(f"  [ok] {fname}")
    if changed == 0:
        raise SystemExit("No se encontraron referencias de versión que actualizar.")
    print(f"Versión actualizada a {new_version}")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    if args[0] == "--check":
        print(f"Versión actual: {current_version()}")
        return

    if VERSION_RE.match(args[0]):
        new_version = args[0]
    elif args[0] in ("patch", "minor", "major"):
        major, minor, patch = map(int, current_version().split("."))
        if args[0] == "major":
            major += 1
            minor = patch = 0
        elif args[0] == "minor":
            minor += 1
            patch = 0
        else:
            patch += 1
        new_version = f"{major}.{minor}.{patch}"
    else:
        print(__doc__)
        sys.exit(1)

    print(f"Bump de versión: {current_version()} -> {new_version}")
    apply_version(new_version)

    print()
    print("Siguiente paso (la publicación es automática en CI):")
    print("  git add pyproject.toml setup.py openlegal.manifest.json mcp_server.py")
    print(f'  git commit -m "chore(release): v{new_version}"')
    print("  git push origin main")


if __name__ == "__main__":
    main()
