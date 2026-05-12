from app.core.database import SessionLocal, engine
from app.models.article import Base, Article
from app.services.pipeline_service import run_pipeline

# 테이블 생성
Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    run_pipeline(db)
    
    # 저장 확인
    articles = db.query(Article).all()
    print(f"\n✅ 저장된 글 수: {len(articles)}")
    for a in articles[:3]:
        print(f"  [{a.id}] {a.title[:50]}")
        print(f"        {a.url}")
finally:
    db.close()