# Runbook - HighErrorRate

ההתראה `HighErrorRate` (observability/alerts.yml) נורית כשיותר מ-5% מהבקשות נכשלות עם 5xx במשך 5 דקות.

## תסמין (Symptom)
- Grafana: הפאנל "Error rate (5xx)" מעל 5%.
- משתמשים מקבלים שגיאה 500 ב-`/tasks`.

## אבחון (Diagnosis)
1. האם השירות בכלל עולה? `curl -i http://<host>:5000/health`
2. מה אומרים הלוגים? `docker compose logs --tail=100 taskboard` (או `kubectl -n taskboard logs deploy/taskboard`)
3. איזה endpoint נכשל? ב-Prometheus: `sum by (endpoint) (rate(http_requests_total{status=~"5.."}[5m]))`
4. האם היה deploy ב-30 הדקות האחרונות? בודקים את טאב Actions.
5. האם הדיסק מלא? `./health-check-monitor/disk-alert.sh` (SQLite נכשל כשאין מקום).

## מיטיגציה (Mitigation)
- אם היה deploy: חוזרים ל-image הקודם (ה-sha הקודם) ומריצים מחדש.
- אם הדיסק מלא: מפנים מקום, ואז `docker compose restart taskboard`.
- אם קובץ ה-DB נעול או פגום: עוצרים את השירות, מגבים את הקובץ מה-volume, ומפעילים מחדש.

## הסלמה (Escalation)
- אחרי 15 דקות בלי שיפור: מעדכנים את בעל הפרויקט.
- אם יש אובדן נתונים: עוצרים כתיבה ומתעדים הכול ל-postmortem.
