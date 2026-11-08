# שלב 3 · רשתות ו-Docker - Dockerize את TaskBoard

📖 השיעור: [שלב 3 באתר הקורס](https://atia9.github.io/learning-devops/03-networking-docker.html) · 📁 עובדים ב-`project-taskboard/`

ה-API כבר כתוב ועובד (`app/app.py`, עם טסטים). אתה עוטף אותו ב-Docker.

```bash
python3 lab.py check 3          # בדיקת הקבצים
python3 lab.py check 3 --live   # גם בונה ומריץ באמת (צריך Docker)
```

| בדיקה | מה צריך | רמז |
|---|---|---|
| **3.1** | `Dockerfile`: `FROM python:3.12-slim`, קודם `COPY requirements.txt` ו-`RUN pip install --no-cache-dir`, ורק אז `COPY . .`, `EXPOSE 5000`, והרצה עם gunicorn | `CMD ["gunicorn", "-b", "0.0.0.0:5000", "app.app:app"]` · הסדר הזה הוא מה שמאפשר cache |
| **3.2** | `.dockerignore` עם `.git`, `__pycache__`, `*.db`, `.venv` | פחות קבצים = image קטן ובנייה מהירה |
| **3.3** | `docker-compose.yml`: שירות עם `build: .`, `ports: ["5000:5000"]`, volume שממופה ל-`/data`, ו-`DB_PATH=/data/taskboard.db` | בלי volume, ה-SQLite נמחק עם ה-container |
| **3.4** | עם `--live`: הבודק בונה, מריץ, כותב משימה, עושה `down` ו-`up`, ובודק שהמשימה נשארה | אם נכשל: `docker compose logs` |
| **3.5** | ב-`project-taskboard/NOTES.md`: אילו שכבות הגיעו מה-cache בבנייה השנייה | בנה פעמיים עם שינוי קטן בקוד וחפש `CACHED` בפלט |

**לנסות:** `docker compose up --build`, ובטרמינל אחר `curl localhost:5000/health`.
