# שלב 9 · SRE - TaskBoard Production Readiness

📖 השיעור: [שלב 9 באתר הקורס](https://atia9.github.io/learning-devops/09-sre-operations.html) · 📁 `project-taskboard/docs/`

לא מוסיפים קוד: מוכיחים שהמערכת מוכנה לרוץ באחריות.

```bash
python3 lab.py check 9
```

| בדיקה | מה צריך | רמז |
|---|---|---|
| **9.1** | `docs/SLO.md`: SLO באחוזים (למשל 99.5%), חלון (למשל 30 ימים), ו-error budget **בדקות** - והחשבון חייב להיות נכון | 30 ימים = 43,200 דקות · 0.5% מזה = 216 דקות |
| **9.2** | `docs/RUNBOOK.md` להתראה `HighErrorRate` עם פרקים: תסמין, אבחון, מיטיגציה, הסלמה | מישהו שלא מכיר את הפרויקט צריך להצליח לפעול לפיו |
| **9.3** | `docs/POSTMORTEM.md`: ציר זמן, 5 Whys (5 שורות שמתחילות ב"למה"), ומשימות | blameless: מה בתהליך איפשר את התקלה, לא מי טעה |
| **9.4** | `project-taskboard/README.md` מקשר לשלושת המסמכים | |

**רעיון לתקלה אמיתית:** בשלב 3, אם שכחת את `DB_PATH`, הנתונים נמחקו אחרי restart. זו תקלה מצוינת ל-postmortem.
