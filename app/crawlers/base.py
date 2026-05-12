import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional
import time

@dataclass
class Notice:
    title: str
    content: str
    url: str
    date: str
    source: str  # 어느 사이트에서 왔는지

class BaseCrawler:
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        try:
            res = self.session.get(url, timeout=10)
            res.raise_for_status()
            res.encoding = res.apparent_encoding
            return BeautifulSoup(res.text, "html.parser")
        except Exception as e:
            print(f"[{self.source_name}] 요청 실패: {url} → {e}")
            return None

    def get_list(self, page: int = 1) -> list[Notice]:
        raise NotImplementedError

    def get_content(self, url: str) -> str:
        raise NotImplementedError

    def crawl(self, pages: int = 3) -> list[Notice]:
        notices = []
        for page in range(1, pages + 1):
            print(f"[{self.source_name}] 페이지 {page} 크롤링 중...")
            page_notices = self.get_list(page)
            for notice in page_notices:
                content = self.get_content(notice.url)
                notice.content = content
                notices.append(notice)
                time.sleep(0.5)  # 서버 부하 방지
            time.sleep(1)
        print(f"[{self.source_name}] 총 {len(notices)}개 수집 완료")
        return notices