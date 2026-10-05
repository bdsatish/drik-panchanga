#!/usr/bin/env python3
"""Run each ``tests/test_*.py`` module in its own process, in parallel.

``unittest discover`` runs every test module serially and spends most of its
wall time in a handful of Swiss Ephemeris-heavy modules. Each module is
independent, so running one process per module cuts the wall time to roughly
the slowest module. ``ci_test_summary.py`` keeps only the last ``Ran`` line,
so this runner prints one combined trailer after all module output.

Usage:
  run_tests.py [-j N]

Exits non-zero if any module fails.
"""

import argparse
import concurrent.futures
import os
import re
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Slowest modules first so a machine with few cores does not leave them last.
MODULE_ORDER = [
    "test_pdf_service",
    "test_lunar_year_calendar",
    "test_monthly_calendar",
    "test_pdf_layout",
]

RAN_RE = re.compile(r"^Ran (\d+) tests? in ([0-9.]+)s\s*$", re.MULTILINE)
FAILED_RE = re.compile(r"^FAILED \(([^)]*)\)\s*$", re.MULTILINE)


def discover_modules(tests_dir):
  names = sorted(
      name[:-3] for name in os.listdir(tests_dir) if name.startswith("test_") and name.endswith(".py"))
  rank = {name: index for index, name in enumerate(MODULE_ORDER)}
  return sorted(names, key=lambda name: (rank.get(name, len(MODULE_ORDER)), name))


def run_module(module):
  result = subprocess.run(
      [sys.executable, "-m", "unittest", f"tests.{module}"],
      cwd=REPO_ROOT,
      capture_output=True,
      text=True,
  )
  return module, result.returncode, result.stdout + result.stderr


def parse_counts(output):
  ran = 0
  for match in RAN_RE.finditer(output):
    ran += int(match.group(1))
  failures = errors = 0
  failed = FAILED_RE.search(output)
  if failed:
    for part in failed.group(1).split(","):
      key, _, value = part.strip().partition("=")
      if key == "failures":
        failures = int(value)
      elif key == "errors":
        errors = int(value)
  return ran, failures, errors


def main(argv=None):
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 1, help="worker processes")
  args = parser.parse_args(argv)

  modules = discover_modules(os.path.join(REPO_ROOT, "tests"))
  started = time.perf_counter()
  results = {}
  ephemeris = None
  with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
    futures = {pool.submit(run_module, module): module for module in modules}
    for future in concurrent.futures.as_completed(futures):
      module, returncode, output = future.result()
      results[module] = (returncode, output)
      for line in output.splitlines():
        if ephemeris is None and line.startswith("ephemeris:"):
          ephemeris = line

  if ephemeris is not None:
    print(ephemeris, file=sys.stderr)

  total = failures = errors = 0
  for module in modules:
    returncode, output = results[module]
    ran, module_failures, module_errors = parse_counts(output)
    total += ran
    failures += module_failures
    errors += module_errors
    if returncode != 0:
      for line in output.splitlines():
        if line.startswith("ephemeris:"):
          continue
        print(line)

  wall = time.perf_counter() - started
  print(f"Ran {total} tests in {wall:.3f}s")
  if failures or errors or any(result[0] != 0 for result in results.values()):
    print(f"FAILED (failures={failures}, errors={errors})")
    return 1
  print("OK")
  return 0


if __name__ == "__main__":
  sys.exit(main())
