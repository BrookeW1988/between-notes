import io
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from privacy import mask
from documents import extract
from app import app
from PIL import Image, ImageDraw, ImageFont


def test_roundtrip_and_identifiers():
    source = 'Client: Maya Lawson\nDOB: 14/03/1988\nPhone: 0412 345 678\nEmail: maya@example.com\nNDIS: 431 234 567\nAddress: 24 Banksia Road, Fremantle WA 6160\nMaya reported pain 4/10. No pain at rest. Practised for 15 minutes.'
    result = mask(source, ['Maya', '6160'])
    for secret in ['Maya', 'Lawson', '14/03/1988', '0412', 'maya@example.com', '431 234 567', 'Banksia', '6160']:
        assert secret not in result['text']
    assert '4/10' in result['text'] and '15 minutes' in result['text'] and 'No pain at rest' in result['text']
    restored = re.sub(r'\[\[[^\]]+\]\]', lambda m: result['mapping'][m[0]], result['text'])
    assert restored == source


def test_session_separation():
    assert mask('Client: Maya Lawson')['mapping'].keys() != mask('Client: Maya Lawson')['mapping'].keys()


def test_custom_terms_and_overlap():
    result = mask('Maya Lawson met Maya. Maya Lawson.', ['Maya Lawson', 'Maya'])
    assert 'Maya' not in result['text']
    assert len(result['mapping']) == 2


def test_http_boundaries():
    client = app.test_client()
    assert client.get('/').headers['Cache-Control'] == 'no-store'
    assert client.post('/api/mask',json={'text':'hello'}).status_code == 403
    assert client.post('/api/mask',json={'text':'hello'},headers={'X-Clinical-Notes':'local','Origin':'https://evil.example'}).status_code == 403
    assert client.get('/',headers={'Host':'evil.example'}).status_code == 400
    assert client.post('/api/mask',json={'text':5},headers={'X-Clinical-Notes':'local'}).status_code == 400
    assert client.post('/api/mask',json={'text':'hello','extra':'oops'},headers={'X-Clinical-Notes':'local'}).status_code == 400


def fixture_image():
    img = Image.new('RGB',(1600,600),'white')
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',38)
    draw.multiline_text((60,60),'Client: Maya Lawson\nPain: 4/10. No pain at rest.\nPractised for 15 minutes.',fill='black',font=font,spacing=20)
    return img


def test_image_ocr():
    image=fixture_image(); buf=io.BytesIO();image.save(buf,format='PNG')
    result=extract(buf.getvalue(),'scan.png')
    assert 'Maya Lawson' in result['text'] and '15 minutes' in result['text']


def test_scanned_pdf():
    image=fixture_image();buf=io.BytesIO();image.save(buf,format='PDF')
    result=extract(buf.getvalue(),'scan.pdf',True)
    assert 'Maya Lawson' in result['text'] and len(result['pages'])==1


def test_bad_pdf():
    import pytest
    with pytest.raises(ValueError):extract(b'%PDF-broken','broken.pdf')


def test_first_name_reused_without_manual_help():
    result=mask('Client: Maya Lawson\nMaya reported no pain. Lawson completed the task.')
    assert 'Maya' not in result['text'] and 'Lawson' not in result['text']


def test_no_network_during_detection(monkeypatch):
    import socket
    def blocked(*args, **kwargs):
        raise AssertionError('Detection attempted a network connection')
    monkeypatch.setattr(socket.socket, 'connect', blocked)
    result=mask('Client: Noor Haddad\nEmail: noor@example.com\nWebsite: https://example.com\nPhone: 0412 345 678')
    assert 'noor@example.com' not in result['text']


def test_upload_stream_stays_in_memory():
    from app import MemoryRequest
    stream=MemoryRequest.from_values()._get_file_stream(2_000_000,'application/pdf')
    assert isinstance(stream,io.BytesIO)


def test_api_upload_ocr():
    image=fixture_image();buf=io.BytesIO();image.save(buf,format='PNG');buf.seek(0)
    response=app.test_client().post('/api/extract',data={'file':(buf,'fictional.png')},headers={'X-Clinical-Notes':'local'})
    assert response.status_code==200 and 'Maya Lawson' in response.json['text']


def test_text_pdf_and_page_limit():
    import pytest
    # Small hand-authored PDF fixture with selectable text; no PDF writer dependency.
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    content=b'BT /F1 18 Tf 50 700 Td (Client: Maya Lawson. No pain at rest.) Tj ET'
    objects.append(b'<< /Length '+str(len(content)).encode()+b' >>\nstream\n'+content+b'\nendstream')
    pdf=b'%PDF-1.4\n';offsets=[0]
    for i,obj in enumerate(objects,1):
        offsets.append(len(pdf));pdf+=str(i).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
    xref=len(pdf);pdf+=b'xref\n0 6\n0000000000 65535 f \n'+b''.join(f'{n:010d} 00000 n \n'.encode() for n in offsets[1:])+b'trailer << /Size 6 /Root 1 0 R >>\nstartxref\n'+str(xref).encode()+b'\n%%EOF'
    result=extract(pdf,'text.pdf')
    assert 'Maya Lawson' in result['text'] and result['pages'][0]['method']=='Selectable text'
    import pypdfium2 as pdfium
    doc=pdfium.PdfDocument.new()
    for _ in range(21):doc.new_page(100,100)
    data=io.BytesIO();doc.save(data);doc.close()
    with pytest.raises(ValueError,match='20 pages'):extract(data.getvalue(),'too-many.pdf')
