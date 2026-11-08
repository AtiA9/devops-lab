#!/usr/bin/env python3
"""Stage 1 - log-report.py LOGFILE

Summarise a web server access log (format: samples/access.log). Print exactly:
    total=<number of requests>
    errors_5xx=<number of 5xx responses>
    error_rate=<5xx percent, one decimal>%
    top_path=<most requested path> (<count>)
Missing file: print an error to stderr and exit 1.
Full task and hints: stages/01-linux.md
"""
import sys

print("TODO: implement log-report.py (see stages/01-linux.md)")
sys.exit(3)
