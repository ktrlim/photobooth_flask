from flask import Flask, jsonify, render_template, Response, request, send_file
import cv2
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
import io
import base64

app = Flask(__name__)
camera = cv2.VideoCapture(0)

# function to continuously stream video frames
def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# capture image and send as base64
@app.route('/capture', methods=['POST'])
def capture():
    """captures images"""
    success, frame = camera.read()
    if not success:
        return "Failed to capture image", 500

    # convert frame to PIL format
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(frame)

    # convert image to base64 to send to frontend
    img_io = io.BytesIO()
    image.save(img_io, 'JPEG')
    img_io.seek(0)
    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

    return {"image": f"data:image/jpeg;base64,{img_base64}"}

# receives images from frontend and stores them
@app.route('/save_photos', methods=['POST'])
def save_photos():
    global stored_images
    data = request.json
    stored_images = data.get("images", [])  # Store in memory
    return jsonify({"message": "Photos saved successfully"})

# sends images to frontend
@app.route('/get_photos', methods=['GET'])
def get_photos():
    return jsonify({"images": stored_images})

@app.route('/display')
def display():
    return render_template("display.html")

# apply color filter & generate photo strip
@app.route('/generate_strip', methods=['POST'])
def generate_strip():
    data = request.json
    images_data = data.get("images", [])
    filter_type = data.get("filter", "original")

    if not images_data:
        return "No images received", 400

    # Define strip size
    strip_width, strip_height = 400, 900
    strip_rows = len(images_data)
    strip = Image.new('RGB', (strip_width, strip_height), (255, 255, 255))

    target_height = strip_height // strip_rows
    target_width = strip_width

    # Process each image
    for idx, img_data in enumerate(images_data):
        img = Image.open(io.BytesIO(base64.b64decode(img_data.split(",")[1])))
        
        # Apply color filter
        if filter_type == "grayscale":
            img = ImageOps.grayscale(img).convert("RGB")
        elif filter_type == "sepia":
            sepia = np.array(img.convert("RGB"))
            tr = (sepia[:, :, 0] * 0.393 + sepia[:, :, 1] * 0.769 + sepia[:, :, 2] * 0.189)
            tg = (sepia[:, :, 0] * 0.349 + sepia[:, :, 1] * 0.686 + sepia[:, :, 2] * 0.168)
            tb = (sepia[:, :, 0] * 0.272 + sepia[:, :, 1] * 0.534 + sepia[:, :, 2] * 0.131)
            sepia[:, :, 0] = np.clip(tr, 0, 255)
            sepia[:, :, 1] = np.clip(tg, 0, 255)
            sepia[:, :, 2] = np.clip(tb, 0, 255)
            img = Image.fromarray(sepia)

        # Resize & paste into strip
        img = ImageOps.fit(img, (target_width, target_height))
        strip.paste(img, (0, idx * target_height))

    # Save strip to memory & send
    img_io = io.BytesIO()
    strip.save(img_io, 'JPEG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name="photo_strip.jpg")

# Video feed route
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Homepage
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)