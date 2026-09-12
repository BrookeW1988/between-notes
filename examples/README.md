# Fictional test PDFs

Every detail is invented. These are software fixtures, not clinical guidance.

- **fictional-client.pdf**: a normal PDF with selectable text. Turn off **OCR every PDF page** to exercise text extraction.
- **fictional-client-scanned.pdf**: the same page saved as an image-only PDF with no text layer. Use it to exercise OCR. This is a clean synthetic scan; success does not establish handwriting or poor-scan accuracy.

## Try the whole workflow

1. Import either PDF and compare the imported text with the original.
2. Select SOAP and find identifying details.
3. Check the full name, first-name references, partner, clinician, DOB, address, telephone, email, NDIS candidate and session date. Detection is fallible; add anything missed using **Anything we missed?** and rescan.
4. Review the lantern-parade sentence. It illustrates context that may identify a person even after direct identifiers are hidden; remove it from the prompt if unnecessary.
5. Copy the reviewed prompt to an AI tool and return its response to the restoration step.
6. Check that names restore correctly and clinically relevant details remain accurate: pain **4/10 while chopping**, **no pain at rest**, **15 minutes**, **two verbal prompts**, **no swelling**, and review in **two weeks**. Check that no facts were invented.

Do not upload the original PDF to an external AI tool as a substitute for the reviewed prompt. The app only processes extracted text; it does not redact the original PDF.
