#!/usr/bin/env python3
"""lab.py - automatic checker for the DevOps lab.

    python3 lab.py                 progress of every stage
    python3 lab.py check 3         every check of stage 3, with a hint for each one that fails
    python3 lab.py check 3 --live  stage 3 also builds and runs the containers (needs Docker)
    python3 lab.py --summary       Markdown progress table (used by GitHub Actions)

Every check has a number (e.g. 3.2). The Hebrew explanation of each number is in stages/.
The checker never changes your files.
"""
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from collections import Counter
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

try:
    import yaml
except ImportError:  # the checks that need YAML report it instead of crashing
    yaml = None

ROOT = Path(__file__).resolve().parent
HCM = ROOT / "health-check-monitor"
TB = ROOT / "project-taskboard"
WORKFLOWS = ROOT / ".github" / "workflows"
LAB_WORKFLOW = "lab-progress.yml"
LIVE = "--live" in sys.argv

PASS, FAIL, SKIP, MANUAL = "pass", "fail", "skip", "manual"


# ---------------------------------------------------------------- helpers
def read(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def run(cmd, timeout=30, env=None, cwd=None, inp=None):
    """Runs a command; returns (exit code, stdout+stderr). Never raises."""
    full_env = dict(os.environ)
    full_env.update(env or {})
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           env=full_env, cwd=cwd, input=inp)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "timed out after %ss" % timeout
    except OSError as e:
        return 127, str(e)


def yaml_docs(path):
    if yaml is None:
        raise RuntimeError("PyYAML is not installed: pip install -r requirements-lab.txt")
    text = read(path)
    if text is None:
        return []
    return [d for d in yaml.safe_load_all(text) if d is not None]


def need_yaml():
    return (SKIP, "PyYAML is not installed - run: pip install -r requirements-lab.txt") if yaml is None else None


def git(*args):
    return run(["git", "-C", str(ROOT)] + list(args))


def student_workflows():
    """The student's workflow files (everything except the lab's own progress workflow)."""
    out = []
    if WORKFLOWS.is_dir():
        for f in sorted(WORKFLOWS.iterdir()):
            if f.suffix in (".yml", ".yaml") and f.name != LAB_WORKFLOW:
                try:
                    doc = (yaml_docs(f) or [None])[0]
                except Exception:
                    doc = None
                if isinstance(doc, dict):
                    out.append((f, doc))
    return out


def triggers(wf):
    # YAML 1.1 reads the key "on" as True
    on = wf.get("on", wf.get(True))
    if isinstance(on, str):
        return {on: None}
    if isinstance(on, list):
        return {k: None for k in on}
    return on if isinstance(on, dict) else {}


def steps_text(job):
    parts = []
    for s in job.get("steps", []) or []:
        if isinstance(s, dict):
            parts.append(json.dumps(s))
    return "\n".join(parts)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


TS = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?")


# ---------------------------------------------------------------- stage 1: linux
def s1_disk_header():
    f = HCM / "disk-alert.sh"
    text = read(f)
    if text is None:
        return FAIL, "health-check-monitor/disk-alert.sh is missing"
    if not text.startswith("#!/bin/bash") and not text.startswith("#!/usr/bin/env bash"):
        return FAIL, "first line must be the shebang #!/bin/bash"
    if not re.search(r"^\s*set -euo pipefail", text, re.M):
        return FAIL, "add 'set -euo pipefail' near the top"
    if not os.access(f, os.X_OK):
        return FAIL, "not executable - run: chmod +x health-check-monitor/disk-alert.sh"
    return PASS, ""


def s1_disk_behaviour():
    f = HCM / "disk-alert.sh"
    if not f.exists():
        return FAIL, "disk-alert.sh is missing"
    rc, out = run(["bash", str(f)], env={"THRESHOLD": "0"})
    if rc != 1 or "WARNING" not in out or not TS.search(out):
        return FAIL, "with THRESHOLD=0 expected exit 1 and '[timestamp] WARNING: ...' (got exit %d: %s)" % (rc, out.strip()[:80])
    rc, out = run(["bash", str(f)], env={"THRESHOLD": "100"})
    if rc != 0 or "OK" not in out or not TS.search(out):
        return FAIL, "with THRESHOLD=100 expected exit 0 and '[timestamp] OK: ...' (got exit %d: %s)" % (rc, out.strip()[:80])
    if not re.search(r"\d+%", out):
        return FAIL, "print the usage as a percent, e.g. 'disk usage is 42%'"
    return PASS, ""


class _Ok(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200 if self.path == "/health" else 404)
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def log_message(self, *a):
        pass


def s1_health_check():
    f = HCM / "health-check.sh"
    if not f.exists():
        return FAIL, "health-check.sh is missing"
    rc, _ = run(["bash", str(f)])
    if rc != 64:
        return FAIL, "without a URL expected exit 64 (got %d)" % rc
    port = free_port()
    server = HTTPServer(("127.0.0.1", port), _Ok)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = "http://127.0.0.1:%d/health" % port
        rc, out = run(["bash", str(f), url], timeout=20)
        if rc != 0 or "UP" not in out:
            return FAIL, "a healthy URL should print '[timestamp] UP URL' and exit 0 (got exit %d: %s)" % (rc, out.strip()[:80])
        rc, out = run(["bash", str(f), "http://127.0.0.1:%d/missing" % port], timeout=20)
        if rc != 2 or "DOWN" not in out:
            return FAIL, "a 404 should count as DOWN with exit 2 - use curl -f (got exit %d)" % rc
    finally:
        server.shutdown()
    rc, out = run(["bash", str(f), "http://127.0.0.1:%d/health" % free_port()], timeout=20)
    if rc != 2 or "DOWN" not in out:
        return FAIL, "a closed port should print DOWN and exit 2 (got exit %d)" % rc
    return PASS, ""


