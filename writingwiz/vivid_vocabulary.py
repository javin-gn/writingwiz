"""
Learned vivid-vocabulary and vivid-phrase detector for the essay grader.

This no longer matches against the curated Vocabulary/Phrase bank (that
bank still powers the separate "Vivid Vocabulary Listing" page and the
theme-based suggestions shown above the essay box - this module is only
for *detecting* vivid vocabulary usage inside a submitted essay). Instead
it learns which words and phrases are distinctive straight from the
corpus of model answers and high-scoring student essays (EssayAttempt).

A word qualifies as "vivid" if, within that corpus, it:
  - is long enough to be a real vocabulary choice, not function words
    ("the", "was", "and"...) - enforced by MIN_WORD_LENGTH plus sklearn's
    built-in English stopword list;
  - isn't so common across the corpus that it's just generic narrative
    filler ("mother", "looked", "started") - enforced by max_df;
  - stands out strongly in at least one document (max, not mean, TF-IDF -
    mean is dominated by words that recur across many documents, which is
    the opposite of "distinctive");
  - isn't a character/place name - a lightweight heuristic flags a word as
    a likely proper noun if it's capitalised in the source text far more
    often than not, excluding the first word of each sentence (which is
    always capitalised regardless of being a proper noun or not);
  - is predominantly used as an adjective or adverb (NLTK's bundled
    averaged-perceptron POS tagger, run on each sentence for context -
    the same word can be a noun or a verb depending on its role, e.g.
    "run" is VB in "decided to run quickly" but NN read in isolation).
    TF-IDF rarity alone can't tell a genuinely descriptive word ("adorable")
    from an ordinary-but-topical noun ("accident"); this is what actually
    does that job.

This is corpus statistics plus a POS tagger, not true semantic judgement,
so it won't be perfect - but it reshapes itself as more essays are
submitted, rather than being stuck with a fixed list: min_df=2 means a
one-off typo can't make the list, it has to show up in at least two
different texts.

Phrases (2-3 word n-grams, e.g. "heart pounding") are learned the same
way - distinctiveness via max TF-IDF - but POS tagging a whole phrase
doesn't map cleanly onto a single adjective/adverb check. Instead a
phrase must: not start or end on a stop word (keeps boundaries clean,
e.g. "of the garden" is dropped); not contain a likely proper noun; and
contain at least one word this corpus already flagged as descriptive.
That last rule is doing the real work - without it, TF-IDF alone
surfaces any statistically rare collocation, including purely topical
ones ("assessment books", "civil defence") that aren't actually vivid.
"""

import os
import re
import threading
from collections import Counter, defaultdict

import nltk
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS

from .models import ModelAns, EssayAttempt

# Bundled in the repo (writingwiz/nltk_data/) so grading works without a
# network call to NLTK's servers at runtime - important on Vercel, where
# the filesystem is read-only and there's no guarantee of outbound access.
_NLTK_DATA_DIR = os.path.join(os.path.dirname(__file__), 'nltk_data')
if _NLTK_DATA_DIR not in nltk.data.path:
    nltk.data.path.insert(0, _NLTK_DATA_DIR)

MIN_CORPUS_SIZE = 20
MIN_ESSAY_WORDS = 15
GOOD_ESSAY_PERCENT = 80
MIN_WORD_LENGTH = 5
MIN_DOCUMENT_FREQUENCY = 2
MAX_DOCUMENT_FREQUENCY = 0.08
TOP_N_WORDS = 300
TOP_N_PHRASES = 150
PHRASE_NGRAM_RANGE = (2, 3)
PROPER_NOUN_CAP_RATIO = 0.7
ADJECTIVE_ADVERB_TAGS = {'JJ', 'JJR', 'JJS', 'RB', 'RBR', 'RBS'}

_lock = threading.Lock()
_vivid_words = None
_vivid_phrases = None
_built = False


def _build_corpus():
    texts = [a for a in ModelAns.objects.values_list('ans', flat=True) if a and len(a.split()) >= MIN_ESSAY_WORDS]
    texts += [
        a.essay_text for a in EssayAttempt.objects.filter(total_max__gt=0)
        if a.essay_text and len(a.essay_text.split()) >= MIN_ESSAY_WORDS and a.percent >= GOOD_ESSAY_PERCENT
    ]
    return texts


