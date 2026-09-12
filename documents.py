"""Extract text and OCR locally. Input files are never saved by this module."""
import io
import sys
from PIL import Image, ImageOps
import pypdfium2 as pdfium

MAX_PAGES = 20
MAX_PIXELS = 25_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


def ocr(image):
    if sys.platform == 'darwin':
        import Vision
        import Quartz
        from Foundation import NSData
        data = io.BytesIO()
        image.save(data, format='PNG')
        nsdata = NSData.dataWithBytes_length_(data.getvalue(), len(data.getvalue()))
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        request.setRecognitionLanguages_(['en-AU'])
        request.setUsesLanguageCorrection_(False)
        handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(nsdata, {})
        success, error = handler.performRequests_error_([request], None)
        if not success:
            raise ValueError('OCR could not read this image. Try a clearer scan.')
        return '\n'.join(r.topCandidates_(1)[0].string() for r in request.results())
    import pytesseract
    return pytesseract.image_to_string(image, lang='eng', timeout=45)


def extract(data, filename, force_ocr=False):
    pages = []
    if data.startswith(b'%PDF-'):
        try:
            doc = pdfium.PdfDocument(data)
        except Exception as exc:
            raise ValueError('This PDF could not be opened. Export an unlocked copy and try again.') from exc
        try:
            if len(doc) > MAX_PAGES:
                raise ValueError(f'Use a document of {MAX_PAGES} pages or fewer. No pages were imported.')
            for index in range(len(doc)):
                page = doc[index]
                textpage = page.get_textpage()
                text = textpage.get_text_range().strip()
                textpage.close()
                method = 'Selectable text'
                if force_ocr or not text:
                    width, height = page.get_size()
                    if width * height * 4 > MAX_PIXELS:
                        raise ValueError('A PDF page is too large to process safely. Export a smaller scan.')
                    bitmap = page.render(scale=2)
                    picture = bitmap.to_pil()
                    text = ocr(picture).strip()
                    picture.close()
                    bitmap.close()
                    method = 'OCR — check against original'
                page.close()
                if not text:
                    raise ValueError(f'Page {index+1} has no readable text. No pages were imported; check the original.')
                pages.append({'page': index + 1, 'method': method, 'text': text})
        finally:
            doc.close()
    else:
        try:
            with Image.open(io.BytesIO(data)) as img:
                if getattr(img, 'n_frames', 1) != 1:
                    raise ValueError('Multi-frame images are not supported. Export each page as a separate image or PDF.')
                if img.width * img.height > MAX_PIXELS:
                    raise ValueError('Image is too large. Use an image under 25 megapixels.')
                picture = ImageOps.exif_transpose(img).convert('RGB')
                text = ocr(picture).strip()
                picture.close()
        except (Image.UnidentifiedImageError, OSError) as exc:
            raise ValueError('Choose a readable PDF, PNG, JPEG or single-page TIFF.') from exc
        if not text:
            raise ValueError('No readable text found. Try a clearer image or paste the text.')
        pages.append({'page': 1, 'method': 'OCR — check against original', 'text': text})
    return {'text': '\n\n'.join(f"Page {p['page']}\n{p['text']}" for p in pages),
            'pages': [{'page': p['page'], 'method': p['method']} for p in pages],
            'warning': 'Only extracted text is imported. The original file is not redacted. For mixed text/scanned PDFs, select OCR every page and compare every page with the original.'}
