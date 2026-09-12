"""Local Presidio detection with reversible, session-specific placeholders."""
import re
import secrets
from functools import lru_cache

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig, RecognizerResult


@lru_cache(maxsize=1)
def analyser():
    # Require an installed model: never download a model while processing a client.
    import spacy
    if not spacy.util.is_package('en_core_web_sm'):
        raise RuntimeError('Install the English model using the setup instructions, then restart.')
    nlp = NlpEngineProvider(nlp_configuration={
        'nlp_engine_name': 'spacy',
        'models': [{'lang_code': 'en', 'model_name': 'en_core_web_sm'}],
    }).create_engine()
    engine = AnalyzerEngine(nlp_engine=nlp, supported_languages=['en'])
    # The default email validator can fetch a public-suffix list. A conservative
    # local pattern avoids any network lookup or cache write during processing.
    engine.registry.remove_recognizer('EmailRecognizer')
    patterns = {
        'EMAIL_ADDRESS': r"(?<![\w.+-])[\w.!#$%&'*+/=?^`{|}~-]+@[\w.-]+\.[A-Za-z]{2,}(?!\w)",
        'AU_PHONE': r'(?<!\w)(?:\+61[ -]?[23478]|0[23478])(?:[ -]?\d){8}(?!\d)',
        'AU_MEDICARE_CANDIDATE': r'(?<!\d)[2-6]\d{3}[ -]?\d{5}[ -]?\d(?:[ /-]?\d)?(?!\d)',
        'DATE': r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b',
        'ADDRESS': r'\b\d{1,5}[A-Za-z]?(?:/\d{1,5})?\s+(?:[A-Za-z]+\s+){1,5}(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Crescent|Cres|Court|Ct|Parade|Pde|Way|Terrace|Tce)\b',
    }
    for kind, pattern in patterns.items():
        engine.registry.add_recognizer(PatternRecognizer(supported_entity=kind,
            patterns=[Pattern(name=kind, regex=pattern, score=.8)]))
    return engine


def mask(text, extra_terms=None):
    if '[[' in text or ']]' in text:
        raise ValueError('Remove existing double-square-bracket placeholders before starting a new client.')
    engine = analyser()
    entities = ['PERSON', 'LOCATION', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 'URL',
                'AU_MEDICARE', 'AU_TFN', 'AU_ABN', 'AU_ACN', 'AU_PHONE',
                'AU_MEDICARE_CANDIDATE', 'DATE', 'ADDRESS']
    supported = engine.get_supported_entities(language='en')
    found = engine.analyze(text=text, language='en',
        entities=[e for e in entities if e in supported], score_threshold=.4)
    spans = [(f.start, f.end, f.entity_type) for f in found]
    name_parts = set()
    for finding in found:
        if finding.entity_type == 'PERSON':
            name_parts.update(re.findall(r"[^\W\d_][^\W\d_'-]+(?:['-][^\W\d_]+)*", text[finding.start:finding.end]))
    for match in re.finditer(r'(?im)^(?:client|patient|name|parent|carer|therapist|clinician)\s*:\s*([^\n;]+)', text):
        name_parts.update(re.findall(r"[^\W\d_][^\W\d_'-]+(?:['-][^\W\d_]+)*", match[1]))
    # First names and surnames used alone often escape the statistical model.
    # Do not guess that two occurrences refer to the same person: preserve each exact value.
    for part in name_parts:
        if part.lower() not in {'client', 'patient', 'clinician', 'therapist', 'unknown', 'not', 'documented', 'dr', 'mr', 'mrs', 'ms'}:
            for match in re.finditer(r'(?<!\w)' + re.escape(part) + r'(?!\w)', text, re.I):
                spans.append((match.start(), match.end(), 'PERSON'))
    # Schools, employers and clinics can identify someone even without a name.
    doc = engine.nlp_engine.nlp['en'](text)
    for ent in doc.ents:
        if ent.label_ in {'ORG', 'FAC', 'GPE', 'LOC'} and ent.text.lower() not in {'clinician', 'therapist', 'client', 'patient', 'soap', 'dap', 'ndis'}:
            spans.append((ent.start_char, ent.end_char, 'ORGANISATION' if ent.label_ == 'ORG' else 'LOCATION'))
    # Labelled IDs are candidates, not claims of checksum validity.
    for match in re.finditer(r'(?im)\b(?:NDIS(?:\s+(?:number|no\.?|ID))?|MRN|IHI|client\s+ID|patient\s+ID|Medicare(?:\s+(?:number|no\.?))?)\s*[:#-]?\s*([A-Z0-9][A-Z0-9 /-]{3,24})', text):
        a, b = match.span(1)
        value = text[a:b].rstrip()
        if any(c.isdigit() for c in value):
            spans.append((a, a + len(value), 'CLIENT_ID'))
    # Full labelled fields supplement statistical recognition, especially unfamiliar names.
    for match in re.finditer(r'(?im)^(?:client|patient|name|parent|carer|therapist|clinician|address|school|employer)\s*:\s*([^\n;]+)', text):
        a, b = match.span(1)
        spans.append((a, b, 'DETAIL'))
    for value in extra_terms or []:
        value = value.strip()
        if value:
            for m in re.finditer(re.escape(value), text, flags=re.I):
                spans.append((m.start(), m.end(), 'DETAIL'))
    # Merge overlaps so a shorter finding cannot expose the end of an address or ID.
    merged = []
    for start, end, kind in sorted(spans, key=lambda s: (s[0], -s[1])):
        if merged and start < merged[-1][1]:
            prev = merged[-1]
            merged[-1] = (prev[0], max(end, prev[1]), prev[2])
        else:
            merged.append((start, end, kind))
    nonce = secrets.token_hex(4).upper()
    mapping, replacements, seen = {}, [], {}
    anonymizer = AnonymizerEngine()
    for start, end, kind in merged:
        value = text[start:end]
        # Exact originals remain distinct, avoiding loss of spelling/case on restoration.
        if value not in seen:
            token = f'[[{kind}_{nonce}_{len(mapping)+1:03d}]]'
            seen[value] = token
            mapping[token] = value
        token = seen[value]
        replacements.append((start, end, token))
    masked = text
    for start, end, token in reversed(replacements):
        original = text[start:end]
        # Use Presidio's replace operator, with our local reversible map held by the tab.
        result = anonymizer.anonymize(text=original,
            analyzer_results=[RecognizerResult(entity_type='DETAIL', start=0, end=len(original), score=1)],
            operators={'DEFAULT': OperatorConfig('replace', {'new_value': token})})
        masked = masked[:start] + result.text + masked[end:]
    return {'text': masked, 'mapping': mapping, 'occurrences': len(replacements)}
