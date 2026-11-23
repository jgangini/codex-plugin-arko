"""Repository example delegates to the plugin's single maintained implementation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "plugins/arko/skills/arko/scripts"))
from arko_lib.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
