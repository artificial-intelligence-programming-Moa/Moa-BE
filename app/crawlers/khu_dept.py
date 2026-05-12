import re
from .base import BaseCrawler, Notice

class KhuDeptCrawler(BaseCrawler):
    """
    컴퓨터공학부 / 소프트웨어융합학과 공용 크롤러
    목록: table tr → 제목 a 태그 (onclick="javascript:fnView('nttId')")
    상세: /view.do?nttId=NNN&menuNo=NNN
    """

    def __init__(self, source_name: str, list_url: str, base_url: str, menu_no: str):
        super().__init__(source_name)
        self.list_url = list_url
        self.base_url = base_url
        self.menu_no = menu_no

    def get_list(self, page: int = 1) -> list[Notice]:
        url = f"{self.list_url}&pageIndex={page}"
        soup = self.get_soup(url)
        if not soup:
            return []

        notices = []
        for a in soup.find_all("a"):
            href = a.get("href", "")
            # javascript:view('nttId') 형태
            match = re.search(r"javascript:view\('(\d+)'\)", href)
            if not match:
                continue

            title = a.get_text(strip=True)
            if not title:
                continue

            ntt_id = match.group(1)
            detail_url = f"{self.base_url}/view.do?nttId={ntt_id}&menuNo={self.menu_no}"

            # 날짜: 부모 tr의 마지막 td
            tr = a.find_parent("tr")
            tds = tr.find_all("td") if tr else []
            date = tds[-1].get_text(strip=True) if tds else ""

            notices.append(Notice(
                title=title,
                content="",
                url=detail_url,
                date=date,
                source=self.source_name,
            ))

        return notices

    def get_content(self, url: str) -> str:
    # 목록 페이지 먼저 방문해서 세션 확보
        self.get_soup(self.list_url)
    
        soup = self.get_soup(url)
        if not soup:
            return ""
    
        # 에러 페이지 감지
        if "게시글에 대한 정보가 없습니다" in soup.get_text():
            return ""
    
        area = (
            soup.select_one(".bbs_content")
            or soup.select_one(".view_content")
            or soup.select_one(".bbsV_cont")
            or soup.select_one("#cont")
    )
        return area.get_text(separator="\n", strip=True) if area else ""


def make_ce_crawler() -> KhuDeptCrawler:
    """컴퓨터공학부 학사/장학"""
    return KhuDeptCrawler(
        source_name="컴퓨터공학부",
        list_url="https://software.khu.ac.kr/ce25/user/bbs/BMSR00040/list.do?menuNo=21600019",
        base_url="https://software.khu.ac.kr/ce25/user/bbs/BMSR00040",
        menu_no="21600019",
    )

def make_swcon_crawler() -> KhuDeptCrawler:
    """소프트웨어융합학과 학사/장학"""
    return KhuDeptCrawler(
        source_name="소프트웨어융합학과",
        list_url="https://swcon.khu.ac.kr/swcon/user/bbs/BMSR00040/list.do?menuNo=21300017",
        base_url="https://swcon.khu.ac.kr/swcon/user/bbs/BMSR00040",
        menu_no="21300017",
    )