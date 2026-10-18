"""Build dist/wowhandy.pyz – a single executable file (standard library only).

    python3 scripts/build_zipapp.py

Copy the result anywhere (e.g. ~/.local/bin/wowhandy.pyz) and enter that path
as Handy's external script. Requires Python 3.11+ on the target system.
"""

import shutil
import sys
import tempfile
import zipapp
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    target = ROOT / "dist" / "wowhandy.pyz"
    target.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp)
        shutil.copytree(ROOT / "src" / "wowhandy", staging / "wowhandy",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (staging / "__main__.py").write_text(
            "import sys\nfrom wowhandy.cli import main\nsys.exit(main())\n", encoding="utf-8")
        zipapp.create_archive(staging, target, interpreter="/usr/bin/env python3", compressed=True)
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
