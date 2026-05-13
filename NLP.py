"""
MoA 프로젝트 - NLP 기반 공지 요약 모듈 (API 없는 버전, 송가현 담당)
✨필요 패키지 설치✨:
  pip install scikit-learn networkx numpy
 ✨ 사용방법 ✨ 
  from NLP import summarize_notice, summarize_batch

  summarize_notice 함수->공지 요약 함수
  summarize_batch 함수->공지 목록 일괄 요약 함수(summarize_notice()를 반복 호출하는 편의 함수)
"""

import re
import csv
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx


#-------------------------------------------------------------------------------
CATEGORY_BOOST_KEYWORDS = {
    "장학":     ["장학", "신청", "마감", "금액", "지원", "자격", "기간", "원",
                 "접수", "모집", "이수", "수료"],                          
    "학사":     ["수강", "신청", "기간", "대상", "절차", "방법", "학생", "등록",
                 "학년", "재학생", "학부"],                               
    "취업":     ["모집", "지원", "마감", "채용", "인턴", "방법", "대상", "기업",
                 "자격", "접수", "서류", "이메일"],                        
    "행사":     ["일시", "장소", "행사", "참가", "신청", "대상", "개최", "날짜",
                 "접수", "마감", "온라인", "비대면"],                      
    "프로그램": ["프로그램", "교육", "참가", "신청", "기간", "대상", "내용",
                 "자격", "모집", "학년", "재학생"],                        
    "기타":     ["공지", "안내", "신청", "기간", "방법", "대상", "중요"],
}

#-------------------------------------------------------------------------------
CATEGORY_PRIORITY_PATTERNS = {
    "장학": [
        r'\d+[,\d]*\s*원',
        r'마감|신청\s*기간|접수\s*기간|모집\s*기간|신청\s*마감|접수\s*마감',  
        r'자격|성적\s*\d+\.\d+|학점|이수|수료',                            
    ],
    "학사": [
        r'\d{1,2}[.월]\s*\d{1,2}[일]?',
        r'신청\s*방법|절차|기간|등록\s*방법',
        r'대상\s*학생|해당\s*학생|학년|재학생|학부생|대학원생',             
    ],
    "취업": [
        r'마감|접수\s*기간|지원\s*마감|모집\s*마감',                        
        r'모집\s*(인원|대상)|지원\s*자격|지원\s*가능|자격\s*요건|우대',     
        r'지원\s*방법|서류|이메일|포털|구글폼|링크|지원서|접수\s*방법',     
    ],
    "행사": [
        r'\d{1,2}[.월]\s*\d{1,2}[일]?',
        r'장소|위치|호관|캠퍼스|온라인|비대면|줌|zoom',                     
        r'참가\s*(신청|방법|대상)|신청\s*기간|접수\s*기간|마감',            
    ],
    "프로그램": [
        r'교육\s*(내용|일정|기간)',
        r'신청\s*(기간|방법)|접수\s*(기간|방법)|마감',                      
        r'참가\s*(대상|자격)|지원\s*(대상|자격)|모집\s*대상|학년|재학생',   
    ],
    "기타": [
        r'\d{1,2}[.월]\s*\d{1,2}[일]?',
        r'신청|방법|기간|대상',
    ],
}

# 종결어미 패턴
_SENTENCE_ENDING = re.compile(
    r'[다요임됩니습니까음함][\.\!\?]?$|'
    r'(바랍니다|드립니다|알립니다|합니다|됩니다|주십시오|주세요)[\.\!]?$'
)

# 불완전 문장 판별 (숫자/특수문자로 끝나는 경우)
_INCOMPLETE_ENDING = re.compile(r'[\d\.\,\:\-\*\/\\A-Za-z]$')

# 제거할 목록 마커 패턴
_LIST_MARKER = re.compile(
    r'^[\s]*[①②③④⑤⑥⑦⑧⑨⑩○●◎◆◇■□▶▷\-]+\s*|'
    r'^[\s]*\d+[\.）\)]\s+|'
    r'^[\s]*[가나다라마바사아자차카타파하][\.）\)]\s+|'
    r'^[\s]*[A-Za-z][\.）\)]\s+'
)

