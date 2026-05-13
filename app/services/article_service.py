from sqlalchemy.orm import Session
from app.models.article import Article
from app.crawlers.base import Notice
from classifier import classify
from NLP import summarize_notice

# 특정 소스는 해당 카테고리 전용 크롤러 → 모델이 other로 분류할 때 소스 힌트로 보정
_SOURCE_CATEGORY_HINT: dict[str, str] = {
    "경희대(장학)": "scholarship",
}

def save_new_articles(db: Session, notices: list[Notice]) -> list[Article]:
    saved = []
    for notice in notices:
        # 1. 분류
        result = classify(notice.title, notice.content)
        probs = result["probs"]
        category = max(probs, key=probs.get)

        hint = _SOURCE_CATEGORY_HINT.get(notice.source)
        if hint and category == "other":
            category = hint

        # 2. 요약
        summary = summarize_notice(
            {"title": notice.title, "content": notice.content},
            category=category,
        )

        article = Article(
            title=notice.title,
            url=notice.url,
            content=notice.content,
            source=notice.source,
            category=category,
            summary=summary,
            published_at=None,
        )
        db.add(article)
        saved.append(article)
    db.commit()
    return saved
