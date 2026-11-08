# TaskBoard API

שירות רשימת משימות קטן (Flask + SQLite) שעליו בונים את כל שלבי ה-DevOps במעבדה.

| | |
|---|---|
| הרצה מקומית | `pip install -r requirements-dev.txt && flask --app app.app run` |
| טסטים | `pytest` |
| Docker | `docker compose up --build` → http://localhost:5000/health |

## API
- `GET /health`
- `GET /tasks`, `POST /tasks {"title": "..."}`
- `PATCH /tasks/<id> {"done": true}`, `DELETE /tasks/<id>`
- `GET /metrics` (Prometheus)

## תפעול
- [SLO ותקציב שגיאות](docs/SLO.md)
- [Runbook ל-HighErrorRate](docs/RUNBOOK.md)
- [Postmortem לדוגמה](docs/POSTMORTEM.md)
- [ממצאי אבטחה](SECURITY.md)
