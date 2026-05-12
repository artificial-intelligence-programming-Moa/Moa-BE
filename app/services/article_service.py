from sqlalchemy.orm import Session
from app.models.article import Article
from app.crawlers.base import Notice
from classifier import classify

def save_new_articles(db: Session, notices: list[Notice]) -> list[Article]:
    saved = []
    for notice in notices:
        result = classify(notice.title, notice.content)
        category = max(result["probs"], key=result["probs"].get)

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
