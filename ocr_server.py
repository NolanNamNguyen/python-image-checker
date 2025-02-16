import os
import base64
import uuid
import traceback
from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
from io import BytesIO

app = Flask(__name__)

# Initialize OCR once (to avoid reloading on every request)
ocr = PaddleOCR(use_angle_cls=True, lang='en')

TEMP_IMAGE_FOLDER = "temp_images"  # Store temporary images

# Ensure the folder exists
os.makedirs(TEMP_IMAGE_FOLDER, exist_ok=True)

def process_ocr(base64_string):
    try:
        # Generate a unique filename
        file_name = f"{uuid.uuid4().hex}.png"
        file_path = os.path.join(TEMP_IMAGE_FOLDER, file_name)

        # Decode base64 and save as PNG file
        base64_string = base64_string.split(",")[-1]  # Remove metadata if exists
        image_data = base64.b64decode(base64_string)

        with open(file_path, "wb") as f:
            f.write(image_data)

        # Perform OCR on the saved image
        result = ocr.ocr(file_path, cls=True)

        # Extract text from OCR result
        extracted_text = [word[1][0] for line in result for word in line if word]

        # Remove the temporary file
        # os.remove(file_path)

        return extracted_text

    except Exception as e:
        print(f"Error in OCR processing: {e}")
        return []

@app.route('/extract_text', methods=['POST'])
def extract_text():
    try:
        data = request.get_json()
        base64_image = data.get("image")

        if not base64_image:
            return jsonify({"error": "No image data provided"}), 400

        extracted_text = process_ocr(base64_image)

        return jsonify({"text": extracted_text})

    except Exception as e:
        error_message = traceback.format_exc()
        return jsonify({"error": "Internal Server Error", "details": str(e), "traceback": error_message}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
