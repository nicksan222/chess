"""Execute board pytest checks and retain machine-readable coverage evidence."""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def run_suite(tests: Path, directory: Path) -> dict[str, object]:
    """Run collected pytest cases; failures, skips and empty suites cannot pass."""
    directory.mkdir(parents=True, exist_ok=True)
    junit = directory / "junit.xml"
    result = subprocess.run(
        (
            sys.executable,
            "-m",
            "pytest",
            str(tests),
            "-q",
            "-rA",
            "-o",
            "python_files=*_test.py test_*.py",
            f"--junitxml={junit}",
        ),
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    (directory / "tests.log").write_text(result.stdout + result.stderr)
    cases: dict[str, dict[str, str]] = {}
    if junit.exists():
        for case in ET.parse(junit).iter("testcase"):
            name = f"{case.get('classname', '')}.{case.get('name', '')}"
            failure = case.find("failure")
            error = case.find("error")
            skip = case.find("skipped")
            problem = failure if failure is not None else error
            if problem is not None:
                cases[name] = {"status": "failed", "reason": problem.get("message", "")}
            elif skip is not None:
                cases[name] = {"status": "blocked", "reason": skip.get("message", "")}
            else:
                cases[name] = {"status": "passed"}
    passed = sum(case["status"] == "passed" for case in cases.values())
    summary: dict[str, object] = {
        "planned": len(cases),
        "passed": passed,
        "blocked": sum(case["status"] == "blocked" for case in cases.values()),
        "failed": sum(case["status"] == "failed" for case in cases.values()),
        "complete": result.returncode == 0 and bool(cases) and passed == len(cases),
        "cases": cases,
    }
    (directory / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    if result.returncode:
        raise ValueError(f"electrical tests failed:\n{result.stdout}{result.stderr}")
    return summary
