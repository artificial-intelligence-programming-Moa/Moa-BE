from sqlalchemy.orm import Session
from app.models.article import Article
from app.crawlers.base import Notice
from classifier import classify

# 특정 소스는 해당 카테고리 전용 크롤러 → 모델이 other로 분류할 때 소스 힌트로 보정
_SOURCE_CATEGORY_HINT: dict[str, str] = {
    "경희대(장학)": "scholarship",
}

def save_new_articles(db: Session, notices: list[Notice]) -> list[Article]:
    saved = []
    for notice in notices:
        result = classify(notice.title, notice.content)
        probs = result["probs"]
        category = max(probs, key=probs.get)

        # 모델이 other로 분류했고 소스 힌트가 있으면 힌트 카테고리로 보정
        hint = _SOURCE_CATEGORY_HINT.get(notice.source)
        if hint and category == "other":
            category = hint

        article = Article(
            title=notice.title,
            url=notice.url,
            content=notice.content,
            source=notice.source,
            category=category,
            published_at=None,
        )
        db.add(article)
        saved.append(article)
    db.commit()
    return saved