# 제거할 인라인 기호
_INLINE_MARKER = re.compile(r'[①②③④⑤⑥⑦⑧⑨⑩○●◎◆◇■□▶▷]')


#전처리-----------------------------------------------------------------------

def clean_text(text: str) -> str:#url제거
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def split_sentences(text: str) -> list:#공지 텍스트용 문장 분리기
    
    raw_lines = [l.strip() for l in text.split('\n') if l.strip()]

    eojeol_pattern = re.compile(r'(?<=[다요임함됩니까음습])\.\s+')
    chunks = []
    for line in raw_lines:
        line = re.sub(r'(?<!\d)(\d+\.\s+[가-힣A-Z])', r'\n\1', line)
        sub = re.split(r'\n', line)
        for s in sub:
            s = s.strip()
            if not s:
                continue
            parts = eojeol_pattern.split(s)
            chunks.extend(p.strip() for p in parts if p.strip())

    MIN_LEN = 15
    MAX_LEN = 200  # 120 -> 200: 문장 잘림 방지

    sentences = []
    buffer = ""
    for chunk in chunks:
        if not chunk:
            continue
        if len(chunk) < MIN_LEN:
            buffer = (buffer + " " + chunk).strip() if buffer else chunk
            continue
        if buffer:
            # buffer가 "장소 :", "신청기간 :" 같은 라벨이면 다음 청크에 붙임
            if buffer.rstrip().endswith((':', '：')):
                chunk = (buffer.strip() + " " + chunk)[:MAX_LEN]
            else:
                sentences.append(buffer[:MAX_LEN])
            buffer = ""
        sentences.append(chunk[:MAX_LEN])

    if buffer:
        sentences.append(buffer[:MAX_LEN])

    # 중복 제거 (순서 유지)
    seen, unique = set(), []
    for s in sentences:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    return unique


#추출 후 문장 후처리-----------------------------------------------------------------------

def fix_spacing_artifacts(sent: str) -> str:#글자 사이 공백 오류 보정
    # 숫자 바로 뒤 한국어 단위 앞 공백만 제거 (4 월, 6 일, 30 원 등)
    sent = re.sub(r'(\d)\s+(월|일|시|분|년|호|층|관|원|개|명|번)', r'\1\2', sent)
    # 연속 공백 정리
    sent = re.sub(r'\s{2,}', ' ', sent)
    return sent.strip()


def clean_extracted_sentence(sent: str) -> str:#기호/번호 제거 +정제
    
    # 1) 앞쪽 목록 마커 제거 (반복 적용으로 '- -' 같은 중첩 기호 처리)
    for _ in range(3):
        prev = sent
        sent = _LIST_MARKER.sub('', sent)
        if sent == prev:
            break
    # 2) 인라인 특수 기호 제거
    sent = _INLINE_MARKER.sub('', sent)
    # 3) 문장 앞 쓰레기 기호 제거 (콜론, 쉼표, 닫는 괄호, 점, 하이픈 등)
    sent = re.sub(r'^[\s:,·\)\]\.\-]+', '', sent)
    # 4) PDF/OCR 공백 오류 보정
    sent = fix_spacing_artifacts(sent)
    # 5) 중복 공백 정리
    sent = re.sub(r'\s+', ' ', sent).strip()
    # 6) 내부 ' - ' 구분자가 있는 복합 항목은 첫 번째 청크만 사용
    #    (예: "참가신청 - 신청기간: ... - 신청방법: ..." -> "신청기간: ...")
    if re.search(r'\s+-\s+', sent):
        parts = re.split(r'\s+-\s+', sent)
        # 가장 길고 정보가 많은 청크 선택 (날짜/기간 포함 우선)
        info_parts = [p for p in parts if re.search(r'기간|일시|장소|방법|자격|금액|\d{4}', p)]
        sent = info_parts[0] if info_parts else max(parts, key=len)
        sent = sent.strip()
    # 7) 불완전하게 끝나는 쓰레기 제거
    sent = re.sub(r'\s*[/\\\*]\s*\d+[가-힣]*\s*$', '', sent).strip()  # /12일간 등
    sent = re.sub(r'(\s*\.\s*\d+[\.\s]*)+$', '', sent).strip()          # . 4. 등
    sent = re.sub(r'\(\s*\)\s*$', '', sent).strip()                      # 빈 괄호 ( )
    sent = re.sub(r'\*\s*[A-Z]+\s*$', '', sent).strip()                  # * TOPCIT 등
    # 8) 종결어미 문장에 마침표 추가
    if sent and sent[-1] not in '.!?':
        if _SENTENCE_ENDING.search(sent):
            sent += '.'
    return sent