def expected_report(log_path):
    lines = [l for l in read(log_path).splitlines() if l.strip()]
    statuses = [int(l.split('"')[2].split()[0]) for l in lines]
    paths = [l.split('"')[1].split()[1] for l in lines]
    e5 = sum(1 for s in statuses if s >= 500)
    top, n = Counter(paths).most_common(1)[0]
    return ["total=%d" % len(lines), "errors_5xx=%d" % e5,
            "error_rate=%.1f%%" % (100.0 * e5 / len(lines)), "top_path=%s (%d)" % (top, n)]


def s1_log_report():
    f = HCM / "log-report.py"
    sample = HCM / "samples" / "access.log"
    if not f.exists():
        return FAIL, "log-report.py is missing"
    rc, out = run([sys.executable, str(f), str(sample)])
    want = expected_report(sample)
    got = [l.strip() for l in out.strip().splitlines()]
    if rc != 0 or got != want:
        return FAIL, "on samples/access.log expected exactly: %s | got (exit %d): %s" % (" / ".join(want), rc, " / ".join(got)[:120])
    rc, _ = run([sys.executable, str(f), str(HCM / "samples" / "no-such.log")])
    if rc != 1:
        return FAIL, "a missing file should exit 1 (got %d)" % rc
    return PASS, ""


def s1_shellcheck():
    if not shutil.which("shellcheck"):
        return SKIP, "shellcheck not installed - sudo apt install shellcheck (CI runs it for you)"
    files = [p for p in (HCM / "disk-alert.sh", HCM / "health-check.sh") if p.exists()]
    if len(files) < 2 or any("TODO: implement" in (read(p) or "") for p in files):
        return FAIL, "write disk-alert.sh and health-check.sh first (1.2, 1.3)"
    rc, out = run(["shellcheck"] + [str(p) for p in files])
    return (PASS, "") if rc == 0 else (FAIL, "shellcheck found problems:\n" + out.strip()[:600])


def s1_cron():
    text = read(HCM / "crontab.txt") or ""
    lines = [l for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]
    for l in lines:
        if re.match(r"^\*/5\s+\*\s+\*\s+\*\s+\*\s+\S*health-check\.sh\s+\S+.*>>\s*/var/log/health-check\.log", l):
            return PASS, ""
    return FAIL, "need a line: */5 * * * * /path/to/health-check.sh URL >> /var/log/health-check.log 2>&1"


def s1_systemd():
    svc = read(HCM / "health-check.service")
    tmr = read(HCM / "health-check.timer")
    if svc is None or tmr is None:
        return FAIL, "create health-check.service and health-check.timer in health-check-monitor/"
    if "[Service]" not in svc or not re.search(r"^Type=oneshot", svc, re.M) or not re.search(r"^ExecStart=\S*health-check\.sh", svc, re.M):
        return FAIL, "the service needs [Service], Type=oneshot and ExecStart=/path/health-check.sh URL"
    if "[Timer]" not in tmr or not re.search(r"^(OnCalendar|OnUnitActiveSec)=", tmr, re.M):
        return FAIL, "the timer needs [Timer] with OnCalendar= or OnUnitActiveSec="
    if not re.search(r"^WantedBy=timers\.target", tmr, re.M):
        return FAIL, "the timer needs [Install] WantedBy=timers.target"
    return PASS, ""


# ---------------------------------------------------------------- stage 2: git
CONVENTIONAL = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([\w./-]+\))?!?: \S")


# Lab maintenance is not your work: commits with the scope (lab), and merges of the lab's own update branches.
LAB_COMMIT = re.compile(r"^\w+\(lab\)!?: ")
LAB_MERGE = re.compile(r"claude/")


def lab_range():
    """Your commits: everything after the lab's first commit (or the lab-start tag, if it exists)."""
    rc, _ = git("rev-parse", "-q", "--verify", "refs/tags/lab-start")
    if rc == 0:
        return "lab-start..HEAD"
    rc, out = git("rev-list", "--max-parents=0", "HEAD")
    roots = out.split()
    return "%s..HEAD" % roots[-1] if rc == 0 and roots else "HEAD"


def s2_commits():
    rc, out = git("log", lab_range(), "--no-merges", "--format=%s")
    if rc != 0:
        return FAIL, "not a git repository? " + out.strip()[:100]
    subjects = [s for s in out.splitlines() if s.strip() and not LAB_COMMIT.match(s)]
    if len(subjects) < 3:
        return FAIL, "make at least 3 commits of your own (found %d)" % len(subjects)
    bad = [s for s in subjects if not CONVENTIONAL.match(s)]
    if bad:
        return FAIL, "not Conventional Commits: " + " | ".join(bad[:3])
    return PASS, "%d commits" % len(subjects)


def s2_merges():
    rc, out = git("log", lab_range(), "--merges", "--format=%s")
    merges = [s for s in out.splitlines() if s.strip() and not LAB_MERGE.search(s)]
    if len(merges) < 3:
        return FAIL, "merge at least 3 branches through Pull Requests with 'Create a merge commit' (found %d merges, then git pull)" % len(merges)
    return PASS, "%d merges" % len(merges)


def s2_workflow():
    r = need_yaml()
    if r:
        return r
    for f, wf in student_workflows():
        t = triggers(wf)
        text = read(f)
        if "push" in t and "pull_request" in t and "shellcheck" in text:
            return PASS, f.name
    if (HCM / ".github").exists():
        return FAIL, "workflows must be in .github/workflows at the ROOT of the repo, not inside health-check-monitor/"
    return FAIL, "add .github/workflows/<name>.yml that runs on push and pull_request and runs shellcheck"


