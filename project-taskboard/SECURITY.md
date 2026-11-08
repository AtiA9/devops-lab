# Security - what the scans found (stage 8)

## Bandit (קוד)
| ממצא | חומרה | מה עשיתי |
|---|---|---|
| B105 - `SECRET_KEY` כתוב בקוד | LOW | קורא מ-`os.environ`, ואם חסר נוצר ערך אקראי |
| B201 - `debug=True` | HIGH | הוסר. ב-container רץ gunicorn, לא שרת הפיתוח |
| B104 - האזנה ל-`0.0.0.0` | MEDIUM | `app.run` מקומי מאזין ל-127.0.0.1; ב-container gunicorn מאזין ל-0.0.0.0 בכוונה |

Bandit רץ ב-CI (`bandit -r app -ll`) ונכשל על ממצא בינוני ומעלה.

## Trivy (image)
Trivy סורק את ה-image אחרי build ולפני push, ונכשל על חולשה CRITICAL שיש לה תיקון.
אם הוא נכשל: מעדכנים את ה-base image (`python:3.12-slim`) או את החבילה, ובונים מחדש.

## סודות
- `SECRET_KEY` עובר כ-env (compose), כ-Secret (Kubernetes) או כ-GitHub Secret. אף פעם לא בקוד.
- למה לא Vault: לפרויקט לימודי עם סוד אחד זה מספיק. הפער: אין רוטציה אוטומטית ואין audit log.

## בסיס ה-container
ה-container רץ כמשתמש `appuser` (uid 10001), לא root.
