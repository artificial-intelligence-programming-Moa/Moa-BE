from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.article import Article
from app.schemas.article import ArticleResponse

router = APIRouter(prefix="/articles", tags=["articles"])

@router.get("/", response_model=list[ArticleResponse])
def get_articles(
    skip: int = 0,
    limit: int = 20,
    category: str = Query(None),
    source: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Article)
    
    if category:
        query = query.filter(Article.category == category)
    if source:
        query = query.filter(Article.source == source)
    
    return query.order_by(Article.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Article not found")
    return article