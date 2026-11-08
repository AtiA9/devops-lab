# שלב 7 · Observability - מדדים, התראות ודשבורד

📖 השיעור: [שלב 7 באתר הקורס](https://atia9.github.io/learning-devops/07-observability-interview-prep.html) · 📁 `project-taskboard/observability/` ו-`app/app.py`

```bash
python3 lab.py check 7
docker compose up   # Prometheus: localhost:9090 · Grafana: localhost:3000 (admin/admin)
```

| בדיקה | מה צריך | רמז |
|---|---|---|
| **7.1** | `GET /metrics` מחזיר Counter של בקשות עם labels `endpoint` ו-`status`, ו-Histogram של זמן תגובה | `prometheus_client`: `Counter`, `Histogram`, `generate_latest` · מודדים ב-`before_request` / `after_request` · הוסף את החבילה ל-requirements.txt |
| **7.2** | `observability/prometheus.yml`: `scrape_interval: 15s`, target על פורט 5000, ו-`rule_files` | בתוך compose שם השירות הוא ה-hostname: `taskboard:5000` |
| **7.3** | התראה `HighErrorRate`: `rate()` של 5xx חלקי כל הבקשות, עם `for:`, `labels.severity` ו-`annotations.summary` | בדוק שהיא באמת נורית: עצור את ה-DB או החזר 500 בכוונה |
| **7.4** | dashboard של Grafana (JSON) עם 3 פאנלים לפחות: throughput, error rate, latency עם p95 | `histogram_quantile(0.95, sum(rate(..._bucket[5m])) by (le))` |
| **7.5** | `prometheus` ו-`grafana` רצים כ-containers ב-docker compose | `prom/prometheus`, `grafana/grafana` |
| **7.6** | 👤 חלק הראיונות (system design, סיפורי תקלות) ב-`NOTES.md` | |