def is_complete_sentence(sent: str) -> bool:#완전한 문장 판단
    
    if len(sent) < 10:
        return False
    if _SENTENCE_ENDING.search(sent):
        return True
    # 날짜/금액/기간 등 핵심 정보가 있으면 부분 문장도 허용
    if re.search(r'\d+[.월일]\s*\d*|마감|기간|자격|금액|\d+[,\d]*\s*원', sent):
        return True
    return False


# ── 2단계: TF-IDF + TextRank ──────────────────────────────────────────────────

def build_similarity_matrix(sentences: list) -> np.ndarray:#TF-IDF로 벡터화+코사인 유사도 행렬 반환

    vectorizer = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(2, 4),
        min_df=1,
    )
    try:
        tfidf_matrix = vectorizer.fit_transform(sentences)
    except ValueError:
        return np.eye(len(sentences))

    sim_matrix = cosine_similarity(tfidf_matrix)
    np.fill_diagonal(sim_matrix, 0)
    return sim_matrix


def textrank_scores(sim_matrix: np.ndarray) -> dict:#유사도 행렬을 PageRank해서 문장별 중요도 점수 생성

    graph = nx.from_numpy_array(sim_matrix)
    try:
        scores = nx.pagerank(graph, max_iter=200, tol=1e-5)
    except nx.PowerIterationFailedConvergence:
        scores = {i: 1.0 / len(sim_matrix) for i in range(len(sim_matrix))}
    return scores


def boost_scores(scores: dict, sentences: list, category: str) -> dict:#부스팅
    
    keywords = CATEGORY_BOOST_KEYWORDS.get(category, CATEGORY_BOOST_KEYWORDS["기타"])
    patterns = CATEGORY_PRIORITY_PATTERNS.get(category, CATEGORY_PRIORITY_PATTERNS["기타"])

    boosted = {}
    for idx, score in scores.items():
        sent = sentences[idx]
        kw_hits  = sum(1 for kw in keywords if kw in sent)
        pat_hits = sum(1 for pat in patterns if re.search(pat, sent))
        complete_bonus = 0.10 if is_complete_sentence(sent) else 0.0
        boosted[idx] = score * (1 + 0.20 * kw_hits + 0.40 * pat_hits + complete_bonus)

    return boosted


#핵심함수--------------------------------------------------------------------------

