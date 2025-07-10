from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image, ImageOps
import io
import base64

app = Flask(__name__)

# Store images in memory
stored_images = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture', methods=['POST'])
def capture():
    data = request.get_json()
    image_data = data['image']

    # Decode base64 image from browser
    header, encoded = image_data.split(",", 1)
    img_bytes = base64.b64decode(encoded)
    image = Image.open(io.BytesIO(img_bytes))

    # Return image back as base64 for preview
    img_io = io.BytesIO()
    image.save(img_io, 'JPEG')
    img_io.seek(0)
    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
    return jsonify({"image": f"data:image/jpeg;base64,{img_base64}"})

@app.route('/save_photos', methods=['POST'])
def save_photos():
    global stored_images
    data = request.json
    stored_images = data.get("images", [])
    return jsonify({"message": "Photos saved successfully"})

@app.route('/get_photos', methods=['GET'])
def get_photos():
    return jsonify({"images": stored_images})

@app.route('/display')
def display():
    return render_template('display.html')

@app.route('/generate_strip', methods=['POST'])
def generate_strip():
    data = request.get_json()
    images_data = data.get("images", [])

    if not images_data:
        return "No images received", 400

    # Create the photostrip
    strip_width, strip_height = 400, 900
    strip_rows = len(images_data)
    strip = Image.new('RGB', (strip_width, strip_height), (255, 255, 255))
    target_height = strip_height // strip_rows

    for idx, img_data in enumerate(images_data):
        img = Image.open(io.BytesIO(base64.b64decode(img_data.split(",")[1])))
        img = ImageOps.fit(img, (strip_width, target_height))
        strip.paste(img, (0, idx * target_height))

    # Return as downloadable JPEG
    img_io = io.BytesIO()
    strip.save(img_io, 'JPEG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name="photo_strip.jpg")

if __name__ == '__main__':
    app.run(debug=False)