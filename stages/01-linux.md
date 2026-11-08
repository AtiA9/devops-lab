# שלב 1 · לינוקס ושורת פקודה - Health Check Monitor

📖 השיעור: [שלב 1 באתר הקורס](https://atia9.github.io/learning-devops/01-linux-basics.html) · 📁 עובדים ב-`health-check-monitor/`

כלי ניטור קטן ב-Bash ו-Python: בודק דיסק, בודק שהשירות עונה, מסכם לוגים, ורץ לבד כל 5 דקות.

```bash
python3 lab.py check 1
```

| בדיקה | מה צריך | רמז |
|---|---|---|
| **1.1** | `disk-alert.sh` מתחיל ב-`#!/bin/bash`, יש בו `set -euo pipefail`, ויש לו הרשאת הרצה | `chmod +x disk-alert.sh` |
| **1.2** | מעל `THRESHOLD` (ברירת מחדל 80) מדפיס `[timestamp] WARNING: disk usage is N%` ויוצא עם 1, אחרת `OK` ו-0 | `df --output=pcent / \| tail -1 \| tr -d ' %'`, `THRESHOLD=${THRESHOLD:-80}`, `date '+%Y-%m-%d %H:%M:%S'` |
| **1.3** | `health-check.sh URL`: בלי URL - הודעת שימוש ל-stderr ויציאה 64. תשובה 2xx תוך 5 שניות - `UP` ו-0. אחרת (גם 404 וגם פורט סגור) - `DOWN` ו-2 | `curl -fsS --max-time 5 -o /dev/null "$URL"` · הדגל `-f` הופך 4xx/5xx לכישלון |
| **1.4** | `log-report.py samples/access.log` מדפיס בדיוק 4 שורות: `total=`, `errors_5xx=`, `error_rate=…%` (ספרה אחת אחרי הנקודה), `top_path=… (N)`. קובץ חסר - יציאה 1 | `line.split('"')` נותן את הבקשה ואת הסטטוס · `collections.Counter` |
| **1.5** | `shellcheck` עובר על שני הסקריפטים בלי אזהרות | `sudo apt install shellcheck` · כמעט תמיד הפתרון הוא מרכאות סביב משתנים |
| **1.6** | ב-`crontab.txt` שורה שמריצה את `health-check.sh` כל 5 דקות ומוסיפה ל-`/var/log/health-check.log` | `*/5 * * * *` · `>> קובץ 2>&1` |
| **1.7** | `health-check.service` (`Type=oneshot`, `ExecStart=`) ו-`health-check.timer` (`OnUnitActiveSec=` או `OnCalendar=`, `WantedBy=timers.target`) | cron ו-systemd timer הם שתי דרכים לאותו דבר - הבוחן ישאל מה ההבדל |

**לנסות על המחשב:** `THRESHOLD=0 ./disk-alert.sh; echo $?` צריך להדפיס WARNING ו-1.
