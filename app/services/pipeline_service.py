from sqlalchemy.orm import Session
from app.services.crawler_service import crawl_and_filter_new
from app.services.article_service import save_new_articles
from app.services.mail_service import send_new_article_mail

def run_pipeline(db: Session):
    print("[pipeline] 시작")

    # 1. 크롤링 + 새 글 필터링
    new_notices = crawl_and_filter_new(db)
    if not new_notices:
        print("[pipeline] 새 글 없음")
        return

    # 2. DB 저장
    saved_articles = save_new_articles(db, new_notices)

    # 3. 메일 알림 (모델 연동 전까지 미분류로 전송)
    send_new_article_mail(saved_articles)

    print(f"[pipeline] 완료 — {len(saved_articles)}개 처리")