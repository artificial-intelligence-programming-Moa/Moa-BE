"""
DB의 모든 articles를 현재 LLMAPI.summarize_notice 로 재요약하는 스크립트.
"""
import sys
import io
import os
import time

# Windows cp949 콘솔에서 유니코드(이모지 등) 인코딩 오류 방지
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# LLMAPI.py가 os.getenv를 사용하므로 .env를 먼저 로드
from dotenv import load_dotenv
load_dotenv()
from app.core.database import SessionLocal
from app.models.article import Article
from LLMAPI import summarize_notice

_CATEGORY_KO = {
    "scholarship": "장학",
    "academic":    "학사",
    "job":         "취업",
    "event":       "행사",
    "program":     "프로그램",
    "other":       "기타",
}

DELAY_SECONDS = 0.5  # API rate-limit 여유


def resummary_all(dry_run: bool = False) -> None:
    db = SessionLocal()
    try:
        articles = db.query(Article).all()
        total = len(articles)
        print(f"총 {total}개 기사 재요약 시작")
        if dry_run:
            print("[dry-run] DB 저장 없이 출력만 합니다.")

        updated = 0
        failed  = 0
        for i, article in enumerate(articles, 1):
            category_ko = _CATEGORY_KO.get(article.category or "other", "기타")
            print(f"[{i}/{total}] [{category_ko}] {article.title[:50]}...")

            new_summary = summarize_notice(
                {"title": article.title, "content": article.content},
                category=category_ko,
            )

            if new_summary:
                if not dry_run:
                    article.summary = new_summary
                updated += 1
                print(f"  → 요약 완료")
            else:
                failed += 1
                print(f"  → 요약 실패, 기존 값 유지")

            time.sleep(DELAY_SECONDS)

        if not dry_run:
            db.commit()
            print(f"\n완료: {updated}개 갱신, {failed}개 실패")
        else:
            print(f"\n[dry-run] {updated}개 성공 예상, {failed}개 실패 예상")

    except Exception as e:
        db.rollback()
        print(f"오류 발생, rollback: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    resummary_all(dry_run=dry)
