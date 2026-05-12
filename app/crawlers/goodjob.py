from .base import BaseCrawler, Notice

class GoodjobCrawler(BaseCrawler):
    BASE_URL = "https://goodjob.khu.ac.kr"
    LIST_URL = "https://goodjob.khu.ac.kr/bbs/board.php?bo_table=s4_1"

    def __init__(self):
        super().__init__("미래인재센터")

    def get_list(self, page: int = 1) -> list[Notice]:
        url = f"{self.LIST_URL}&page={page}"
        soup = self.get_soup(url)
        if not soup:
            return []

        notices = []
        for a in soup.select("div.col_subject a[href*='wr_id']"):
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if not title:
                continue

            row = a.find_parent(class_="div_tb_tr")
            date_div = row.select_one(".col_date") if row else None
            date = date_div.get_text(strip=True) if date_div else ""

            notices.append(Notice(
                title=title,
                content="",
                url=href,
                date=date,
                source=self.source_name,
            ))

        return notices

    def get_content(self, url: str) -> str:
        soup = self.get_soup(url)
        if not soup:
            return ""
        area = soup.select_one("#bo_v_con") or soup.select_one(".view_content")
        return area.get_text(separator="\n", strip=True) if area else ""