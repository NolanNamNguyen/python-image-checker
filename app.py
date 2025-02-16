import paddle
paddle.version.commit = 'bdaa3b4878d0d3405933b4903bcd4b1f48c9446c'

import base64
import traceback
from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
from io import BytesIO
from gevent import monkey
from gevent import Timeout
from werkzeug.exceptions import HTTPException
import psutil


monkey.patch_all()  # For async compatibility

app = Flask(__name__)

# Load configurations from config.py
app.config.from_pyfile('config.py')

# Initialize OCR once (thread-safe)
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='en',
    use_gpu=False,
    enable_mkldnn=False,  # Disable MKLDNN temporarily
    det_limit_side_len=1024,
    rec_algorithm='SVTR_LCNet',
    use_pdserving=False  # Add this line
)

# Rate limiter (optional)
from flask_limiter import Limiter

limiter = Limiter(app=app, key_func=lambda: request.remote_addr)


# Add keep-alive headers
@app.after_request
def add_headers(response):
    response.headers['Connection'] = 'keep-alive'
    response.headers['Keep-Alive'] = 'timeout=300, max=1000'
    return response


# Concurrent processing middleware
class ConcurrentOCR:
    def __init__(self, app):
        self.app = app
        self.semaphore = gevent.lock.BoundedSemaphore(100)  # Max concurrent

    def __call__(self, environ, start_response):
        with self.semaphore:
            return self.app(environ, start_response)


app.wsgi_app = ConcurrentOCR(app.wsgi_app)


# Error handling
@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    app.logger.error(f"Unhandled Exception: {str(e)}")
    return jsonify(error="Internal server error"), 500


# OCR processing function
def process_ocr(base64_string):
    try:
        # Remove metadata if exists and decode
        header, encoded = base64_string.split(",", 1) if "," in base64_string else ("", base64_string)
        image_data = base64.b64decode(encoded)

        # Use in-memory bytes instead of temp files
        image_stream = BytesIO(image_data)

        # Perform OCR
        result = ocr.ocr(image_stream.read(), cls=True)

        return [word[1][0] for line in result for word in line if word]

    except Exception as e:
        app.logger.error(f"OCR Error: {str(e)}")
        return []


# Main endpoint
@app.route('/extract_text', methods=['POST'])
@limiter.limit("200/minute")  # Increased limit
def extract_text():
    try:
        with Timeout(60):  # 1 minute timeout per request
            data = request.get_json()
            if not data or "image" not in data:
                return jsonify({"error": "Missing image data"}), 400

            extracted_text = process_ocr(data["image"])
            return jsonify({"text": extracted_text})

    except Timeout:
        app.logger.warning("Request timed out")
        return jsonify({"error": "Processing timeout"}), 504
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "Processing failed"}), 500


# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        "status": "ok",
        "concurrent": len(gevent.getcurrent().threadpool)
    })


# Metrics endpoint
@app.route('/metrics')
def metrics():
    process = psutil.Process()
    return jsonify({
        "memory_mb": process.memory_info().rss // 1024 // 1024,
        "cpu_percent": process.cpu_percent(),
        "active_requests": len(gevent.getcurrent().threadpool)
    })


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
