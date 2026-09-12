# Verification — 11/09/2026

Working prototype tested on macOS with Python 3.12, Presidio 2.2.364, spaCy 3.8.16 / en_core_web_sm 3.8.0, PDFium 5.13.0 and Apple Vision through PyObjC 12.2.2.

## Completed

- 12 Python tests passed: Australian example identifiers, exact mask/restore round trip, preservation of pain score/negation/duration, different session keys, overlapping manual terms, repeated first/surnames, Host/Origin/header rejection, input validation, in-memory upload streams, image OCR, scanned PDF OCR, selectable PDF text, unreadable PDF rejection, over-page-limit rejection and an OCR upload through the HTTP endpoint. Some tests contain multiple assertions.
- 6 JavaScript tests passed: repeated restoration, another client's tokens, damaged tokens, missing tokens, non-recursive literal replacement, and unused token reporting.
- Browser walkthrough: loaded fictional example, scanned it, reviewed full prompt, copied it, pasted a simulated response, restored full and first names, verified the clinical review gate, copied the reviewed note and cleared the client.
- Desktop screenshot inspection and 390 px mobile review-screen inspection completed. Temporary viewport override reset.
- No real client information or external AI service used. The simulated response tests restoration, not model generation quality.

## Limits

This is not a clinical accuracy study, penetration test, compliance certification or exhaustive PII recall evaluation. OCR was verified with clear machine-printed fictional fixtures, not handwriting or low-quality scans. Linux/Windows OCR and packaging are untested. A network-connect-blocking test covers detection on synthetic input; there has not been a full operating-system traffic capture. Local processing was also reviewed in source, and the default email validator was replaced to avoid a public-suffix network lookup.

The app is ready for Brooke to review using fictional data. Real clinical use and public deployment remain outside the validated scope.
