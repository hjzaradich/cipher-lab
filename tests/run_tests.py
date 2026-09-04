"""Run every suite, each in its own process.

    python tests/run_tests.py

No test framework needed. Each suite is also a plain pytest test, so
`python -m pytest tests` works if you would rather use that.

Separate processes on purpose: several suites build a Tk root, and one rewrites
sys.platform, neither of which survives being repeated in a single interpreter.
"""

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    suites = sorted(HERE.glob("test_*.py"))
    if argv:   # e.g. `python tests/run_tests.py caesar smiley`
        wanted = [a.lower() for a in argv]
        suites = [s for s in suites if any(w in s.stem.lower() for w in wanted)]
        if not suites:
            print("nothing matched %r" % argv)
            return 1

    failures = []
    started = time.time()
    for suite in suites:
        # Flush before handing the console to the child: our own output is
        # buffered, the subprocess writes straight through, and unflushed
        # headers would land after the results they introduce.
        print("=" * 68)
        print(suite.name)
        print("-" * 68, flush=True)
        result = subprocess.run([sys.executable, "-X", "utf8", str(suite)],
                                cwd=str(HERE))
        if result.returncode:
            failures.append(suite.name)
        print(flush=True)

    print("=" * 68)
    elapsed = time.time() - started
    if failures:
        print("FAILED (%d of %d) in %.1fs" % (len(failures), len(suites), elapsed))
        for name in failures:
            print("  - " + name)
        return 1
    print("All %d suites passed in %.1fs." % (len(suites), elapsed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
