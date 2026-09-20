"""Unit tests for the CI test-log summarizer used by the workflow.

``unittest`` writes plain text to stderr, which never reaches the checks API,
so the Checks tab and PR gutter showed only "Process completed with exit code
1" with no failing test names. ``scripts/ci_test_summary.py`` parses the log
into ``::error`` annotations and a job summary; these tests pin that parsing.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import ci_test_summary as summary  # noqa: E402

FAILING_LOG = """ephemeris: 2.10.03 (20230604) | 185 .se1 in /ephe | delta-T year 1 CE 10593.75s
test_ok (tests.test_x.T.test_ok) ... ok
test_bad (tests.test_x.T.test_bad) ... FAIL

======================================================================
FAIL: test_bad (tests.test_x.T.test_bad)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/drik-panchanga/drik-panchanga/tests/test_x.py", line 42, in test_bad
    self.assertEqual(1, 2)
AssertionError: Lists differ: [8, [15, 9, 40]] != [8, [15, 9, 38]]

----------------------------------------------------------------------
Ran 2 tests in 0.010s

FAILED (failures=1)
"""

PASSING_LOG = """ephemeris: 2.10.03 (20230604) | 185 .se1 in /ephe | delta-T year 1 CE 10593.75s
test_ok (tests.test_x.T.test_ok) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
"""

TRUNCATED_LOG = """ephemeris: 2.10.03 (20230604) | 185 .se1 in /ephe | delta-T year 1 CE 10593.75s
test_ok (tests.test_x.T.test_ok) ... ok
"""

# A CI log line carries a "<job>\t<step>\t<timestamp>Z " prefix that local runs
# do not have; the parser must strip it either way.
PREFIXED_FAILING_LOG = "\n".join("Unit tests + app smoke\tRun unit tests\t2026-09-20T20:59:40.3241337Z " + line
                                 for line in FAILING_LOG.splitlines()) + "\n"


class ParseFailuresTests(unittest.TestCase):

  def test_extracts_test_file_and_line(self):
    failures = summary.parse_failures(FAILING_LOG.splitlines())
    self.assertEqual(len(failures), 1)
    failure = failures[0]
    self.assertEqual(failure["test"], "test_bad")
    self.assertEqual(failure["kind"], "fail")
    self.assertEqual(summary.relative(failure["file"]), "tests/test_x.py")
    self.assertEqual(failure["line"], 42)
    self.assertEqual(failure["message"], "Lists differ: [8, [15, 9, 40]] != [8, [15, 9, 38]]")

  def test_strips_the_actions_log_prefix(self):
    lines = [summary.strip_log_prefix(line) for line in PREFIXED_FAILING_LOG.splitlines()]
    failures = summary.parse_failures(lines)
    self.assertEqual(len(failures), 1)
    self.assertEqual(failures[0]["test"], "test_bad")
    self.assertEqual(failures[0]["line"], 42)

  def test_no_failures_in_a_passing_log(self):
    self.assertEqual(summary.parse_failures(PASSING_LOG.splitlines()), [])

  def test_error_sections_are_reported_like_failures(self):
    log = FAILING_LOG.replace("FAIL: test_bad", "ERROR: test_bad").replace("failures=1", "errors=1")
    failures = summary.parse_failures(log.splitlines())
    self.assertEqual(len(failures), 1)
    self.assertEqual(failures[0]["kind"], "error")


class ParseSummaryTests(unittest.TestCase):

  def test_reads_counts_and_status(self):
    ran, seconds, status, detail = summary.parse_summary(FAILING_LOG.splitlines())
    self.assertEqual(ran, 2)
    self.assertEqual(seconds, "0.010")
    self.assertEqual(status, "FAILED")
    self.assertIn("failures=1", detail)

  def test_ok_status(self):
    ran, _seconds, status, _detail = summary.parse_summary(PASSING_LOG.splitlines())
    self.assertEqual(ran, 1)
    self.assertEqual(status, "OK")

  def test_truncated_log_reports_no_status(self):
    _ran, _seconds, status, _detail = summary.parse_summary(TRUNCATED_LOG.splitlines())
    self.assertIsNone(status)


class AnnotationCommandTests(unittest.TestCase):

  def test_command_is_single_line_with_location_and_title(self):
    failure = summary.parse_failures(FAILING_LOG.splitlines())[0]
    command = summary.annotation_command(failure)
    self.assertTrue(command.startswith("::error file=tests/test_x.py,line=42,title=FAIL: test_bad::"))
    self.assertNotIn("\n", command)

  def test_message_with_newline_is_flattened(self):
    failure = {"kind": "fail", "test": "t", "file": None, "line": None, "message": "a\nb"}
    self.assertNotIn("\n", summary.annotation_command(failure))


class RenderSummaryTests(unittest.TestCase):

  def test_failure_summary_lists_each_test(self):
    failures = summary.parse_failures(FAILING_LOG.splitlines())
    ran, seconds, status, detail = summary.parse_summary(FAILING_LOG.splitlines())
    text = summary.render_summary(failures, ran, seconds, status, detail, "ephemeris: x")
    self.assertIn("## Unit test failures (1 of 2)", text)
    self.assertIn("`test_bad`", text)
    self.assertIn("tests/test_x.py:42", text)
    self.assertIn("ephemeris: x", text)

  def test_pass_summary_reports_the_count(self):
    ran, seconds, status, detail = summary.parse_summary(PASSING_LOG.splitlines())
    text = summary.render_summary([], ran, seconds, status, detail, "")
    self.assertIn("## Unit tests passed (1 tests in 0.001s)", text)

  def test_truncated_log_does_not_claim_a_result(self):
    _ran, _seconds, status, _detail = summary.parse_summary(TRUNCATED_LOG.splitlines())
    text = summary.render_summary([], None, None, status, None, "")
    self.assertIn("did not report a result", text)


if __name__ == "__main__":
  unittest.main()
