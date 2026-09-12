# Between Notes

A working local prototype for Australian allied health clinicians: import session material, replace identifiers with reversible placeholders, copy a notes prompt into an approved AI tool, then restore the details in the returned draft.

**Use fictional clients for this prototype. It has not been validated for clinical use, and it does not certify that text is anonymous or safe to disclose.**

## Quick start (macOS)

Install Python 3.12 and Git, then open Terminal and run:

```sh
git clone https://github.com/BrookeW1988/between-notes.git
cd between-notes
bash setup.sh
./start.command
```

Open [the local app](http://127.0.0.1:5179). Keep the Terminal window and browser tab open while using it. Press Control+C in Terminal to stop the server. After setup, you can double-click `start.command` to start again.

This is a local app you install on your own computer, not a hosted website. Downloading the repository ZIP is also supported: extract it, open Terminal in that folder, and run the last two commands above.

## Try it with fictional PDFs

Download [the normal test PDF](examples/fictional-client.pdf) or [the image-only OCR test PDF](examples/fictional-client-scanned.pdf). In GitHub's file viewer, choose **Download raw file** to save the PDF. Both contain the same invented case. Follow the [test walkthrough](examples/README.md).

## Platforms and setup

Setup downloads dependencies and the English model. After setup, text detection and document processing run locally. On macOS, OCR uses Apple Vision via PyObjC. On Linux or Windows, install the Tesseract executable and its English language data as well; the non-macOS path is implemented but has not been tested here. Windows users can create a virtual environment, install `requirements.txt`, run `python -m spacy download en_core_web_sm`, then run `python app.py` rather than the shell launchers.

No API keys or paid service accounts are required. Optional environment variables: `PORT` (default 5179); `PYTHON_BIN` (Python executable used by setup).

## Use

1. Select **Try a fictional example**, paste text, or import a PDF/image. Correct extracted text against every original page.
2. Choose SOAP, DAP, a general progress note or your own editable template. The template is scanned alongside the source.
3. Select **Find identifying details**. Review the full resulting prompt, not just the list of hidden values. Add missed names or phrases under **Anything we missed?**, one per line, and rescan. You can also edit unnecessary context out of the prompt.
4. Confirm your privacy review, copy the prompt and paste it into your practice's approved AI tool. This app does not contact ChatGPT or generate a note itself.
5. Paste the response into **Restore your note**. Exact placeholders are replaced with their original values. Unknown or recognisably damaged tokens stop restoration. Omitted placeholders are reported; the app cannot determine whether the AI omitted a clinically important fact.
6. Review the restored note against the original and copy it to your clinical record system. Then clear this client.

Refreshing or closing the tab loses the restoration map. Use one client per workflow. Clearing the app does not erase the operating system clipboard, clipboard history or an external AI conversation. Browser/session recovery, extensions, operating system swap and crash recovery are outside this prototype's control; clearing is not a forensic secure-erasure guarantee.

## What is implemented

- Local Presidio Analyzer and Anonymizer, with spaCy's small English model.
- Australian phone and Medicare-like candidates, labelled NDIS/client IDs, dates and addresses; Presidio's supported Australian identifiers; person/location detection; additional organisation candidates.
- Supplementary detection of repeated name parts and exact clinician-supplied phrases. Each exact original value has a reversible token. Different spellings/name variants are not assumed to be the same person.
- Session-specific random tokens and exact one-pass restoration in the browser. No map is sent to an AI provider.
- Selectable PDF text, OCR for scanned PDFs and single-frame images. OCR every PDF page is on by default to reduce missed scanned regions. Maximum 12 MB, 20 PDF pages, 25 megapixels per raster and 60,000 characters per scan; over-limit documents fail instead of silently importing a subset.
- Editable source, template, outbound prompt and restored note; review gates reset when relevant content changes.
- Loopback-only Flask server, restricted Host/Origin, required custom request header, same-origin content policy, no analytics, no browser storage or database, `no-store` responses and in-memory upload streams.

The original PDF/image is **not redacted**. Only extracted text passes through detection. Never assume the original document, its metadata or its images are safe to upload elsewhere.

## Limits before a real clinical pilot

This is reversible **pseudonymisation**, not guaranteed anonymisation. Context such as rare conditions, family relationships, small locations, dates and occupations can still identify a person. Detection can miss unfamiliar names and identifiers and can hide non-identifying text. The small English model is a prototype starting point, not a validated Australian clinical model. There is no handwritten-note accuracy claim.

Before using real records: assess representative Australian clinical material and OCR error rates; complete an appropriate privacy/security assessment and practice-specific review of external AI use; assess relevant Commonwealth and state/territory obligations; validate templates with clinicians; and choose an operational model for packaging, updates and support. Do not deploy this Flask prototype as a public multi-user service. It has no authentication, tenancy, durable record storage or production isolation.

Clinical judgement stays with the practitioner. The prompt discourages invented facts, but does not prevent AI errors. No real AI-generated clinical note was used in testing.

## Dependencies and tests

Runtime dependencies are listed in `requirements.txt`. No frontend build, JavaScript library, database or API subscription is required. Development tests use pytest and Node's built-in test runner.

```sh
.venv/bin/python -m pip install pytest
.venv/bin/python -m pytest tests/test_app.py -q
node --test tests/restore.test.js
```

OCR fixtures use a macOS system font, so the current OCR tests are Mac-specific. See `verification.md` for the completed checks and limits.

## Sources checked 11/09/2026

- [Presidio Anonymizer](https://microsoft.github.io/presidio/anonymizer/): replacement and reversible operations. The upstream docs now redirect to the Data Privacy Stack project.
- [Presidio supported entities](https://presidio.dataprivacystack.org/supported_entities/): built-in coverage and country-specific recognition.
- [OAIC guidance on commercially available AI](https://www.oaic.gov.au/privacy/privacy-guidance-for-organisations-and-government-agencies/guidance-on-privacy-and-the-use-of-commercially-available-ai-products): sensitive information, oversight and privacy assessment.
- [OAIC health privacy guide](https://www.oaic.gov.au/privacy/privacy-guidance-for-organisations-and-government-agencies/health-service-providers/guide-to-health-privacy/introduction-and-key-concepts): health information and re-identification risks.

## Licence and contributions

[MIT licence](LICENSE). You can use, adapt and share this project's code under those terms. Dependencies and language models retain their own licences. This project uses Presidio and is not affiliated with or endorsed by Microsoft.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). Use only fictional data in community discussions, issues and pull requests.
