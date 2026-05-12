from sqlalchemy.orm import Session
from app.models.article import Article
from app.crawlers.goodjob import GoodjobCrawler
from app.crawlers.swedu import SweduCrawler
from app.crawlers.khu_main import make_khu_haksa_crawler, make_khu_janghak_crawler

def get_all_crawlers():
    return [
        GoodjobCrawler(),
        SweduCrawler(),
        make_khu_haksa_crawler(),
        make_khu_janghak_crawler(),
    ]

def crawl_and_filter_new(db: Session) -> list:
    """모든 사이트 크롤링 후 DB에 없는 새 글만 반환"""

    # DB에 저장된 URL 목록 가져오기
    existing_urls = set(url for (url,) in db.query(Article.url).all())

    new_notices = []
    for crawler in get_all_crawlers():
        notices = crawler.crawl(pages=1)  # 1페이지만 (최신글 감지용)
        for notice in notices:
            if notice.url not in existing_urls:
                new_notices.append(notice)

    print(f"[crawler_service] 새 글 {len(new_notices)}개 감지")
    return new_notices