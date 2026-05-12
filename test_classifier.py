import os, sys, pickle
os.environ['JAVA_HOME'] = 'C:/Program Files/Java/jdk-24'
import __main__

from konlpy.tag import Okt
okt = Okt()
stopwords = ['공지','안내','문의','학생','대학','관련','운영','신청','지원','참여','대상']

def tokenizer(text):
    nouns = okt.nouns(text)
    return [w for w in nouns if len(w) > 1 and w not in stopwords]

__main__.tokenizer = tokenizer

with open('app/vectorizer.pkl', 'rb') as f:
    vectorizer = pickle.load(f)
with open('app/model.pkl', 'rb') as f:
    model = pickle.load(f)

def classify(title, content='', threshold=0.3):
    text = title + ' ' + content
    tfidf = vectorizer.transform([text])
    probs = model.predict_proba(tfidf)[0]
    result = {cat: round(float(prob), 3) for cat, prob in zip(model.classes_, probs)}
    tags = [cat for cat, prob in result.items() if prob >= threshold]
    return {'tags': tags, 'probs': result}

# 카테고리별 테스트 케이스 (기대카테고리, 제목, 내용)
test_cases = [
    ('scholarship', '2024학년도 2학기 국가장학금 신청 안내', '한국장학재단 국가장학금 신청 기간입니다. 소득분위 8구간 이하 재학생은 꼭 신청하세요.'),
    ('scholarship', '교내 성적우수 장학금 선발 공고', '성적우수 장학생을 선발합니다. GPA 3.5 이상 재학생 대상으로 장학금을 지급합니다.'),
    ('job',         '삼성전자 하계 인턴십 채용 공고', '삼성전자에서 2024년 하계 인턴십을 모집합니다. 전공 무관, 서류 접수 마감 6월 30일.'),
    ('job',         '카카오 신입 공채 안내', '카카오에서 2024년 하반기 신입 개발자 공채를 진행합니다.'),
    ('event',       '2024 봄 축제 개최 안내', '올해 봄 축제가 5월 15일부터 17일까지 대운동장에서 열립니다. 다양한 공연과 이벤트가 준비되어 있습니다.'),
    ('event',       '학과 체육대회 개최 알림', '소프트웨어학과 체육대회를 개최합니다. 참가 학생 모집 중'),
    ('academic',    '2024학년도 2학기 수강신청 일정 안내', '2학기 수강신청은 7월 15일부터 시작됩니다. 선이수 과목 확인 후 신청 바랍니다.'),
    ('academic',    '졸업논문 제출 마감 일정 공지', '2024년 8월 졸업 예정자는 졸업논문을 6월 30일까지 제출해야 합니다.'),
    ('program',     '해외 교환학생 프로그램 참가자 모집', '2025년 봄학기 해외 교환학생 프로그램 참가자를 모집합니다. 미국, 유럽, 아시아 30개 대학 참여 가능.'),
    ('program',     '창업 멘토링 프로그램 참가자 모집', '스타트업 창업에 관심 있는 학생을 위한 멘토링 프로그램입니다. 현직 CEO가 직접 코칭합니다.'),
    ('other',       '도서관 임시 휴관 안내', '리모델링 공사로 인해 중앙도서관이 7월 1일부터 8월 31일까지 임시 휴관합니다.'),
    ('other',       '교내 주차 제한 안내', '5월 행사 기간 동안 교내 주차가 제한됩니다. 대중교통 이용을 권장합니다.'),
]

print('=' * 75)
print(f"{'제목':<32} {'기대':>10} {'예측':>12}  {'확률분포'}")
print('=' * 75)
correct = 0
for expected, title, content in test_cases:
    result = classify(title, content)
    best = max(result['probs'], key=result['probs'].get)
    mark = 'O' if best == expected else 'X'
    if best == expected:
        correct += 1
    short_title = title[:30] + '..' if len(title) > 30 else title
    top3 = sorted(result['probs'].items(), key=lambda x: -x[1])[:3]
    top3_str = ', '.join(f"{k}:{v:.2f}" for k, v in top3)
    print(f"[{mark}] {short_title:<33} {expected:>10} -> {best:<12}  {top3_str}")

print('=' * 75)
print(f"\n정확도: {correct}/{len(test_cases)} = {correct/len(test_cases)*100:.1f}%")

# threshold 테스트: 경계값 케이스
print('\n\n=== threshold 민감도 테스트 ===')
ambiguous = [
    ('장학금과 인턴십이 동시에 언급된 글', '장학금 지원 및 인턴십 채용 연계 프로그램', '우수 학생에게 장학금 지원과 함께 기업 인턴십 기회를 제공합니다.'),
    ('짧은 제목만 있는 글', '수강신청', ''),
    ('영어만 있는 제목', 'Software Engineering Internship 2024', 'Apply now for our summer internship program.'),
]
for label, title, content in ambiguous:
    result = classify(title, content, threshold=0.2)
    best = max(result['probs'], key=result['probs'].get)
    all_probs = ', '.join(f"{k}:{v:.3f}" for k, v in sorted(result['probs'].items(), key=lambda x: -x[1]))
    print(f"\n[{label}]")
    print(f"  제목: {title}")
    print(f"  예측: {best}  tags(>=0.2): {result['tags']}")
    print(f"  전체확률: {all_probs}")
