"""
Rule-based PSLE English essay grader, plus one trained ML signal.

This is a deterministic approximation of PSLE marking, not a real marker or an
LLM assessment - most checks are mechanical/structural proxies (spelling,
sentence mechanics, length, paragraphing, coherence, keyword overlap with the
question, vocabulary variety). The one genuinely trained component is the
"Writing style (ML classifier)" signal from classifier.py, a TF-IDF +
Logistic Regression model trained on real PSLE model answers vs.
programmatically degraded copies of them - it estimates word-order/grammatical
fluency, not content quality. None of this can judge narrative quality,
creativity, or whether the content actually makes sense. Scores and feedback
should be read as a checklist, not an authoritative grade.

PSLE marking scheme this approximates:
  Continuous Writing: 40 marks total (Content 15, Language 25)
  Situational Writing: 10 marks total (Content 5, Language 5)
"""

import re

from spellchecker import SpellChecker

from .models import Vocabulary, Phrase
from .classifier import classify_essay

MAX_MARKS = {
    'Continuous': {'content': 15, 'language': 25},
    'Situational': {'content': 5, 'language': 5},
}

WORD_COUNT_BAND = {
    'Continuous': (150, 400),
    'Situational': (50, 150),
}

STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'if', 'so', 'of', 'to', 'in', 'on',
    'at', 'for', 'with', 'about', 'as', 'by', 'is', 'was', 'were', 'are',
    'be', 'been', 'being', 'it', 'its', 'this', 'that', 'these', 'those',
    'i', 'you', 'he', 'she', 'we', 'they', 'my', 'your', 'his', 'her',
    'our', 'their', 'me', 'him', 'us', 'them', 'not', 'no', 'do', 'did',
    'does', 'have', 'has', 'had', 'will', 'would', 'can', 'could', 'should',
    'from', 'up', 'out', 'into', 'over', 'then', 'than', 'there', 'here',
}

# Cohesive devices PSLE band descriptors explicitly look for when assessing
# whether ideas are "coherently and logically organised".
LINKING_WORDS = [
    'however', 'therefore', 'moreover', 'furthermore', 'nevertheless', 'nonetheless',
    'consequently', 'thus', 'hence', 'additionally', 'besides', 'firstly', 'secondly',
    'thirdly', 'finally', 'lastly', 'meanwhile', 'afterwards', 'subsequently',
    'eventually', 'suddenly', 'although', 'though', 'despite', 'because', 'since',
    'as a result', 'in addition', 'on the other hand', 'in contrast', 'similarly',
    'likewise', 'for example', 'for instance', 'in conclusion', 'to conclude',
    'in summary', 'as soon as', 'in the end', 'after that', 'before long',
]

_spell = SpellChecker()

# PSLE uses British/Singapore English, but pyspellchecker's dictionary is
# US-leaning - without this, correct words like "realised" or "colour" would
# be wrongly flagged as spelling mistakes.
_BRITISH_SPELLINGS = [
    'colour', 'colours', 'coloured', 'colouring', 'favour', 'favours', 'favourite',
    'favourites', 'neighbour', 'neighbours', 'neighbourhood', 'honour', 'honours',
    'honoured', 'humour', 'humourous', 'behaviour', 'behavioural', 'labour', 'labours',
    'rumour', 'rumours', 'endeavour', 'endeavours', 'savour', 'savoury',
    'realise', 'realised', 'realises', 'realising', 'organise', 'organised',
    'organises', 'organising', 'organisation', 'organisations', 'recognise',
    'recognised', 'recognises', 'recognising', 'apologise', 'apologised',
    'apologises', 'apologising', 'memorise', 'memorised', 'memorising',
    'criticise', 'criticised', 'criticising', 'analyse', 'analysed', 'analysing',
    'summarise', 'summarised', 'summarising', 'emphasise', 'emphasised',
    'emphasising', 'catalogue', 'dialogue', 'dialogues', 'centre', 'centres',
    'centred', 'theatre', 'theatres', 'metre', 'metres', 'litre', 'litres',
    'fibre', 'fibres', 'travelled', 'travelling', 'traveller', 'travellers',
    'cancelled', 'cancelling', 'modelled', 'modelling', 'labelled', 'labelling',
    'jewellery', 'defence', 'offence', 'licence', 'practise', 'practised',
    'practising', 'grey', 'greyish', 'mould', 'moulded', 'plough', 'programme',
    'programmes', 'tyre', 'tyres', 'kerb', 'aeroplane', 'aeroplanes', 'aluminium',
    'cheque', 'cheques', 'draught', 'gaol', 'manoeuvre', 'manoeuvring',
    'mum', 'mummy', 'whilst', 'amongst',
]
_spell.word_frequency.load_words(_BRITISH_SPELLINGS)


