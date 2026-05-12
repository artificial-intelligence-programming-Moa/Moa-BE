import os
import pickle
from pathlib import Path

if not os.environ.get("JAVA_HOME"):
    os.environ["JAVA_HOME"] = "C:/Program Files/Java/jdk-24"

from konlpy.tag import Okt

okt = Okt()
stopwords = ["공지","안내","문의","학생","대학","관련","운영","신청","지원","참여","대상"]

def tokenizer(text):
    nouns = okt.nouns(text)
    return [w for w in nouns if len(w) > 1 and w not in stopwords]

_MODEL_DIR = Path(__file__).parent / "app"
_vectorizer = None
_model = None

def _load():
    global _vectorizer, _model
    if _vectorizer is None:
        with open(_MODEL_DIR / "vectorizer.pkl", "rb") as f:
            _vectorizer = pickle.load(f)
        with open(_MODEL_DIR / "model.pkl", "rb") as f:
            _model = pickle.load(f)

def classify(title: str, content: str = "", threshold: float = 0.3):
    _load()
    text = title + " " + content
    tfidf = _vectorizer.transform([text])
    probs = _model.predict_proba(tfidf)[0]
    result = {
        cat: round(float(prob), 3)
        for cat, prob in zip(_model.classes_, probs)
    }
    tags = [cat for cat, prob in result.items() if prob >= threshold]
    return {"tags": tags, "probs": result}