def summarize_notice(notice: dict, category: str = "기타", n: int = 3) -> str:
    title   = notice.get("title", "")
    content = notice.get("content", "")

    full_text = title + ". " + content
    full_text = clean_text(full_text)
    full_text = full_text[:3000]

    sentences = split_sentences(full_text)

    if not sentences:
        return None

    if len(sentences) <= n:
        title_core   = re.sub(r'^\[.*?\]\s*', '', title)
        title_prefix = re.sub(r'\s+', '', title_core)[:15]
        lines = []
        for s in sentences:
            cleaned = clean_extracted_sentence(s)
            if not cleaned or len(cleaned) < 8:
                continue
            cleaned_core = re.sub(r'^\[.*?\]\s*', '', cleaned)
            if re.sub(r'\s+', '', cleaned_core).startswith(title_prefix):
                continue
            lines.append("- " + cleaned)
        return "\n".join(lines) if lines else None

    try:
        sim_matrix = build_similarity_matrix(sentences)
        scores     = textrank_scores(sim_matrix)
        scores     = boost_scores(scores, sentences, category)

        # 상위 n개 인덱스를 원문 순서대로 정렬
        top_indices = sorted(
            sorted(scores, key=scores.get, reverse=True)[:n]
        )

        # [중요], [홍보] 같은 prefix 제거 후 제목 핵심 부분만 비교에 사용
        title_core = re.sub(r'^\[.*?\]\s*', '', title)
        title_prefix = re.sub(r'\s+', '', title_core)[:15]

        # 점수 높은 순으로 순회하며 필터 통과한 문장을 n개 수집
        ranked = sorted(scores, key=scores.get, reverse=True)
        selected = []
        for i in ranked:
            if len(selected) >= n:
                break
            cleaned = clean_extracted_sentence(sentences[i])
            if not cleaned or len(cleaned) < 8:
                continue
            # 제목과 동일한 내용이면 건너뜀
            # cleaned에서도 [중요] 같은 prefix 제거 후 비교
            cleaned_core = re.sub(r'^\[.*?\]\s*', '', cleaned)
            if re.sub(r'\s+', '', cleaned_core).startswith(title_prefix):
                continue
            # 불완전 문장 필터: 날짜/기간/금액이 있으면 허용, 없으면 제외
            if _INCOMPLETE_ENDING.search(cleaned):
                if not re.search(r'\d{1,2}[.월일]|\d+[,\d]*\s*원|기간|마감|신청', cleaned):
                    continue
            selected.append((i, cleaned))

        # 원문 순서(인덱스 오름차순)대로 재정렬해서 출력
        selected.sort(key=lambda x: x[0])
        summary_lines = ["- " + cleaned for _, cleaned in selected]

        return "\n".join(summary_lines) if summary_lines else None

    except Exception as e:
        print("[NLP] 요약 실패 - " + title[:30] + " / 오류: " + str(e))
        return None


def summarize_batch(notices: list) -> list:
    
    results = []
    total   = len(notices)

    for i, notice in enumerate(notices, 1):
        category = notice.get("category", "기타")
        title    = notice.get("title", "")[:40]
        print("[" + str(i) + "/" + str(total) + "] 요약 중: [" + category + "] " + title + "...")

        summary = summarize_notice(notice, category=category)
        results.append({**notice, "summary": summary})

    return results


#단독실행테스트----------------------------------------------------------------------------
if __name__ == "__main__":

    def _guess_category(title):
        if any(k in title for k in ["장학", "장학금"]):
            return "장학"
        if any(k in title for k in ["수강", "학사", "재입학"]):
            return "학사"
        if any(k in title for k in ["취업", "인턴", "채용"]):
            return "취업"
        if any(k in title for k in ["챌린지", "해커톤", "대회", "행사"]):
            return "행사"
        if any(k in title for k in ["프로그램", "교육"]):
            return "프로그램"
        return "기타"

    csv_path = "notices.csv"
    try:
        with open(csv_path, encoding="utf-8-sig") as f:
            all_notices = list(csv.DictReader(f))
    except FileNotFoundError:
        print("[오류] " + csv_path + " 파일을 찾을 수 없습니다.")
        exit(1)

    # 카테고리별 샘플 1건씩 추출
    seen_cats, samples = set(), []
    for n in all_notices:
        cat = _guess_category(n["title"])
        if cat not in seen_cats:
            n["category"] = cat
            samples.append(n)
            seen_cats.add(cat)
        if len(seen_cats) == len(CATEGORY_BOOST_KEYWORDS):
            break

    print("=" * 65)
    print("  TF-IDF + TextRank  카테고리별 요약 테스트")
    print("=" * 65)

    for notice in samples:
        cat   = notice["category"]
        title = notice["title"]
        date  = notice.get("date", "날짜 미상")
        print("\n[" + cat + "] " + title)
        print("날짜: " + date)
        result = summarize_notice(notice, category=cat)
        if result:
            print("요약:\n" + result)
        else:
            print("요약 실패")
        print("-" * 65)