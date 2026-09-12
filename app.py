"""Single-user local prototype. No database, client logging or remote services."""
import logging
import os
import io
from flask import Flask, Request, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from privacy import mask
from documents import extract

class MemoryRequest(Request):
    def _get_file_stream(self, total_content_length, content_type, filename=None, content_length=None):
        # Werkzeug otherwise spills larger uploads into a temporary disk file.
        return io.BytesIO()


app = Flask(__name__)
app.request_class = MemoryRequest
app.config.update(MAX_CONTENT_LENGTH=12 * 1024 * 1024, MAX_FORM_MEMORY_SIZE=12 * 1024 * 1024,
                  TRUSTED_HOSTS=['localhost', '127.0.0.1'])
logging.getLogger('werkzeug').setLevel(logging.ERROR)


@app.before_request
def local_only():
    if request.remote_addr not in {'127.0.0.1', '::1'}:
        return jsonify(error='This prototype only accepts connections from this computer.'), 403
    if request.method == 'POST':
        # Browsers cannot submit cross-site forms or read this local service.
        if request.headers.get('X-Clinical-Notes') != 'local' or request.headers.get('Origin', request.host_url.rstrip('/')) != request.host_url.rstrip('/'):
            return jsonify(error='Open the app directly on this computer and try again.'), 403


@app.after_request
def private_response(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    return response


@app.get('/')
def home():
    return render_template('index.html')


@app.post('/api/mask')
def anonymise():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ValueError('Enter text to process.')
    text, extra = body.get('text'), body.get('extra', [])
    if not isinstance(text, str) or not text.strip() or len(text) > 60000:
        raise ValueError('Enter between 1 and 60,000 characters.')
    if not isinstance(extra, list) or len(extra) > 100 or any(not isinstance(v, str) or len(v) > 1000 for v in extra):
        raise ValueError('Use up to 100 additional details, one per line.')
    return jsonify(mask(text, extra))


@app.post('/api/extract')
def import_document():
    upload = request.files.get('file')
    if not upload:
        raise ValueError('Choose a document to import.')
    result = extract(upload.read(), upload.filename or '', request.form.get('ocr') == 'true')
    if len(result['text']) > 60000:
        raise ValueError('The extracted text exceeds 60,000 characters. Split the document before importing.')
    return jsonify(result)


@app.errorhandler(Exception)
def handle_error(error):
    if isinstance(error, ValueError):
        return jsonify(error=str(error)), 400
    if isinstance(error, HTTPException):
        return jsonify(error='File is too large (12 MB maximum).' if error.code == 413 else error.description), error.code
    # Never echo source text, filenames or underlying exception details to logs.
    return jsonify(error='Local processing failed. Check the setup instructions and try again with synthetic text.'), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', '5179')), debug=False, threaded=False)
