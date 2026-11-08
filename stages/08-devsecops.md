# שלב 8 · DevSecOps - Harden TaskBoard

📖 השיעור: [שלב 8 באתר הקורס](https://atia9.github.io/learning-devops/08-devsecops.html) · 📁 `project-taskboard/` ו-`.github/workflows/`

ב-`app/app.py` יש בכוונה בעיות אבטחה. מצא אותן עם הכלים, תקן, ותעד.

```bash
pip install bandit && bandit -r project-taskboard/app
python3 lab.py check 8
```

| בדיקה | מה צריך | רמז |
|---|---|---|
| **8.1** | Bandit לא מוצא ממצאים בחומרה בינונית או גבוהה ב-`app/` | קרא כל ממצא: מה הסיכון, ומה התיקון |
| **8.2** | `SECRET_KEY` נקרא מהסביבה ולא כתוב בקוד | `os.environ.get("SECRET_KEY")` |
| **8.3** | Trivy סורק את ה-image אחרי build ולפני push, ונכשל על CRITICAL | `aquasecurity/trivy-action` עם `severity: CRITICAL` ו-`exit-code: "1"` |
| **8.4** | Bandit רץ גם ב-pipeline | `bandit -r app -ll` (ממצאים בינוניים ומעלה מכשילים) |
| **8.5** | ה-container לא רץ כ-root | `useradd` ואחריו `USER` · זכור לתת לו הרשאה על `/data` |
| **8.6** | `SECURITY.md`: מה Bandit ו-Trivy מצאו, מה תיקנת, ומה השארת ולמה | גם false positive מתעדים |
