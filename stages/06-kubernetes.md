# שלב 6 · Kubernetes - TaskBoard on Kubernetes

📖 השיעור: [שלב 6 באתר הקורס](https://atia9.github.io/learning-devops/06-kubernetes.html) · 📁 `project-taskboard/k8s/`

אותו image בדיוק, הפעם על cluster (kind או minikube מספיקים).

```bash
python3 lab.py check 6
kubectl apply -f project-taskboard/k8s/ && kubectl -n taskboard get pods
```

| בדיקה | מה צריך | רמז |
|---|---|---|
| **6.1** | `Namespace` בשם `taskboard`, וכל השאר עם `metadata.namespace: taskboard` | |
| **6.2** | `Deployment` עם `replicas: 2` לפחות, image עם תג מדויק (ה-sha משלב 4, לא `:latest`), `containerPort: 5000` | `:latest` אומר "מה שיהיה" - אי אפשר לדעת מה רץ |
| **6.3** | `readinessProbe` ו-`livenessProbe` על `/health` | readiness: מתי לשלוח תעבורה. liveness: מתי להפעיל מחדש |
| **6.4** | `resources.requests` ו-`resources.limits` ל-cpu ו-memory | בלי requests ה-scheduler מנחש |
| **6.5** | `Service` שה-selector שלו תואם ל-labels של ה-pods ושולח ל-`targetPort: 5000` | `kubectl -n taskboard port-forward svc/taskboard 8080:80` |
| **6.6** | `ConfigMap` ו-`Secret`, ושני הסוגים בשימוש ב-container | `envFrom: configMapRef`, `secretKeyRef` |
| **6.7** | ב-`NOTES.md`: למה SQLite ו-2 replicas לא מסתדרים, ומה בחרת | לכל pod קובץ משלו → כל אחד רואה נתונים אחרים |
