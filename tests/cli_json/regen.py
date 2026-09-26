"""Regenerate the golden CLI `--json` fixtures next to this file.

Run it only when the report shape changed *on purpose*, and read the diff: these
files are the published contract in `docs/JSON-OUTPUT.md`, so a surprise in the
diff means an accidental breaking change.

    python tests/cli_json/regen.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))
sys.path.insert(0, os.path.dirname(HERE))

from test_cli_json import CASES, run_json  # noqa: E402


def main() -> int:
    for name, argv, expected_exit in CASES:
        code, report = run_json(argv)
        if code != expected_exit:
            print(f"!! {name}: exit {code}, expected {expected_exit}")
            return 1
        report.pop("rubric_version", None)
        path = os.path.join(HERE, name + ".json")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        print(f"wrote {name}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