def _paragraphs(text):
    return [p.strip() for p in re.split(r'\n\s*\n', text.strip()) if p.strip()]


def _sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _words(text):
    return re.findall(r"[A-Za-z']+", text)


def _scale(fraction, weight):
    """Clamp fraction to [0, 1] and scale to a mark allocation."""
    return round(max(0.0, min(1.0, fraction)) * weight, 1)


def _score_length(word_count, qtype):
    low, high = WORD_COUNT_BAND[qtype]
    if word_count == 0:
        return 0.0, f'No text submitted.'
    if low <= word_count <= high:
        return 1.0, f'{word_count} words - within the expected {low}-{high} word range.'
    if word_count < low:
        fraction = word_count / low
        return fraction, f'{word_count} words - shorter than the expected {low}-{high} word range.'
    # too long: mild penalty, capped
    over_by = word_count - high
    fraction = max(0.6, 1.0 - over_by / (high * 2))
    return fraction, f'{word_count} words - longer than the expected {low}-{high} word range.'


def _score_structure(paragraphs, qtype):
    n = len(paragraphs)
    if qtype == 'Continuous':
        if n >= 3:
            return 1.0, f'{n} paragraphs - has an introduction/body/conclusion shape.'
        if n == 2:
            return 0.7, f'{n} paragraphs - consider splitting into an intro, body and conclusion.'
        return 0.4, f'{n} paragraph - not broken into an introduction, body and conclusion.'
    else:
        if n >= 1:
            return 1.0, f'{n} paragraph(s).'
        return 0.4, 'No clear paragraph breaks.'


# Pronouns/determiners that typically point back to something in a previous
# sentence - a core way narrative writing stays connected without repeating nouns.
_REFERENCE_WORDS = {
    'he', 'she', 'it', 'they', 'him', 'her', 'them', 'his', 'their', 'its',
    'this', 'that', 'these', 'those', 'there',
}


def _has_continuity_signal(sentence_words, text_lower_sentence):
    if any(w in _REFERENCE_WORDS for w in sentence_words[:4]):
        return True
    return any(re.search(r'\b' + re.escape(lw) + r'\b', text_lower_sentence) for lw in LINKING_WORDS)


def _score_coherence(sentences, text):
    if len(sentences) < 2:
        return 0.5, 'Too few sentences to assess how well ideas connect.'

    # Continuity: does each sentence (after the first) pick up a pronoun/reference
    # to something earlier, or use a linking word/phrase, rather than reading as
    # a standalone, disconnected statement?
    connected = 0
    for s in sentences[1:]:
        words_lower = [w.lower() for w in _words(s)]
        if _has_continuity_signal(words_lower, s.lower()):
            connected += 1
    continuity_fraction = connected / (len(sentences) - 1)

    text_lower = text.lower()
    linking_hits = sum(1 for w in LINKING_WORDS if re.search(r'\b' + re.escape(w) + r'\b', text_lower))

    # Repetitive sentence openers ("I did... I did... I did...") read as choppy,
    # disconnected narration rather than flowing prose.
    openers = [w[0].lower() for w in (_words(s) for s in sentences) if w]
    max_run = 1
    run = 1
    for i in range(1, len(openers)):
        run = run + 1 if openers[i] == openers[i - 1] else 1
        max_run = max(max_run, run)
    opener_penalty = 0.3 if max_run >= 3 else 0.0

    fraction = max(0.0, continuity_fraction - opener_penalty)

    note = f'{connected} of {len(sentences) - 1} sentences pick up a reference or linking word from what came before; {linking_hits} cohesive device(s) found overall (e.g. however, firstly, as a result).'
    if opener_penalty:
        note += f' {max_run} sentences in a row start with the same word - try varying your sentence openers.'
    return fraction, note


