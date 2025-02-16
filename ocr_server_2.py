import base64
import traceback
from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
from io import BytesIO
from gevent import monkey

monkey.patch_all()  # For async compatibility

app = Flask(__name__)

# Initialize OCR once (thread-safe)
ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)  # Set use_gpu=True if available

# Rate limiter (optional)
from flask_limiter import Limiter

limiter = Limiter(app=app, key_func=lambda: request.remote_addr)


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


@app.route('/extract_text', methods=['POST'])
def extract_text():
    try:
        data = request.get_json()
        if not data or "image" not in data:
            return jsonify({"error": "Missing image data"}), 400

        extracted_text = process_ocr(data["image"])
        return jsonify({"text": extracted_text})

    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "Processing failed"}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)