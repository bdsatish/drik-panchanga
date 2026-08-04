"""Configure process logging to stderr and syslog."""

import logging
import os
import sys
from logging.handlers import SysLogHandler

_CONFIGURED = False
_APP_NAME = "drik-panchanga"


def configure_logging(level=None):
  """Attach stderr + syslog handlers once (safe to call from every entrypoint).

    Stderr is skipped when ``unittest`` is already loaded so the test suite
    stays quiet; syslog still receives messages when available.
    """
  global _CONFIGURED
  if _CONFIGURED:
    return
  _CONFIGURED = True

  if level is None:
    level_name = os.environ.get("PANCHANGA_LOG_LEVEL", "ERROR").upper()
    level = getattr(logging, level_name, logging.ERROR)

  root = logging.getLogger()
  root.setLevel(level)

  formatter = logging.Formatter("%(name)s: %(levelname)s: %(message)s")

  # ``unittest discover`` imports app/CGI modules before tests run; skip
  # console there so intentional soft-fail ERROR logs do not flood stderr.
  if "unittest" not in sys.modules:
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(level)
    console.setFormatter(formatter)
    root.addHandler(console)

  syslog = None
  for address in ("/dev/log", "/var/run/syslog"):
    try:
      syslog = SysLogHandler(address=address)
      break
    except OSError:
      continue
  if syslog is None:
    try:
      syslog = SysLogHandler(address=("localhost", 514))
    except OSError:
      syslog = None
  if syslog is not None:
    syslog.setLevel(level)
    syslog.setFormatter(logging.Formatter(f"{_APP_NAME}: %(name)s: %(levelname)s: %(message)s"))
    root.addHandler(syslog)
