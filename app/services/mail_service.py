import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.models.article import Article
from app.core.config import settings

def send_new_article_mail(articles: list[Article]):
    if not articles:
        return

    body = "\n\n".join([
        f"[{a.category or '미분류'}] {a.title}\n{a.url}"
        for a in articles
    ])

    msg = MIMEMultipart()
    msg["From"] = settings.MAIL_FROM
    msg["To"] = settings.MAIL_TO
    msg["Subject"] = f"[공지 알림] 새 글 {len(articles)}개"
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)

    print(f"[mail_service] 메일 전송 완료 ({len(articles)}개)")