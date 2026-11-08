# שלב 5 · ענן - TaskBoard on AWS עם Terraform

📖 השיעור: [שלב 5 באתר הקורס](https://atia9.github.io/learning-devops/05-cloud-aws-terraform.html) · 📁 `project-taskboard/terraform/`

מעלים את ה-image משלב 4 לשרת EC2 אמיתי, כשכל התשתית כתובה כקוד.

```bash
python3 lab.py check 5
```

| בדיקה | מה צריך | רמז |
|---|---|---|
| **5.1** | `provider "aws"`, `aws_instance` מסוג `t2.micro` או `t3.micro`, ו-`user_data` שמריץ `docker run` כשהשרת עולה | `templatefile("user_data.sh", { image = var.image })` |
| **5.2** | security group: פורט 5000 פתוח, SSH (22) **רק** מה-IP שלך | `cidr_blocks = [var.my_ip_cidr]` עם `/32` · `curl -s ifconfig.me` |
| **5.3** | state מרוחק: `backend "s3"` | יוצרים את ה-bucket פעם אחת ידנית |
| **5.4** | אין מפתחות AWS בקוד, ו-`.terraform/` ו-`*.tfstate` ב-`.gitignore` | `aws configure` שומר מפתחות מחוץ לריפו |
| **5.5** | `output` עם ה-`public_ip` | `terraform output public_ip` |
| **5.6** | `terraform fmt` ו-`terraform validate` עוברים | `terraform fmt` מתקן את העיצוב לבד |

⚠️ **כסף:** t2/t3.micro נכנס ל-free tier, אבל תמיד סיים עם `terraform destroy`.