def _score_relevance(essay_words, question_text):
    if not question_text:
        return None, 'No question selected, so relevance to a prompt was not checked.'
    q_keywords = {w.lower() for w in _words(question_text) if len(w) > 3 and w.lower() not in STOPWORDS}
    e_words = {w.lower() for w in essay_words}
    if not q_keywords:
        return None, 'Could not extract keywords from the question.'
    overlap = q_keywords & e_words
    fraction = len(overlap) / len(q_keywords)
    return fraction, f'Essay touches on {len(overlap)} of {len(q_keywords)} key words/topics from the question.'


def _score_spelling(words):
    if not words:
        return 0.0, [], 'No words to check.'
    lower_words = [w.lower() for w in words]
    misspelled = _spell.unknown(lower_words)
    accuracy = 1 - (len(misspelled) / len(words))
    misspelled_list = sorted(misspelled)
    return accuracy, misspelled_list, f'{len(misspelled_list)} possibly misspelled word(s) out of {len(words)}.'


def _score_mechanics(sentences):
    if not sentences:
        return 0.0, 'No sentences to check.'
    ok = 0
    for s in sentences:
        starts_upper = s[:1].isupper()
        ends_proper = s[-1:] in '.!?"\''
        if starts_upper and ends_proper:
            ok += 1
    fraction = ok / len(sentences)
    return fraction, f'{ok} of {len(sentences)} sentences start with a capital letter and end with proper punctuation.'


def _score_vocabulary(words, essay_text):
    if not words:
        return 0.0, 'No words to assess.'
    unique_ratio = len(set(w.lower() for w in words)) / len(words)
    ttr_score = min(1.0, unique_ratio / 0.5)

    essay_lower = essay_text.lower()
    vivid_hits = [
        v for v in Vocabulary.objects.values_list('vocabulary', flat=True)
        if re.search(r'\b' + re.escape(v.lower()) + r'\b', essay_lower)
    ]
    phrase_hits = [
        p for p in Phrase.objects.values_list('phrase', flat=True)
        if p.lower() in essay_lower
    ]
    bonus = min(0.3, 0.03 * (len(vivid_hits) + len(phrase_hits)))
    fraction = min(1.0, ttr_score * 0.8 + bonus)

    note = f'Vocabulary variety score {unique_ratio:.2f} (unique/total words).'
    if vivid_hits or phrase_hits:
        sample = (vivid_hits + phrase_hits)[:8]
        note += f' Used {len(vivid_hits) + len(phrase_hits)} vivid vocabulary/phrase bank word(s): {", ".join(sample)}.'
    return fraction, note


def _score_sentence_variety(sentences):
    if not sentences:
        return 0.0, 'No sentences to check.'
    lengths = [len(_words(s)) for s in sentences]
    long_run_ons = sum(1 for l in lengths if l > 40)
    avg_len = sum(lengths) / len(lengths)
    fraction = 1.0
    notes = [f'Average sentence length {avg_len:.0f} words.']
    if long_run_ons:
        fraction -= min(0.6, 0.2 * long_run_ons)
        notes.append(f'{long_run_ons} sentence(s) look like run-ons (over 40 words) - consider breaking them up.')
    if avg_len < 5 and len(sentences) > 3:
        fraction -= 0.2
        notes.append('Many very short sentences - try combining some for better flow.')
    return max(0.0, fraction), ' '.join(notes)