def s2_conflict_notes():
    text = read(HCM / "NOTES.md") or ""
    m = re.search(r"^#+ .*(conflict|קונפליקט).*$", text, re.I | re.M)
    if not m:
        return FAIL, "add a '## Conflict' section to health-check-monitor/NOTES.md"
    body = text[m.end():].split("\n#")[0]
    if len([l for l in body.splitlines() if l.strip()]) < 3:
        return FAIL, "describe the conflict in at least 3 lines: what clashed and how you resolved it"
    return PASS, ""


def s2_protection():
    return MANUAL, "GitHub > Settings > Branches: protect main (require a PR and a passing check) - checked by you, not by the script"


# ---------------------------------------------------------------- stage 3: docker
def dockerfile():
    return read(TB / "Dockerfile")


def s3_dockerfile():
    d = dockerfile()
    if d is None:
        return FAIL, "project-taskboard/Dockerfile is missing"
    lines = [l.strip() for l in d.splitlines() if l.strip() and not l.strip().startswith("#")]
    froms = [l for l in lines if l.upper().startswith("FROM ")]
    if not froms or not re.match(r"FROM\s+python:3\.12-slim\b", froms[0], re.I):
        return FAIL, "start from python:3.12-slim"
    try:
        i_req = next(i for i, l in enumerate(lines) if re.match(r"COPY\s+requirements\.txt", l, re.I))
        i_pip = next(i for i, l in enumerate(lines) if re.match(r"RUN\s+.*pip install", l, re.I))
        i_all = next(i for i, l in enumerate(lines) if re.match(r"COPY\s+\.\s+\.", l, re.I))
    except StopIteration:
        return FAIL, "need: COPY requirements.txt ..., RUN pip install ..., COPY . ."
    if not i_req < i_pip < i_all:
        return FAIL, "order for the layer cache: COPY requirements.txt, then RUN pip install, then COPY . ."
    if "--no-cache-dir" not in lines[i_pip]:
        return FAIL, "use pip install --no-cache-dir to keep the image small"
    if not any(re.match(r"EXPOSE\s+5000\b", l, re.I) for l in lines):
        return FAIL, "add EXPOSE 5000"
    cmd = " ".join(l for l in lines if re.match(r"(CMD|ENTRYPOINT)\b", l, re.I))
    if "gunicorn" not in cmd or "0.0.0.0:5000" not in cmd or "app.app:app" not in cmd:
        return FAIL, 'run with gunicorn, e.g. CMD ["gunicorn", "-b", "0.0.0.0:5000", "app.app:app"]'
    return PASS, ""


def s3_dockerignore():
    text = read(TB / ".dockerignore")
    if text is None:
        return FAIL, "project-taskboard/.dockerignore is missing"
    need = [".git", "__pycache__", "*.db", ".venv"]
    missing = [n for n in need if n not in text]
    return (PASS, "") if not missing else (FAIL, "also ignore: " + ", ".join(missing))


def compose_doc():
    path = TB / "docker-compose.yml"
    if not path.exists():
        path = TB / "compose.yaml"
    docs = yaml_docs(path)
    return docs[0] if docs else None


def s3_compose():
    r = need_yaml()
    if r:
        return r
    c = compose_doc()
    if not isinstance(c, dict) or not isinstance(c.get("services"), dict):
        return FAIL, "project-taskboard/docker-compose.yml with a services: section is missing"
    svc = next((s for s in c["services"].values() if isinstance(s, dict) and s.get("build")), None)
    if svc is None:
        return FAIL, "a service with build: . is needed"
    ports = [str(p) for p in svc.get("ports", [])]
    if not any(p.endswith("5000:5000") for p in ports):
        return FAIL, 'publish the port: ports: ["5000:5000"]'
    vols = [str(v) for v in svc.get("volumes", [])]
    if not any(v.split(":")[1:2] == ["/data"] for v in vols if ":" in v):
        return FAIL, "mount a volume at /data so the SQLite file survives restarts"
    env = svc.get("environment", {})
    env_text = json.dumps(env)
    if "DB_PATH" not in env_text or "/data/" not in env_text:
        return FAIL, "set DB_PATH to a file inside /data (e.g. /data/taskboard.db)"
    return PASS, ""


def http(method, url, body=None, timeout=5):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode()


def wait_health(url, seconds=90):
    end = time.time() + seconds
    while time.time() < end:
        try:
            if http("GET", url)[0] == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def s3_live():
    if not LIVE:
        return SKIP, "run 'python3 lab.py check 3 --live' to build and run it for real"
    if not shutil.which("docker"):
        return SKIP, "docker is not installed here"
    dc = ["docker", "compose", "-p", "labcheck"]
    run(dc + ["down", "-v"], timeout=120, cwd=TB)
    try:
        rc, out = run(dc + ["up", "-d", "--build"], timeout=900, cwd=TB)
        if rc != 0:
            return FAIL, "docker compose up failed:\n" + out[-600:]
        if not wait_health("http://127.0.0.1:5000/health"):
            return FAIL, "the container started but /health did not answer 200 within 90s (docker compose logs)"
        http("POST", "http://127.0.0.1:5000/tasks", {"title": "survives restart"})
        run(dc + ["down"], timeout=120, cwd=TB)  # without -v: the volume must keep the data
        rc, out = run(dc + ["up", "-d"], timeout=300, cwd=TB)
        if rc != 0 or not wait_health("http://127.0.0.1:5000/health"):
            return FAIL, "could not start again after docker compose down"
        tasks = json.loads(http("GET", "http://127.0.0.1:5000/tasks")[1])
        if not any(t.get("title") == "survives restart" for t in tasks):
            return FAIL, "the task disappeared after down/up - DB_PATH is not on the volume"
        return PASS, "built, ran, and the data survived a restart"
    finally:
        run(dc + ["down", "-v"], timeout=120, cwd=TB)


def s3_cache_notes():
    text = read(TB / "NOTES.md") or ""
    if not re.search(r"cache|CACHED|קאש|מטמון", text, re.I):
        return FAIL, "document in project-taskboard/NOTES.md which layers came from the cache on a second build"
    return PASS, ""


