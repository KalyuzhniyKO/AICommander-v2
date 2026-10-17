# Local Python dependency audit — #20

[Русский](DEPENDENCY_AUDIT.md)

2026-10-18: audited the actual macOS/Python 3.13 development/UI environment used
for project tests, not Zorin. [PyPA pip-audit 2.10.1](https://github.com/pypa/pip-audit)
ran in a separate temporary venv against application site-packages, using PyPI
advisories. No application code, database or credentials were sent; only public
package names/versions. No application runtime dependency was added.

Before: 35 distributions, exit 1, eight advisory entries in pip 26.0 corresponding
to four unique PYSEC IDs. Other installed packages had no known findings.
Updated only pip to [26.2.1](https://pypi.org/project/pip/26.2.1/) from PyPI wheel;
application/dev/UI package versions stayed unchanged. Afterwards: same 35
distributions, **zero known findings, exit 0**, pip check successful.
[JSON evidence](research/dependency-audit-2026-10-18.json) records versions,
normalized findings, raw counts, final report and installed license metadata.

CI test/UI jobs update pip before installation. A dedicated read-only Ubuntu
Python 3.13 audit job installs application/UI dependencies, isolates the scanner
in another venv, audits installed application packages with --strict, fails on
findings/incomplete collection/network failures, and retains a JSON artifact.
No --fix, ignored advisories or continue-on-error. This job audits its own package
selection, not every Windows/Python matrix environment. Requirements are lower
bounds, not a hash-locked reproducible installation.

Zero known advisories is not evidence of zero unknown vulnerabilities. License
metadata is an inventory, not a completed compatibility/redistribution review.
Wheel/native notices, bundled browsers/Chromium, OS packages, other platforms,
Zorin, Hermes/OmniRoute and the separate scanner dependency environment remain
outside this result. Full #20 stays open. No upstream source was copied.
