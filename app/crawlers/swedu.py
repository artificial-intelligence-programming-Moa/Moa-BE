from .base import BaseCrawler, Notice

class SweduCrawler(BaseCrawler):
    """경희대 SW중심대학사업단 — 그누보드"""

    BASE_URL = "https://swedu.khu.ac.kr"
    LIST_URL = "https://swedu.khu.ac.kr/bbs/board.php?bo_table=07_01"

    def __init__(self):
        super().__init__("SW중심대학사업단")

    def get_list(self, page: int = 1) -> list[Notice]:
        url = f"{self.LIST_URL}&page={page}"
        soup = self.get_soup(url)
        if not soup:
            return []

        notices = []
        # 실제 구조: table > tr > td > a[href]
        for a in soup.select("table tr td a[href]"):
            href = a.get("href", "")
            # 게시글 링크만 (wr_id 포함)
            if "wr_id" not in href:
                continue
            if not href.startswith("http"):
                href = self.BASE_URL + href

            title = a.get_text(strip=True)
            if not title:
                continue

            # 날짜: 같은 tr의 마지막 td
            tr = a.find_parent("tr")
            tds = tr.find_all("td") if tr else []
            date = tds[-1].get_text(strip=True) if tds else ""

            notices.append(Notice(
                title=title,
                content="",
                url=href,
                date=date,
                source=self.source_name,
            ))

        return notices

    def get_content(self, url: str) -> str:
        import re
        soup = self.get_soup(url)
        if not soup:
            return ""
        area = soup.select_one("#bo_v_con") or soup.select_one(".bo_content")
        if not area:
            return ""

        # <br> 태그를 개행 마커로 교체
        for br in area.find_all("br"):
            br.replace_with("\n")

        # <p> 단위로만 줄바꿈 — span 사이는 separator="" 로 붙임
        paragraphs = area.find_all("p")
        if paragraphs:
            lines = []
            for p in paragraphs:
                line = p.get_text(separator="", strip=False).strip()
                line = re.sub(r" {2,}", " ", line)
                if line:
                    lines.append(line)
            return "\n".join(lines)

        # p 태그가 없는 구조 폴백
        return area.get_text(separator="\n", strip=True)