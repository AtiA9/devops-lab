# מעבדת DevOps 🛠️

המעבדה המעשית של [מסלול DevOps](https://atia9.github.io/learning-devops/). בכל שלב קוראים את השיעור באתר, בונים את הפרויקט כאן, ו-`lab.py` בודק אוטומטית מה עובד ומה חסר, עם רמז לכל בדיקה שנכשלת.

שני פרויקטים, כמו בקורס:
- **Health Check Monitor** (שלבים 1–2): כלי ניטור ב-Bash ו-Python, ותהליך עבודה מקצועי ב-Git.
- **TaskBoard** (שלבים 3–9): API קטן שכבר כתוב ועובד. אתה לוקח אותו מקוד ועד production: Docker, CI/CD, AWS, Kubernetes, ניטור, אבטחה ו-SRE.

## להתחיל (WSL / לינוקס)

```bash
git clone https://github.com/AtiA9/devops-lab.git
cd devops-lab
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-lab.txt
python3 lab.py            # ההתקדמות בכל השלבים
python3 lab.py check 1    # כל הבדיקות של שלב 1, עם רמזים
```

## השלבים

| שלב | נושא | השיעור | איפה עובדים | ההסבר |
|---|---|---|---|---|
| 1 | לינוקס ושורת פקודה | [01](https://atia9.github.io/learning-devops/01-linux-basics.html) | `health-check-monitor/` | [stages/01-linux.md](stages/01-linux.md) |
| 2 | Git ו-GitHub | [02](https://atia9.github.io/learning-devops/02-git-github.html) | `health-check-monitor/` + `.github/workflows/` | [stages/02-git.md](stages/02-git.md) |
| 3 | Docker | [03](https://atia9.github.io/learning-devops/03-networking-docker.html) | `project-taskboard/` | [stages/03-docker.md](stages/03-docker.md) |
| 4 | CI/CD | [04](https://atia9.github.io/learning-devops/04-cicd.html) | `.github/workflows/` | [stages/04-cicd.md](stages/04-cicd.md) |
| 5 | AWS + Terraform | [05](https://atia9.github.io/learning-devops/05-cloud-aws-terraform.html) | `project-taskboard/terraform/` | [stages/05-cloud.md](stages/05-cloud.md) |
| 6 | Kubernetes | [06](https://atia9.github.io/learning-devops/06-kubernetes.html) | `project-taskboard/k8s/` | [stages/06-kubernetes.md](stages/06-kubernetes.md) |
| 7 | Observability | [07](https://atia9.github.io/learning-devops/07-observability-interview-prep.html) | `project-taskboard/observability/` | [stages/07-observability.md](stages/07-observability.md) |
| 8 | DevSecOps | [08](https://atia9.github.io/learning-devops/08-devsecops.html) | `project-taskboard/` + pipeline | [stages/08-devsecops.md](stages/08-devsecops.md) |
| 9 | SRE | [09](https://atia9.github.io/learning-devops/09-sre-operations.html) | `project-taskboard/docs/` | [stages/09-sre.md](stages/09-sre.md) |

שלב 10 (SwarmOps) הוא פרויקט חדש שבונים מאפס, על בסיס כל מה שתרגלת כאן.

## איך הבודק עובד

כל בדיקה מקבלת מספר (למשל `3.2`), וההסבר המלא שלה בעברית נמצא בקובץ השלב ב-`stages/`.

| סימון | פירוש |
|---|---|
| `PASS` | עובד |
| `FAIL` | עוד לא. מתחת מופיע רמז מה חסר |
| `SKIP` | חסר כלי במחשב (למשל terraform), או צריך להריץ עם `--live` |
| `YOU` | בדיקה ידנית: משהו שרק אתה יכול לראות, למשל pipeline ירוק ב-GitHub |

- `python3 lab.py check 3 --live` גם בונה ומריץ את ה-containers באמת.
- בכל push, ה-workflow `lab-progress` מציג טבלת התקדמות בטאב **Actions** (פותחים את ההרצה ← Summary).
- הבודק רק קורא את הקבצים שלך, הוא לא משנה כלום. אל תשנה את `lab.py`.

הפלט של הבודק באנגלית, כי טרמינל של Windows/WSL מציג עברית הפוך.

## חוקי העבודה
- משלב 2 והלאה: כל שינוי ב-branch משלו, ונכנס ל-`main` רק דרך Pull Request.
- כל commit לפי [Conventional Commits](https://www.conventionalcommits.org/): `feat: …`, `fix: …`, `docs: …`.
- סודות (סיסמאות, מפתחות AWS, טוקנים) לא נכנסים לריפו אף פעם.

## נתקעת?
1. קרא את הרמז ב-`FAIL`, ואת ההסבר בקובץ השלב.
2. רק אחרי שניסית: בענף `solutions` יש פתרון לדוגמה לכל שלב, שכל הבדיקות עוברות עליו:
   ```bash
   git fetch origin solutions
   git diff main origin/solutions -- project-taskboard/Dockerfile
   ```
