from app.crawlers.goodjob import GoodjobCrawler
from app.crawlers.swedu import SweduCrawler
from app.crawlers.khu_main import make_khu_haksa_crawler, make_khu_janghak_crawler

crawlers = [
    GoodjobCrawler(),
    SweduCrawler(),
    make_khu_haksa_crawler(),
    make_khu_janghak_crawler(),
]

for crawler in crawlers:
    notices = crawler.crawl(pages=1)
    print(f"✅ {crawler.source_name}: {len(notices)}개")
    if notices:
        n = notices[0]
        print(f"  제목: {n.title}")
        print(f"  내용: {n.content[:50]!r}")
    print()