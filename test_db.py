from app.core.database import engine, SessionLocal
from app.models.article import Base, Article

# 테이블 생성
Base.metadata.create_all(bind=engine)
print("✅ 테이블 생성 완료")

# 연결 테스트
db = SessionLocal()
count = db.query(Article).count()
print(f"✅ DB 연결 성공 — articles 테이블 행 수: {count}")
db.close()