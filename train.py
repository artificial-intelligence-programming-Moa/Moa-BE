"""
notices_fixed.csv 기반 모델 학습 + 검증
"""
import os, sys, csv, pickle
sys.path.insert(0, os.path.dirname(__file__))
os.environ['JAVA_HOME'] = 'C:/Program Files/Java/jdk-24'

from classifier import tokenizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix
from collections import Counter
import numpy as np

# ─── 데이터 로드 ──────────────────────────────────────────────────────────────
with open('app/notices_fixed.csv', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

labels, texts = [], []
for r in rows:
    cat = r['category'].strip()
    title = r['title'].strip()
    content = r['content'].strip()
    if cat and title:
        labels.append(cat)
        texts.append(title + " " + content)

print(f"총 데이터: {len(texts)}건")
print("카테고리 분포:", dict(sorted(Counter(labels).items())))

# ─── Train / Test 분리 (80/20, stratified) ────────────────────────────────────
X_train_raw, X_test_raw, y_train, y_test = train_test_split(
    texts, labels, test_size=0.2, random_state=42, stratify=labels
)
print(f"\nTrain: {len(X_train_raw)}건 / Test: {len(X_test_raw)}건")

# ─── 벡터라이저 학습 (train set만 fit) ───────────────────────────────────────
vectorizer = TfidfVectorizer(
    tokenizer=tokenizer,
    max_features=5000,
    ngram_range=(1, 2),
    token_pattern=None,
    sublinear_tf=True,
)
X_train = vectorizer.fit_transform(X_train_raw)
X_test  = vectorizer.transform(X_test_raw)

# ─── 모델 학습 ────────────────────────────────────────────────────────────────
model = LogisticRegression(
    C=5.0,
    max_iter=1000,
    multi_class='multinomial',
    solver='lbfgs',
    class_weight='balanced',
)
model.fit(X_train, y_train)

# ─── 검증 ─────────────────────────────────────────────────────────────────────
print("\n=== Test Set 성능 ===")
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred, digits=3))

print("=== Confusion Matrix ===")
classes = sorted(set(labels))
cm = confusion_matrix(y_test, y_pred, labels=classes)
header = f"{'':>12}" + "".join(f"{c:>12}" for c in classes)
print(header)
for i, row in enumerate(cm):
    print(f"{classes[i]:>12}" + "".join(f"{v:>12}" for v in row))

print("\n=== 5-Fold Stratified CV (전체 데이터) ===")
X_all = vectorizer.transform(texts)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X_all, labels, cv=skf, scoring='accuracy')
print(f"CV 정확도: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
print(f"각 fold:   {[f'{s:.4f}' for s in cv_scores]}")

# ─── 저장 (전체 데이터로 최종 재학습 후 저장) ────────────────────────────────
X_all_fit = vectorizer.fit_transform(texts)
model.fit(X_all_fit, labels)

with open('app/vectorizer.pkl', 'wb') as f:
    pickle.dump(vectorizer, f)
with open('app/model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("\n최종 모델 저장 완료: app/vectorizer.pkl, app/model.pkl")
