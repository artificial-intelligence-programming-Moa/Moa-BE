import re
from .base import BaseCrawler, Notice

class KhuMainCrawler(BaseCrawler):
    """경희대 메인 공지사항 (학사/장학/행사 등)"""

    BASE_URL = "https://www.khu.ac.kr"
    VIEW_BASE_URL = "https://news.khu.ac.kr"

    CATEGORIES = {
        "학사": "200317",
        "장학": "200318",
    }

    def __init__(self, category: str, menu_no: str):
        super().__init__(f"경희대({category})")
        self.category = category
        self.menu_no = menu_no
        self.list_url = f"{self.BASE_URL}/kor/user/bbs/BMSR00040/list.do?menuNo={menu_no}"

    def get_list(self, page: int = 1) -> list[Notice]:
        url = f"{self.list_url}&pageIndex={page}"
        soup = self.get_soup(url)
        if not soup:
            return []

        notices = []
        for a in soup.find_all("a"):
            href = a.get("href", "")
            match = re.search(r"javascript:view\('(\d+)'", href)
            if not match:
                continue

            title = a.get_text(strip=True)
            if not title:
                continue

            board_id = match.group(1)
            detail_url = f"{self.VIEW_BASE_URL}/kor/user/bbs/BMSR00040/view.do?menuNo={self.menu_no}&boardId={board_id}"

            # 날짜: 부모 row에서 찾기
            row = a.find_parent(class_="row")
            date_el = row.select_one(".date, .dateBox") if row else None
            date = date_el.get_text(strip=True) if date_el else ""

            notices.append(Notice(
                title=title,
                content="",
                url=detail_url,
                date=date,
                source=self.source_name,
            ))

        return notices

    def get_content(self, url: str) -> str:
        soup = self.get_soup(url)
        if not soup:
            return ""
        area = soup.select_one("div.row.contents")
        return area.get_text(separator="\n", strip=True) if area else ""


def make_khu_haksa_crawler() -> KhuMainCrawler:
    return KhuMainCrawler("학사", "200317")

def make_khu_janghak_crawler() -> KhuMainCrawler:
    return KhuMainCrawler("장학", "200318")