from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
import base64
import os
from io import BytesIO
from PIL import Image
import uuid  # For generating unique file names

app = Flask(__name__)
ocr = PaddleOCR(use_angle_cls=True, lang='en')  # Initialize PaddleOCR

UPLOAD_FOLDER = "uploaded_images"  # Directory to store images
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure folder exists

@app.route('/extract_text', methods=['POST'])
def extract_text():
    try:
        data = request.get_json()
        base64_image = data.get("image")

        if not base64_image:
            return jsonify({"error": "No image data provided"}), 400

        # Remove metadata prefix (if exists)
        if base64_image.startswith("data:image"):
            base64_image = base64_image.split(",")[1]

        # Decode base64 string
        image_data = base64.b64decode(base64_image)

        # Generate a unique file name
        file_name = f"{uuid.uuid4().hex}.png"
        file_path = os.path.join(UPLOAD_FOLDER, file_name)

        # Save image to file
        with open(file_path, "wb") as f:
            f.write(image_data)

        print(f"Image saved at: {file_path}")  # Debugging: Check file path

        # Perform OCR on the saved file
        result = ocr.ocr(file_path, rec=True)

        # Debug: Print raw OCR output
        print("OCR Raw Output:", result)

        # If OCR returns None, return a message
        if not result or all(not line for line in result):
            return jsonify({"error": "No text detected in image"}), 400

        # Extract text safely
        extracted_text = [word[1][0] for line in result for word in line if word]

        # Cleanup: Remove the saved image file after OCR
        # os.remove(file_path)

        return jsonify({"text": extracted_text})

    except Exception as e:
        import traceback
        print("Error:", traceback.format_exc())  # Print full error traceback
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)