def grade_essay(text, qtype='Continuous', question_text=''):
    """Grade `text` against an approximate PSLE rubric for `qtype`
    ('Continuous' or 'Situational'), optionally scored for relevance
    against `question_text`."""
    qtype = qtype if qtype in MAX_MARKS else 'Continuous'
    max_marks = MAX_MARKS[qtype]

    words = _words(text)
    sentences = _sentences(text)
    paragraphs = _paragraphs(text)
    word_count = len(words)

    if word_count == 0:
        return {
            'qtype': qtype,
            'word_count': 0,
            'sentence_count': 0,
            'paragraph_count': 0,
            'content_score': 0,
            'content_max': max_marks['content'],
            'language_score': 0,
            'language_max': max_marks['language'],
            'total_score': 0,
            'total_max': max_marks['content'] + max_marks['language'],
            'breakdown': [],
            'misspelled_words': [],
            'suggestions': ['Write your essay in the box above before grading.'],
        }

    breakdown = []

    # --- Content ---
    content_max = max_marks['content']
    length_frac, length_note = _score_length(word_count, qtype)
    structure_frac, structure_note = _score_structure(paragraphs, qtype)
    coherence_frac, coherence_note = _score_coherence(sentences, text)
    relevance_frac, relevance_note = _score_relevance(words, question_text)

    length_weight = content_max * 0.2
    structure_weight = content_max * 0.2
    coherence_weight = content_max * 0.3
    relevance_weight = content_max * 0.3

    content_score = (
        _scale(length_frac, length_weight)
        + _scale(structure_frac, structure_weight)
        + _scale(coherence_frac, coherence_weight)
    )
    breakdown.append({'label': 'Length', 'score': _scale(length_frac, length_weight), 'max': round(length_weight, 1), 'note': length_note})
    breakdown.append({'label': 'Paragraph structure', 'score': _scale(structure_frac, structure_weight), 'max': round(structure_weight, 1), 'note': structure_note})
    breakdown.append({'label': 'Sentence coherence', 'score': _scale(coherence_frac, coherence_weight), 'max': round(coherence_weight, 1), 'note': coherence_note})

    if relevance_frac is None:
        # No question selected - give the benefit of the doubt (neutral, not zero)
        relevance_marks = round(relevance_weight * 0.5, 1)
    else:
        relevance_marks = _scale(relevance_frac, relevance_weight)
    content_score += relevance_marks
    breakdown.append({'label': 'Relevance to question', 'score': relevance_marks, 'max': round(relevance_weight, 1), 'note': relevance_note})

    content_score = round(min(content_max, content_score), 1)

    # --- Language ---
    language_max = max_marks['language']
    spelling_frac, misspelled, spelling_note = _score_spelling(words)
    mechanics_frac, mechanics_note = _score_mechanics(sentences)
    vocab_frac, vocab_note = _score_vocabulary(words, text)
    variety_frac, variety_note = _score_sentence_variety(sentences)
    style_frac, style_note = classify_essay(text)

    spelling_weight = language_max * 0.30
    mechanics_weight = language_max * 0.20
    vocab_weight = language_max * 0.15
    variety_weight = language_max * 0.15
    style_weight = language_max * 0.20

    language_parts = [
        {'label': 'Spelling', 'score': _scale(spelling_frac, spelling_weight), 'max': round(spelling_weight, 1), 'note': spelling_note},
        {'label': 'Sentence mechanics (capitals/punctuation)', 'score': _scale(mechanics_frac, mechanics_weight), 'max': round(mechanics_weight, 1), 'note': mechanics_note},
        {'label': 'Vocabulary variety', 'score': _scale(vocab_frac, vocab_weight), 'max': round(vocab_weight, 1), 'note': vocab_note},
        {'label': 'Sentence variety', 'score': _scale(variety_frac, variety_weight), 'max': round(variety_weight, 1), 'note': variety_note},
    ]

    if style_frac is None:
        style_marks = round(style_weight * 0.5, 1)
    else:
        style_marks = _scale(style_frac, style_weight)
    language_parts.append({'label': 'Writing style (ML classifier)', 'score': style_marks, 'max': round(style_weight, 1), 'note': style_note})

    breakdown += language_parts
    language_score = round(min(language_max, sum(p['score'] for p in language_parts)), 1)

    total_score = round(content_score + language_score, 1)
    total_max = content_max + language_max

    suggestions = []
    if word_count and word_count < WORD_COUNT_BAND[qtype][0]:
        suggestions.append('Try writing more - your essay is shorter than the expected length.')
    if misspelled:
        suggestions.append(f'Check the spelling of: {", ".join(misspelled[:10])}.')
    if mechanics_frac < 0.8:
        suggestions.append('Check that every sentence starts with a capital letter and ends with a full stop, question mark or exclamation mark.')
    if qtype == 'Continuous' and len(paragraphs) < 3:
        suggestions.append('Organise your writing into an introduction, body paragraphs and a conclusion.')
    if coherence_frac < 0.5:
        suggestions.append('Use more linking words (however, therefore, meanwhile, as a result...) to connect your ideas, and avoid starting several sentences in a row the same way.')
    if variety_frac < 0.7:
        suggestions.append('Vary your sentence lengths - break up very long sentences and combine short, choppy ones.')

    return {
        'qtype': qtype,
        'word_count': word_count,
        'sentence_count': len(sentences),
        'paragraph_count': len(paragraphs),
        'content_score': content_score,
        'content_max': content_max,
        'language_score': language_score,
        'language_max': language_max,
        'total_score': total_score,
        'total_max': total_max,
        'breakdown': breakdown,
        'misspelled_words': misspelled,
        'suggestions': suggestions,
    }
