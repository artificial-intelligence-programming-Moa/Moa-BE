from app.crawlers.base import BaseCrawler

crawler = BaseCrawler("debug")
# 텍스트 본문이 있을 법한 다른 글
soup = crawler.get_soup("https://news.khu.ac.kr/kor/user/bbs/BMSR00040/view.do?menuNo=200318&boardId=321887")

if soup:
    area = soup.select_one("div.row.contents")
    print(area.get_text(strip=True)[:300] if area else "없음")