def _analyze_corpus(texts):
    """Single pass over the corpus: flags likely proper nouns by
    capitalisation pattern, and tracks each word's most common POS tag
    (tagged in its original sentence, not in isolation, since context is
    what the tagger actually uses to disambiguate noun/verb/adjective)."""
    cap_counts = Counter()
    total_counts = Counter()
    pos_counts = defaultdict(Counter)

    for text in texts:
        for sentence in re.split(r'(?<=[.!?])\s+', text.strip()):
            tokens = re.findall(r'[A-Za-z]+', sentence)
            if not tokens:
                continue
            for i, (tok, tag) in enumerate(nltk.pos_tag(tokens)):
                lower = tok.lower()
                if len(lower) < MIN_WORD_LENGTH:
                    continue
                if i > 0:  # sentence-initial word is always capitalised regardless
                    total_counts[lower] += 1
                    if tok[0].isupper():
                        cap_counts[lower] += 1
                pos_counts[lower][tag] += 1

    proper_nouns = {
        w for w, total in total_counts.items()
        if total >= MIN_DOCUMENT_FREQUENCY and cap_counts[w] / total >= PROPER_NOUN_CAP_RATIO
    }
    descriptive_words = {
        w for w, tags in pos_counts.items()
        if tags.most_common(1)[0][0] in ADJECTIVE_ADVERB_TAGS
    }
    return proper_nouns, descriptive_words


def _learn_vivid_words(texts, proper_nouns, descriptive_words):
    vectorizer = TfidfVectorizer(
        token_pattern=r'[a-zA-Z]{%d,}' % MIN_WORD_LENGTH,
        min_df=MIN_DOCUMENT_FREQUENCY,
        max_df=MAX_DOCUMENT_FREQUENCY,
        stop_words='english',
        lowercase=True,
    )
    tfidf = vectorizer.fit_transform(texts)
    if tfidf.shape[1] == 0:
        return frozenset()

    vocab = vectorizer.get_feature_names_out()
    max_scores = tfidf.max(axis=0).toarray().ravel()

    ranked = sorted(
        ((w, s) for w, s in zip(vocab, max_scores) if w not in proper_nouns and w in descriptive_words),
        key=lambda kv: kv[1], reverse=True,
    )
    return frozenset(word for word, _score in ranked[:TOP_N_WORDS])


def _is_clean_phrase(phrase, proper_nouns, descriptive_words):
    words = phrase.split()
    if any(len(w) < 2 for w in words):
        return False  # tokenizer artifact, e.g. "boy's" -> "boy", "s"
    if words[0] in ENGLISH_STOP_WORDS or words[-1] in ENGLISH_STOP_WORDS:
        return False
    if any(w in proper_nouns for w in words):
        return False
    # Without this, TF-IDF surfaces any distinctive *topic* collocation
    # ("assessment books", "civil defence") - requiring a word this corpus
    # already treats as descriptive keeps phrases in the same "paints a
    # picture" spirit as the single-word list, not just "rare phrase".
    if not any(w in descriptive_words for w in words):
        return False
    return True


def _learn_vivid_phrases(texts, proper_nouns, descriptive_words):
    vectorizer = TfidfVectorizer(
        ngram_range=PHRASE_NGRAM_RANGE,
        token_pattern=r'[a-zA-Z]{2,}',
        min_df=MIN_DOCUMENT_FREQUENCY,
        max_df=MAX_DOCUMENT_FREQUENCY,
        lowercase=True,
    )
    tfidf = vectorizer.fit_transform(texts)
    if tfidf.shape[1] == 0:
        return frozenset()

    vocab = vectorizer.get_feature_names_out()
    max_scores = tfidf.max(axis=0).toarray().ravel()

    ranked = sorted(
        ((p, s) for p, s in zip(vocab, max_scores) if _is_clean_phrase(p, proper_nouns, descriptive_words)),
        key=lambda kv: kv[1], reverse=True,
    )
    return frozenset(phrase for phrase, _score in ranked[:TOP_N_PHRASES])


def _learn_vivid_vocabulary():
    texts = _build_corpus()
    if len(texts) < MIN_CORPUS_SIZE:
        return frozenset(), frozenset()

    proper_nouns, descriptive_words = _analyze_corpus(texts)
    words = _learn_vivid_words(texts, proper_nouns, descriptive_words)
    phrases = _learn_vivid_phrases(texts, proper_nouns, descriptive_words)
    return words, phrases


def _ensure_built():
    global _vivid_words, _vivid_phrases, _built
    if _built:
        return
    with _lock:
        if _built:
            return
        _vivid_words, _vivid_phrases = _learn_vivid_vocabulary()
        _built = True


def get_vivid_words():
    """Lazily trains (once per process) and returns the learned set of vivid
    words. Cached the same way classifier.py caches its pipeline - a fresh
    process picks up whatever essays/model answers exist at that point."""
    _ensure_built()
    return _vivid_words


def get_vivid_phrases():
    """Same cache as get_vivid_words() - both are learned from one pass over
    the corpus, so the first call to either trains both."""
    _ensure_built()
    return _vivid_phrases