# ---------------------------------------------------------------- stage 4: ci/cd
def pipeline():
    """The student's main pipeline: the workflow with jobs test, build and push."""
    for f, wf in student_workflows():
        jobs = wf.get("jobs") or {}
        if isinstance(jobs, dict) and {"test", "build", "push"} <= set(jobs):
            return f, wf
    return None, None


def needs(job):
    n = job.get("needs") or []
    return [n] if isinstance(n, str) else list(n)


def with_pipeline(check):
    def wrapper():
        r = need_yaml()
        if r:
            return r
        f, wf = pipeline()
        if wf is None:
            if (TB / ".github").exists():
                return FAIL, "workflows must be in .github/workflows at the ROOT of the repo, not inside project-taskboard/"
            return FAIL, "no workflow in .github/workflows with jobs named test, build and push"
        return check(f, wf)
    wrapper.__name__ = check.__name__
    return wrapper


@with_pipeline
def s4_triggers(f, wf):
    t = triggers(wf)
    if "push" not in t or "pull_request" not in t:
        return FAIL, "trigger on both push and pull_request"
    text = json.dumps(t)
    if "main" not in text:
        return FAIL, "limit the triggers to the main branch: branches: [main]"
    return PASS, f.name


@with_pipeline
def s4_test_job(f, wf):
    job = wf["jobs"]["test"]
    text = steps_text(job) + json.dumps(job.get("defaults", {})) + json.dumps(wf.get("defaults", {}))
    if "pytest" not in text:
        return FAIL, "the test job must run pytest"
    if "requirements" not in text:
        return FAIL, "the test job must install the dependencies (pip install -r requirements-dev.txt)"
    if "project-taskboard" not in text:
        return FAIL, "run the steps in project-taskboard/ (working-directory: project-taskboard)"
    return PASS, ""


@with_pipeline
def s4_chain(f, wf):
    jobs = wf["jobs"]
    if "test" not in needs(jobs["build"]):
        return FAIL, "build must wait for the tests: needs: test"
    if "build" not in needs(jobs["push"]):
        return FAIL, "push must wait for the build: needs: build"
    return PASS, ""


@with_pipeline
def s4_push(f, wf):
    job = wf["jobs"]["push"]
    text = steps_text(job)
    cond = str(job.get("if", ""))
    if "main" not in cond:
        return FAIL, "push only from main: if: github.ref == 'refs/heads/main'"
    if not re.search(r"secrets\.|GITHUB_TOKEN", text):
        return FAIL, "log in to the registry with ${{ secrets.... }} or ${{ secrets.GITHUB_TOKEN }}"
    for m in re.finditer(r'"password":\s*"([^"]*)"', text):
        if not m.group(1).startswith("${{"):
            return FAIL, "a password is written in plain text in the workflow - move it to GitHub Secrets"
    if "github.sha" not in read(f):
        return FAIL, "tag the image with the commit: ...:${{ github.sha }}"
    return PASS, ""


def s4_green():
    return MANUAL, "open the Actions tab on GitHub and see the pipeline green on main"


# ---------------------------------------------------------------- stage 5: terraform
TF = TB / "terraform"


def tf_text():
    files = sorted(TF.glob("*.tf")) if TF.is_dir() else []
    return "\n".join(read(f) or "" for f in files)


