# שלב 2 · Git ו-GitHub - Git Workflow Showcase

📖 השיעור: [שלב 2 באתר הקורס](https://atia9.github.io/learning-devops/02-git-github.html) · 📁 ממשיכים על `health-check-monitor/`

לא כותבים קוד חדש: מוכיחים תהליך עבודה של צוות. כל שינוי ב-branch, כל branch דרך Pull Request.

```bash
python3 lab.py check 2
```

| בדיקה | מה צריך | רמז |
|---|---|---|
| **2.1** | לפחות 3 commits משלך, וכולם [Conventional Commits](https://www.conventionalcommits.org/): `feat: …`, `fix: …`, `docs: …`, `ci: …` | נבדקים רק commits אחרי התג `lab-start` |
| **2.2** | לפחות 3 branches שמוזגו דרך Pull Request | ב-GitHub בוחרים **Create a merge commit**, ואחר כך `git pull` כדי שה-merge יגיע אליך |
| **2.3** | workflow ב-`.github/workflows/` (בשורש הריפו!) שרץ על `push` ו-`pull_request` ומריץ `shellcheck` | ב-runner של GitHub ‏shellcheck כבר מותקן |
| **2.4** | ב-`health-check-monitor/NOTES.md` פרק `## Conflict`: מה התנגש, ואיך פתרת (3 שורות לפחות) | צור conflict בכוונה: שתי branches שמשנות את אותה שורה ב-`health-check.sh` |
| **2.5** | 👤 בדיקה ידנית: `main` מוגן - Settings → Branches: חובה PR, חובה שה-workflow יעבור | את זה הסקריפט לא יכול לבדוק |

**הזרימה בכל שינוי:** `git switch -c feat/timeout` → שינוי → `git commit -m "feat: add a 5 second timeout"` → `git push -u origin feat/timeout` → Pull Request ב-GitHub → Merge → `git switch main && git pull`.
