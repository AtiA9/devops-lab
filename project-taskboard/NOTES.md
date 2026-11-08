# TaskBoard - notes

## Layer cache (stage 3)
בבנייה השנייה אחרי שינוי ב-`app/app.py` בלבד, השכבות `COPY requirements.txt` ו-`RUN pip install` הגיעו מה-cache (`CACHED` בפלט של `docker build`),
ורק `COPY . .` והשכבות שאחריה נבנו מחדש. לכן מעתיקים את requirements.txt לפני שאר הקוד.

## SQLite vs. replicas (stage 6)
SQLite הוא קובץ על דיסק של מכונה אחת. ב-Kubernetes עם `replicas: 2` לכל replica יש קובץ משלו (emptyDir),
ולכן כל pod רואה רשימת משימות אחרת, והנתונים נמחקים כשה-pod מת.
מה בחרתי: ללמידה זה בסדר, ותיעדתי את זה. ב-production מחליפים ל-PostgreSQL (StatefulSet או שירות מנוהל), וכל ה-replicas מדברים איתו.

## Interview prep (stage 7)
- "איך היית יודע שהשירות לא תקין לפני המשתמשים?" - שלושת המדדים: throughput, error rate, latency p95, והתראה על error rate.
- "תספר על תקלה" - docs/POSTMORTEM.md: הנתונים שנמחקו אחרי restart, ומה שיניתי בתהליך.
