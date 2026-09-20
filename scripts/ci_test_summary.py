#!/usr/bin/env python3
"""Turn a ``unittest`` log into GitHub annotations and a job summary.

``unittest`` writes plain text to stderr, which lands in the step log but
never reaches the checks API, so the Checks tab and PR gutter only ever show
``Process completed with exit code 1``. This script parses the log and emits
``::error`` workflow commands (giving the Checks UI the failing test, file and
line) plus a Markdown summary for the run page.

Usage:
  ci_test_summary.py LOGFILE [--ephemeris "line"]

Exits 0 even when tests failed: it reports, it does not decide. The unit test
step itself carries the failing exit status.
"""

import argparse
import os
import re
import sys

# "FAIL: test_name (module.ClassName.test_name)" / same for ERROR.
SECTION_RE = re.compile(r"^(FAIL|ERROR): (\S+) \((\S+)\)\s*$")

# Traceback frame: File "/path/to/tests/test_x.py", line 123, in test_name
FRAME_RE = re.compile(r'^\s*File "([^"]+)", line (\d+), in (\S+)\s*$')

# "Ran 442 tests in 10.170s" and "FAILED (failures=3, errors=1)" / "OK".
RAN_RE = re.compile(r"^Ran (\d+) tests? in ([0-9.]+)s\s*$")
STATUS_RE = re.compile(r"^(OK|FAILED)\b(.*)$")

# First exception line in a traceback: "AssertionError: ...", "ValueError: ...".
EXCEPTION_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception|Warning))\s*:?\s*(.*)$")

# Leading GitHub Actions log prefix: "<job>\t<step>\t2026-01-01T00:00:00.0000000Z "
LOG_PREFIX_RE = re.compile(r"^.*?\t.*?\t\d{4}-\d{2}-\d{2}T[\d:.]+Z ")


def strip_log_prefix(line):
  """Drop the Actions log prefix, which is absent when reading a local log."""
  return LOG_PREFIX_RE.sub("", line, count=1)


def parse_failures(lines):
  """Return a failure dict per ``FAIL``/``ERROR`` section, in log order."""
  failures = []
  current = None
  for raw in lines:
    line = raw.rstrip("\n")
    section = SECTION_RE.match(line)
    if section:
      if current is not None:
        failures.append(current)
      current = {
        "kind": section.group(1).lower(),
        "test": section.group(2),
        "qualname": section.group(3),
        "file": None,
        "line": None,
        "message": "",
        "local": None,
      }
      continue
    if current is None:
      continue
    frame = FRAME_RE.match(line)
    if frame and current["file"] is None:
      path, number, func = frame.groups()
      current["file"] = path
      current["line"] = int(number)
      current["local"] = func
      continue
    if not current["message"]:
      exception = EXCEPTION_RE.match(line.strip())
      if exception and exception.group(2):
        current["message"] = exception.group(2).strip()
  if current is not None:
    failures.append(current)
  return failures


def parse_summary(lines):
  """Return ``(ran, seconds, status, detail)`` from the trailing summary."""
  ran = seconds = None
  status = detail = None
  for raw in lines:
    line = raw.rstrip("\n")
    count = RAN_RE.match(line)
    if count:
      ran, seconds = int(count.group(1)), count.group(2)
      continue
    result = STATUS_RE.match(line)
    if result and ran is not None:
      status, detail = result.group(1), result.group(2).strip()
  return ran, seconds, status, detail


def relative(path):
  """Trim a traceback path to something repo-relative and clickable."""
  if not path:
    return None
  marker = "/tests/"
  if marker in path:
    return "tests/" + path.split(marker, 1)[1]
  return os.path.basename(path)


def annotation_command(failure):
  """``::error file=...,line=...,title=...::message`` for one failure."""
  location = []
  repo_path = relative(failure["file"])
  if repo_path:
    location.append(f"file={repo_path}")
  if failure["line"]:
    location.append(f"line={failure['line']}")
  title = f"{failure['kind'].upper()}: {failure['test']}"
  location.append(f"title={title}")
  message = failure["message"] or "see the test log"
  # Workflow commands are single-line; escape the reserved characters.
  message = message.replace("%", "%25").replace("\r", "").replace("\n", " ")
  return f"::error {','.join(location)}::{message}"


def render_summary(failures, ran, seconds, status, detail, ephemeris):
  """Markdown for ``$GITHUB_STEP_SUMMARY`` (and the step log fallback)."""
  lines = []
  if status == "OK":
    lines.append(f"## Unit tests passed ({ran} tests in {seconds}s)")
  elif status is None and not failures:
    # No summary line at all: the run died before unittest reported, or the log
    # was truncated. Do not claim a pass or a failure count never observed.
    lines.append("## Unit tests did not report a result")
    lines.append("")
    lines.append("See the **Run unit tests** step log: unittest never printed a "
                 "`Ran N tests` line, so the run stopped early.")
  else:
    heading = f"## Unit test failures ({len(failures)}"
    if ran is not None:
      heading += f" of {ran}"
    heading += ")"
    if detail:
      heading += f" - `{status} {detail}`"
    lines.append(heading)
  if ephemeris:
    lines.append("")
    lines.append(f"`{ephemeris}`")
  if failures:
    lines.append("")
    lines.append("| Test | Location | Message |")
    lines.append("| --- | --- | --- |")
    for failure in failures:
      repo_path = relative(failure["file"]) or "-"
      if failure["line"]:
        repo_path = f"{repo_path}:{failure['line']}"
      message = (failure["message"] or "").replace("|", "\\|")
      if len(message) > 160:
        message = message[:157] + "..."
      lines.append(f"| `{failure['test']}` | `{repo_path}` | {message} |")
  return "\n".join(lines) + "\n"


def main(argv=None):
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("logfile", help="path to the unittest log (stdout+stderr)")
  parser.add_argument("--ephemeris", default="", help="ephemeris fingerprint line to include in the summary")
  args = parser.parse_args(argv)

  try:
    with open(args.logfile, encoding="utf-8", errors="replace") as handle:
      lines = [strip_log_prefix(line) for line in handle]
  except OSError as error:
    print(f"::error::could not read test log {args.logfile}: {error}")
    return 0

  failures = parse_failures(lines)
  ran, seconds, status, detail = parse_summary(lines)
  if not args.ephemeris:
    for line in lines:
      if line.startswith("ephemeris:"):
        args.ephemeris = line.strip()
        break

  summary = render_summary(failures, ran, seconds, status, detail, args.ephemeris)

  for failure in failures:
    print(annotation_command(failure))
  print(summary)

  summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
  if summary_path:
    try:
      with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write(summary)
    except OSError as error:
      print(f"::warning::could not write step summary: {error}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