def blocks(text, kind):
    """Bodies of blocks like 'ingress {' (brace matching, good enough for HCL)."""
    out = []
    for m in re.finditer(r"\b%s\s*\{" % kind, text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        out.append(text[m.end():i - 1])
    return out


def s5_instance():
    t = tf_text()
    if not t:
        return FAIL, "put your .tf files in project-taskboard/terraform/"
    if not re.search(r'provider\s+"aws"', t):
        return FAIL, 'add provider "aws"'
    if not re.search(r'resource\s+"aws_instance"', t):
        return FAIL, 'add resource "aws_instance"'
    if not re.search(r'instance_type\s*=\s*"t[23]\.micro"', t) and not re.search(r'default\s*=\s*"t[23]\.micro"', t):
        return FAIL, "use the free tier: t2.micro or t3.micro"
    if "docker run" not in t and not (TF / "user_data.sh").exists():
        return FAIL, "user_data must start the container on boot (docker run ...)"
    if "user_data" not in t:
        return FAIL, "set user_data on the instance"
    return PASS, ""


def s5_security_group():
    t = tf_text()
    ingress = blocks(t, "ingress")
    if not ingress:
        return FAIL, "add an aws_security_group with ingress rules"
    ssh = [b for b in ingress if re.search(r"from_port\s*=\s*22\b", b)]
    api = [b for b in ingress if re.search(r"from_port\s*=\s*5000\b", b)]
    if not api:
        return FAIL, "open port 5000 for the API"
    if not ssh:
        return FAIL, "add an SSH rule (port 22) limited to your IP"
    for b in ssh:
        if "0.0.0.0/0" in b:
            return FAIL, "SSH is open to the whole internet - limit it to your IP (x.x.x.x/32) through a variable"
    return PASS, ""


def s5_backend():
    t = tf_text()
    if not re.search(r'backend\s+"s3"', t):
        return FAIL, 'keep the state remotely: terraform { backend "s3" { ... } }'
    return PASS, ""


def s5_no_secrets():
    t = tf_text()
    if not t:
        return FAIL, "put your .tf files in project-taskboard/terraform/ first"
    if re.search(r"AKIA[0-9A-Z]{16}", t) or re.search(r'(access_key|secret_key)\s*=\s*"', t):
        return FAIL, "AWS keys are written in the code - remove them and use aws configure / environment variables"
    gi = (read(TF / ".gitignore") or "") + (read(ROOT / ".gitignore") or "")
    if ".terraform" not in gi or "tfstate" not in gi:
        return FAIL, "add .terraform/ and *.tfstate* to .gitignore"
    return PASS, ""


def s5_output():
    t = tf_text()
    for b in re.finditer(r'output\s+"[^"]+"\s*\{([^}]*)\}', t):
        if "public_ip" in b.group(1) or "public_dns" in b.group(1):
            return PASS, ""
    return FAIL, "add an output with the instance's public_ip"


def s5_validate():
    if not shutil.which("terraform"):
        return SKIP, "terraform not installed here - see stages/05-cloud.md"
    if not TF.is_dir():
        return FAIL, "project-taskboard/terraform/ is missing"
    rc, out = run(["terraform", "fmt", "-check", "-recursive"], cwd=TF)
    if rc != 0:
        return FAIL, "terraform fmt found unformatted files - run: terraform fmt\n" + out.strip()[:300]
    with tempfile.TemporaryDirectory() as tmp:
        env = {"TF_DATA_DIR": tmp}
        rc, out = run(["terraform", "init", "-backend=false", "-input=false", "-no-color"], cwd=TF, env=env, timeout=300)
        if rc != 0 and re.search(r"could not connect to registry|Failed to query available provider", out):
            return SKIP, "no network access to registry.terraform.io here - run the check where terraform init works"
        if rc != 0:
            return FAIL, "terraform init failed:\n" + out[-400:]
        rc, out = run(["terraform", "validate", "-no-color"], cwd=TF, env=env, timeout=120)
    return (PASS, "") if rc == 0 else (FAIL, "terraform validate:\n" + out.strip()[-600:])


# ---------------------------------------------------------------- stage 6: kubernetes
K8S = TB / "k8s"


def k8s_objects():
    objs = []
    if K8S.is_dir():
        for f in sorted(K8S.glob("*.y*ml")):
            for d in yaml_docs(f):
                if isinstance(d, dict) and "kind" in d:
                    objs.append(d)
    return objs


def with_k8s(check):
    def wrapper():
        r = need_yaml()
        if r:
            return r
        try:
            objs = k8s_objects()
        except Exception as e:
            return FAIL, "a YAML file in k8s/ does not parse: %s" % e
        if not objs:
            return FAIL, "put your manifests in project-taskboard/k8s/"
        return check(objs)
    wrapper.__name__ = check.__name__
    return wrapper


def kind(objs, k):
    return [o for o in objs if o.get("kind") == k]


def deployment(objs):
    d = kind(objs, "Deployment")
    return d[0] if d else None


def container(dep):
    try:
        return dep["spec"]["template"]["spec"]["containers"][0]
    except (KeyError, IndexError, TypeError):
        return None


@with_k8s
def s6_namespace(objs):
    if not any(o["metadata"].get("name") == "taskboard" for o in kind(objs, "Namespace")):
        return FAIL, "add a Namespace named taskboard"
    stray = [o["kind"] for o in objs if o["kind"] != "Namespace" and (o.get("metadata") or {}).get("namespace") != "taskboard"]
    if stray:
        return FAIL, "set metadata.namespace: taskboard on: " + ", ".join(stray)
    return PASS, ""


@with_k8s
def s6_deployment(objs):
    dep = deployment(objs)
    if dep is None:
        return FAIL, "add a Deployment"
    if int(dep["spec"].get("replicas", 1)) < 2:
        return FAIL, "run more than one replica: replicas: 2"
    c = container(dep)
    image = str((c or {}).get("image", ""))
    if ":" not in image.split("/")[-1] or image.endswith(":latest"):
        return FAIL, "use the exact image tag from stage 4 (the commit sha), not :latest"
    ports = [p.get("containerPort") for p in (c or {}).get("ports", [])]
    if 5000 not in ports:
        return FAIL, "containerPort: 5000"
    return PASS, ""


@with_k8s
def s6_probes(objs):
    c = container(deployment(objs) or {}) or {}
    for p in ("readinessProbe", "livenessProbe"):
        probe = c.get(p) or {}
        if (probe.get("httpGet") or {}).get("path") != "/health":
            return FAIL, "add %s with httpGet path /health port 5000" % p
    return PASS, ""


@with_k8s
def s6_resources(objs):
    res = (container(deployment(objs) or {}) or {}).get("resources") or {}
    for part in ("requests", "limits"):
        if not {"cpu", "memory"} <= set(res.get(part) or {}):
            return FAIL, "set resources.%s for cpu and memory" % part
    return PASS, ""


@with_k8s
def s6_service(objs):
    dep = deployment(objs) or {}
    labels = ((dep.get("spec") or {}).get("template") or {}).get("metadata", {}).get("labels", {})
    svcs = kind(objs, "Service")
    if not svcs:
        return FAIL, "add a Service"
    for s in svcs:
        sel = s["spec"].get("selector") or {}
        if sel and all(labels.get(k) == v for k, v in sel.items()):
            if any(int(p.get("targetPort", p.get("port", 0))) == 5000 for p in s["spec"].get("ports", [])):
                return PASS, ""
            return FAIL, "the Service should send traffic to targetPort 5000"
    return FAIL, "the Service selector does not match the Deployment's pod labels"


@with_k8s
def s6_config(objs):
    if not kind(objs, "ConfigMap") or not kind(objs, "Secret"):
        return FAIL, "add a ConfigMap (e.g. LOG_LEVEL) and a Secret (e.g. API_KEY)"
    c = json.dumps(container(deployment(objs) or {}) or {})
    if "configMap" not in c or "secret" not in c.lower():
        return FAIL, "use both in the container (envFrom / configMapRef, secretKeyRef)"
    return PASS, ""


def s6_sqlite_notes():
    text = read(TB / "NOTES.md") or ""
    if not re.search(r"sqlite", text, re.I) or not re.search(r"replica|רפליק|העתק", text, re.I):
        return FAIL, "explain in NOTES.md why SQLite and several replicas do not fit together, and what you chose"
    return PASS, ""


# ---------------------------------------------------------------- stage 7: observability
OBS = TB / "observability"


def s7_metrics():
    sys.path.insert(0, str(TB))
    try:
        for name in [m for m in list(sys.modules) if m == "app" or m.startswith("app.")]:
            del sys.modules[name]
        from app.app import app as flask_app
    except ImportError as e:
        return FAIL, "could not import the app (%s) - pip install -r project-taskboard/requirements.txt" % e
    finally:
        sys.path.pop(0)
    with tempfile.TemporaryDirectory() as tmp:
        import app.app as mod
        mod.DB_PATH = os.path.join(tmp, "m.db")
        c = flask_app.test_client()
        c.get("/health")
        c.get("/tasks")
        r = c.get("/metrics")
        if r.status_code != 200:
            return FAIL, "GET /metrics answered %d - expose prometheus_client metrics" % r.status_code
        body = r.get_data(as_text=True)
    counters = re.findall(r"^\w+_total\{[^}]*\}", body, re.M)
    if not any(re.search(r"(endpoint|path|handler)=", c) and re.search(r"(status|code)=", c) for c in counters):
        return FAIL, "a Counter of requests with labels endpoint and status is needed (e.g. http_requests_total)"
    if not re.search(r"^\w+_bucket\{", body, re.M):
        return FAIL, "a Histogram of response time is needed (for p95/p99)"
    return PASS, ""


def s7_prometheus():
    r = need_yaml()
    if r:
        return r
    docs = yaml_docs(OBS / "prometheus.yml")
    if not docs:
        return FAIL, "project-taskboard/observability/prometheus.yml is missing"
    p = docs[0]
    jobs = p.get("scrape_configs") or []
    intervals = [str((p.get("global") or {}).get("scrape_interval", ""))] + [str(j.get("scrape_interval", "")) for j in jobs]
    if "15s" not in intervals:
        return FAIL, "scrape every 15s (scrape_interval: 15s)"
    targets = json.dumps(jobs)
    if ":5000" not in targets:
        return FAIL, "scrape the API on port 5000 (targets: ['taskboard:5000'])"
    if not p.get("rule_files"):
        return FAIL, "load the alert rules: rule_files: [alerts.yml]"
    return PASS, ""


def s7_alert():
    r = need_yaml()
    if r:
        return r
    for f in sorted(OBS.glob("*.y*ml")) if OBS.is_dir() else []:
        for d in yaml_docs(f):
            for g in (d or {}).get("groups", []) if isinstance(d, dict) else []:
                for rule in g.get("rules", []):
                    if rule.get("alert") == "HighErrorRate":
                        expr = str(rule.get("expr", ""))
                        if "rate(" not in expr or "5.." not in expr:
                            return FAIL, "HighErrorRate should compare rate() of 5xx responses to all responses"
                        if not rule.get("for") or not (rule.get("labels") or {}).get("severity"):
                            return FAIL, "add for: and labels.severity to HighErrorRate"
                        if not (rule.get("annotations") or {}).get("summary"):
                            return FAIL, "add annotations.summary to HighErrorRate"
                        return PASS, ""
    return FAIL, "add an alert rule named HighErrorRate in observability/alerts.yml"


def s7_dashboard():
    for f in sorted(OBS.rglob("*.json")) if OBS.is_dir() else []:
        try:
            d = json.loads(read(f))
        except (ValueError, TypeError):
            continue
        panels = d.get("panels") if isinstance(d, dict) else None
        if isinstance(panels, list):
            if len(panels) < 3:
                return FAIL, "the dashboard needs at least 3 panels: throughput, error rate, latency"
            if "histogram_quantile(0.95" not in json.dumps(panels).replace(" ", ""):
                return FAIL, "the latency panel should show p95: histogram_quantile(0.95, ...)"
            return PASS, f.name
    return FAIL, "export a Grafana dashboard JSON into project-taskboard/observability/"


def s7_stack():
    r = need_yaml()
    if r:
        return r
    names = set()
    for f in [TB / "docker-compose.yml", OBS / "docker-compose.yml"]:
        for d in yaml_docs(f):
            names |= {str((s or {}).get("image", "")).split(":")[0].split("/")[-1] for s in (d.get("services") or {}).values()}
    if not {"prometheus", "grafana"} <= names:
        return FAIL, "run prometheus and grafana as containers (prom/prometheus, grafana/grafana) in docker compose"
    return PASS, ""


def s7_interview():
    return MANUAL, "the interview part (system design, stories) goes in NOTES.md - checked by you"


# ---------------------------------------------------------------- stage 8: devsecops
def s8_bandit():
    if not shutil.which("bandit"):
        return SKIP, "bandit not installed - pip install bandit (CI runs it for you)"
    rc, out = run(["bandit", "-q", "-r", str(TB / "app"), "-f", "json"], timeout=120)
    try:
        issues = json.loads(out[out.index("{"):])["results"]
    except (ValueError, KeyError):
        return FAIL, "bandit failed: " + out[:200]
    serious = [i for i in issues if i["issue_severity"] in ("HIGH", "MEDIUM")]
    if serious:
        return FAIL, "bandit: " + " | ".join("%s line %d: %s" % (i["test_id"], i["line_number"], i["issue_text"][:60]) for i in serious[:3])
    return PASS, ""


def s8_secret():
    text = read(TB / "app" / "app.py") or ""
    if "taskboard-dev-secret-123" in text:
        return FAIL, "SECRET_KEY is still written in the code - read it from the environment"
    if not re.search(r'SECRET_KEY.*os\.environ', text):
        return FAIL, "read SECRET_KEY from the environment: os.environ[\"SECRET_KEY\"]"
    return PASS, ""


@with_pipeline
def s8_trivy(f, wf):
    jobs = wf["jobs"]
    for name, job in jobs.items():
        text = steps_text(job)
        if "trivy" in text.lower():
            if "CRITICAL" not in text or not re.search(r'"exit-code":\s*"?1', text) and "--exit-code 1" not in text:
                return FAIL, "make Trivy fail the pipeline on CRITICAL: severity: CRITICAL and exit-code: '1'"
            if name != "build" and name not in needs(jobs["push"]):
                return FAIL, "the scan must run before push (in build, or in a job that push needs)"
            return PASS, ""
    return FAIL, "scan the image with Trivy (aquasecurity/trivy-action) before push"


@with_pipeline
def s8_bandit_ci(f, wf):
    if "bandit" not in read(f):
        return FAIL, "run bandit in the pipeline too"
    return PASS, ""


def s8_user():
    d = dockerfile() or ""
    users = re.findall(r"^\s*USER\s+(\S+)", d, re.M)
    if not users or users[-1] in ("root", "0"):
        return FAIL, "do not run as root: create a user and switch to it with USER"
    return PASS, ""


def s8_doc():
    text = read(TB / "SECURITY.md") or ""
    if not re.search(r"bandit", text, re.I) or not re.search(r"trivy", text, re.I):
        return FAIL, "write in project-taskboard/SECURITY.md what Bandit and Trivy found and what you did"
    return PASS, ""


# ---------------------------------------------------------------- stage 9: sre
DOCS = TB / "docs"


def s9_slo():
    text = read(DOCS / "SLO.md")
    if text is None:
        return FAIL, "project-taskboard/docs/SLO.md is missing"
    pct = [float(x) for x in re.findall(r"(\d{2}(?:\.\d+)?)\s*%", text) if 90 <= float(x) < 100]
    if not pct:
        return FAIL, "write the SLO as a percent, e.g. 99.5%"
    minutes = [float(x.replace(",", "")) for x in re.findall(r"(\d[\d,]*(?:\.\d+)?)\s*(?:minutes|min|דקות)", text, re.I)]
    if not minutes:
        return FAIL, "write the error budget in minutes for the window"
    days = re.search(r"(\d+)\s*(?:days|day|ימים|יום)", text, re.I)
    window = int(days.group(1)) if days else 30
    want = (100 - pct[0]) / 100 * window * 24 * 60
    if not any(abs(got - want) <= max(1.0, want * 0.05) for got in minutes):
        return FAIL, "the error budget for %s%% over %d days is not right - recalculate it (%s minutes in a day x days x allowed %%)" % (pct[0], window, 24 * 60)
    return PASS, "%s%% -> %.0f minutes" % (pct[0], want)


def s9_runbook():
    text = read(DOCS / "RUNBOOK.md") or ""
    parts = [("symptom", "תסמין"), ("diagnos", "אבחון"), ("mitigat", "מיטיגציה|הפחתה|טיפול"), ("escalat", "הסלמה")]
    missing = [en for en, he in parts if not re.search(r"^#+ .*(%s|%s)" % (en, he), text, re.I | re.M)]
    if not text:
        return FAIL, "project-taskboard/docs/RUNBOOK.md is missing"
    if missing:
        return FAIL, "the runbook needs sections: symptom, diagnosis, mitigation, escalation (missing: %s)" % ", ".join(missing)
    if "HighErrorRate" not in text:
        return FAIL, "the runbook should be for the HighErrorRate alert from stage 7"
    return PASS, ""


def s9_postmortem():
    text = read(DOCS / "POSTMORTEM.md") or ""
    if not text:
        return FAIL, "project-taskboard/docs/POSTMORTEM.md is missing"
    whys = len(re.findall(r"^\s*(?:\d+\.|[-*])?\s*(why|למה)\b", text, re.I | re.M))
    if whys < 5:
        return FAIL, "write 5 Whys - at least 5 lines that start with Why / למה (found %d)" % whys
    if not re.search(r"^#+ .*(timeline|ציר זמן)", text, re.I | re.M):
        return FAIL, "add a timeline section"
    if not re.search(r"^#+ .*(action items|משימות|פעולות)", text, re.I | re.M):
        return FAIL, "add action items: what changes so it does not happen again"
    return PASS, ""


def s9_links():
    text = read(TB / "README.md") or ""
    missing = [n for n in ("SLO.md", "RUNBOOK.md", "POSTMORTEM.md") if n not in text]
    return (PASS, "") if not missing else (FAIL, "link from project-taskboard/README.md to: " + ", ".join(missing))


# ---------------------------------------------------------------- the stages
STAGES = {
    1: ("Linux & shell", "01-linux.md", [
        ("disk-alert.sh: shebang, set -euo pipefail, executable", s1_disk_header),
        ("disk-alert.sh: warns above THRESHOLD, OK below", s1_disk_behaviour),
        ("health-check.sh: UP / DOWN / usage with the right exit codes", s1_health_check),
        ("log-report.py: correct report on samples/access.log", s1_log_report),
        ("shellcheck passes on both scripts", s1_shellcheck),
        ("crontab.txt: runs every 5 minutes into a log", s1_cron),
        ("systemd: health-check.service + health-check.timer", s1_systemd),
    ]),
    2: ("Git & GitHub", "02-git.md", [
        ("Conventional Commits on every commit", s2_commits),
        ("3+ branches merged through Pull Requests", s2_merges),
        ("a workflow runs shellcheck on push and PR", s2_workflow),
        ("NOTES.md documents a real conflict", s2_conflict_notes),
        ("main is a protected branch", s2_protection),
    ]),
    3: ("Docker", "03-docker.md", [
        ("Dockerfile: base image, layer order, gunicorn", s3_dockerfile),
        (".dockerignore keeps junk out of the image", s3_dockerignore),
        ("docker-compose.yml: port 5000 + volume for the database", s3_compose),
        ("live: build, run, data survives a restart", s3_live),
        ("NOTES.md: what came from the layer cache", s3_cache_notes),
    ]),
    4: ("CI/CD", "04-cicd.md", [
        ("pipeline runs on push and pull_request to main", s4_triggers),
        ("job test runs pytest", s4_test_job),
        ("test -> build -> push (needs)", s4_chain),
        ("push: only from main, secrets, tag = commit sha", s4_push),
        ("the pipeline is green on GitHub", s4_green),
    ]),
    5: ("AWS + Terraform", "05-cloud.md", [
        ("EC2 t2/t3.micro that starts the container on boot", s5_instance),
        ("security group: 5000 open, SSH only from your IP", s5_security_group),
        ("remote state in S3", s5_backend),
        ("no keys in code, state ignored by git", s5_no_secrets),
        ("output with the public IP", s5_output),
        ("terraform fmt + validate", s5_validate),
    ]),
    6: ("Kubernetes", "06-kubernetes.md", [
        ("everything in namespace taskboard", s6_namespace),
        ("Deployment: 2+ replicas, exact image tag, port 5000", s6_deployment),
        ("readiness + liveness probes on /health", s6_probes),
        ("resources: requests and limits", s6_resources),
        ("Service routes to the pods on 5000", s6_service),
        ("ConfigMap + Secret used by the container", s6_config),
        ("NOTES.md: SQLite vs. several replicas", s6_sqlite_notes),
    ]),
    7: ("Observability", "07-observability.md", [
        ("/metrics: request Counter + latency Histogram", s7_metrics),
        ("prometheus.yml scrapes the API every 15s", s7_prometheus),
        ("alert HighErrorRate", s7_alert),
        ("Grafana dashboard: 3 panels incl. p95", s7_dashboard),
        ("prometheus + grafana run in docker compose", s7_stack),
        ("interview prep written down", s7_interview),
    ]),
    8: ("DevSecOps", "08-devsecops.md", [
        ("bandit: no HIGH/MEDIUM findings in the app", s8_bandit),
        ("SECRET_KEY comes from the environment", s8_secret),
        ("Trivy scans the image before push and fails on CRITICAL", s8_trivy),
        ("bandit runs in the pipeline", s8_bandit_ci),
        ("the container does not run as root", s8_user),
        ("SECURITY.md documents the findings", s8_doc),
    ]),
    9: ("SRE", "09-sre.md", [
        ("SLO.md: SLO + correct error budget", s9_slo),
        ("RUNBOOK.md for HighErrorRate", s9_runbook),
        ("POSTMORTEM.md: timeline, 5 Whys, action items", s9_postmortem),
        ("README links to all three", s9_links),
    ]),
}

ICON = {PASS: "PASS", FAIL: "FAIL", SKIP: "SKIP", MANUAL: "YOU "}
COLOR = {PASS: "\033[32m", FAIL: "\033[31m", SKIP: "\033[33m", MANUAL: "\033[36m"}


def evaluate(stage):
    results = []
    for i, (title, fn) in enumerate(STAGES[stage][2], 1):
        try:
            status, detail = fn()
        except Exception as e:  # a bug in the student's file must never crash the checker
            status, detail = FAIL, "%s: %s" % (type(e).__name__, e)
        results.append(("%d.%d" % (stage, i), title, status, detail))
    return results


def paint(text, status):
    if not sys.stdout.isatty():
        return text
    return COLOR[status] + text + "\033[0m"


def cmd_check(stage):
    name, doc, _ = STAGES[stage]
    print("Stage %d - %s   (explanations in Hebrew: stages/%s)\n" % (stage, name, doc))
    results = evaluate(stage)
    for cid, title, status, detail in results:
        print("  %s  %-5s %s" % (paint("[%s]" % ICON[status], status), cid, title))
        if detail and status != PASS:
            for line in detail.splitlines():
                print("               -> " + line)
    done = sum(1 for r in results if r[2] == PASS)
    auto = sum(1 for r in results if r[2] in (PASS, FAIL))
    print("\n  %d/%d automatic checks pass" % (done, auto))
    return 0 if all(r[2] != FAIL for r in results) else 1


def progress():
    rows = []
    for stage, (name, doc, _) in STAGES.items():
        results = evaluate(stage)
        done = sum(1 for r in results if r[2] == PASS)
        auto = sum(1 for r in results if r[2] in (PASS, FAIL))
        rows.append((stage, name, doc, done, auto, results))
    return rows


def cmd_status():
    print("DevOps lab - progress  (details: python3 lab.py check <stage>)\n")
    for stage, name, doc, done, auto, _ in progress():
        bar = "#" * done + "." * (auto - done)
        state = PASS if done == auto else FAIL
        print("  %s  stage %d  %-16s [%s] %d/%d" % (paint("[%s]" % ("DONE" if done == auto else "    "), state), stage, name, bar, done, auto))
    return 0


def cmd_summary():
    print("## התקדמות במעבדת DevOps\n")
    print("| שלב | נושא | בדיקות שעברו | סטטוס |\n|---|---|---|---|")
    for stage, name, doc, done, auto, results in progress():
        status = "✅" if done == auto else ("🟡" if done else "⬜")
        print("| %d | [%s](stages/%s) | %d/%d | %s |" % (stage, name, doc, done, auto, status))
    print("\nפירוט ורמזים: הרץ `python3 lab.py check <שלב>` במחשב שלך.")
    return 0


def main(argv):
    args = [a for a in argv if a != "--live"]
    if not args or args == ["status"]:
        return cmd_status()
    if args == ["--summary"]:
        return cmd_summary()
    if len(args) == 2 and args[0] == "check" and args[1].isdigit() and int(args[1]) in STAGES:
        return cmd_check(int(args[1]))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
