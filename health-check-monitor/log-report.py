#!/usr/bin/env python3
"""Stage 1 - log-report.py LOGFILE: summarise a web server access log."""
import sys
from collections import Counter


def parse(line):
    """'... "GET /tasks HTTP/1.1" 500 515 ...' -> ('/tasks', 500)"""
    request, rest = line.split('"')[1], line.split('"')[2]
    return request.split()[1], int(rest.split()[0])


def main():
    if len(sys.argv) != 2:
        print("usage: log-report.py LOGFILE", file=sys.stderr)
        return 64
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            entries = [parse(line) for line in f if line.strip()]
    except OSError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1

    total = len(entries)
    errors = sum(1 for _, status in entries if status >= 500)
    top_path, top_count = Counter(path for path, _ in entries).most_common(1)[0]
    print("total=%d" % total)
    print("errors_5xx=%d" % errors)
    print("error_rate=%.1f%%" % (100.0 * errors / total))
    print("top_path=%s (%d)" % (top_path, top_count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
