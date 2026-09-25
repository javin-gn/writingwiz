"""
ML-based writing-quality classifier for the essay grader.

There is no PSLE-graded score dataset to train on. Instead, this trains a
binary classifier to tell genuine PSLE model-answer prose (from `model_ans`,
already in the database) apart from programmatically degraded copies of the
same text (punctuation stripped, sentences shuffled, misspellings injected,
lowercased). The classifier's confidence that a submitted essay "reads like"
the genuine class is one signal among several in grading.py - it is a
statistical style/fluency estimate, not a judgement of whether the content
itself is good, and it is only as good as the ~200 model answers it learns
from.
"""

import random
import re
import threading

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .models import ModelAns

MIN_POSITIVE_EXAMPLES = 20
DEGRADATIONS_PER_EXAMPLE = 3

_rng = random.Random(42)
_lock = threading.Lock()
_pipeline = None
_trained = False


def _typo(word):
    if len(word) < 4:
        return word
    i = _rng.randrange(1, len(word) - 1)
    choice = _rng.random()
    if choice < 0.4:
        chars = list(word)
        chars[i], chars[i + 1] = chars[i + 1], chars[i]
        return ''.join(chars)
    if choice < 0.7:
        return word[:i] + word[i + 1:]
    return word[:i] + word[i] + word[i:]


def _degrade(text):
    # TfidfVectorizer's default tokenizer already ignores punctuation/case, so
    # stripping those alone changes nothing a bag-of-words model can see. The
    # signal that actually shows up in n-gram features is word ORDER: scrambling
    # words within each sentence destroys grammatical structure (bigrams) while
    # keeping the same vocabulary - a reasonable proxy for "not well-formed
    # writing" that a TF-IDF classifier can genuinely learn to detect.
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
    if not sentences:
        return text.lower()
    _rng.shuffle(sentences)

    degraded_sentences = []
    for s in sentences:
        words = s.split()
        _rng.shuffle(words)
        out_words = []
        for w in words:
            if _rng.random() < 0.25:
                w = _typo(w)
            out_words.append(w)
        degraded_sentences.append(' '.join(out_words))

    combined = ' '.join(degraded_sentences)
    combined = re.sub(r'[.,!?;:"\']', '', combined)
    return combined.lower()


def _build_training_set():
    answers = [a for a in ModelAns.objects.values_list('ans', flat=True) if a and len(a.split()) >= 15]
    if len(answers) < MIN_POSITIVE_EXAMPLES:
        return [], []

    texts, labels = [], []
    for ans in answers:
        texts.append(ans)
        labels.append(1)
        for _ in range(DEGRADATIONS_PER_EXAMPLE):
            texts.append(_degrade(ans))
            labels.append(0)
    return texts, labels


def _get_pipeline():
    global _pipeline, _trained
    if _trained:
        return _pipeline
    with _lock:
        if _trained:
            return _pipeline
        texts, labels = _build_training_set()
        if texts:
            pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=5000)),
                ('clf', LogisticRegression(max_iter=1000, class_weight='balanced', solver='liblinear')),
            ])
            pipeline.fit(texts, labels)
            _pipeline = pipeline
        _trained = True
        return _pipeline


def classify_essay(text):
    """Returns (probability, note). probability is None if there wasn't
    enough model-answer data in the database to train the classifier."""
    pipeline = _get_pipeline()
    if pipeline is None:
        return None, 'Not enough model-answer data in the database to train the classifier.'
    if not text.strip():
        return 0.0, 'No text to assess.'
    proba = float(pipeline.predict_proba([text])[0][1])
    return proba, (
        f'{proba * 100:.0f}% confidence this reads like genuine PSLE model-answer writing '
        f'(a classifier trained on real model answers vs. deliberately degraded copies of them).'
    )
