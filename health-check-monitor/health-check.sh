#!/bin/bash
# Stage 1 - health-check.sh URL
# Check that a web service answers.
#   - usage: ./health-check.sh http://localhost:5000/health
#   - no URL given: print a usage line to stderr and exit 64
#   - the URL answers with 2xx within 5 seconds: print "[timestamp] UP URL" and exit 0
#   - otherwise:                                  print "[timestamp] DOWN URL" and exit 2
# Full task and hints: stages/01-linux.md
echo "TODO: implement health-check.sh (see stages/01-linux.md)"
exit 3
