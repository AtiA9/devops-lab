# Health Check Monitor - notes

## Conflict
Two branches changed the same line of `health-check.sh`:
- `feat/timeout` changed `--max-time 10` to `--max-time 5`.
- `fix/quiet-curl` added `2>/dev/null` at the end of the same curl line.
`git merge` stopped with a conflict on that line. I kept both changes: the shorter timeout and the quiet output,
ran `./health-check.sh http://localhost:5000/health` again, and committed the merge.
