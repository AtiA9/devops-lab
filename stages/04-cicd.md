# שלב 4 · CI/CD אמיתי - TaskBoard Pipeline

📖 השיעור: [שלב 4 באתר הקורס](https://atia9.github.io/learning-devops/04-cicd.html) · 📁 `.github/workflows/` בשורש הריפו

pipeline שרץ לבד: טסטים → בניית image → דחיפה ל-registry, רק אם כל מה שלפני עבר.

```bash
python3 lab.py check 4
```

| בדיקה | מה צריך | רמז |
|---|---|---|
| **4.1** | workflow שרץ על `push` ו-`pull_request` ל-`main` | `branches: [main]` |
| **4.2** | job בשם `test` שמתקין את `requirements-dev.txt` ומריץ `pytest` בתוך `project-taskboard` | `defaults: run: working-directory: project-taskboard` |
| **4.3** | job בשם `build` עם `needs: test`, ו-job בשם `push` עם `needs: build` | `needs` הוא מה שהופך jobs מקבילים לשרשרת |
| **4.4** | `push` רץ רק מ-main (`if:`), מתחבר ל-registry עם `secrets.*`, והתג של ה-image הוא `${{ github.sha }}` | ל-GHCR מספיק `secrets.GITHUB_TOKEN` עם `permissions: packages: write` · שם ה-image חייב אותיות קטנות |
| **4.5** | 👤 ה-pipeline ירוק בטאב Actions | jobs שעוברים ב-build אבל לא נדחפים מ-PR - זה תקין |

**הנקודה החשובה:** GitHub קורא workflows **רק** מ-`.github/workflows/` בשורש הריפו. קובץ בתוך `project-taskboard/.github` פשוט לא ירוץ, בלי שום שגיאה.
