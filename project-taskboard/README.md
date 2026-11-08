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
