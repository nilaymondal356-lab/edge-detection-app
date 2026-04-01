"""
Edge Detection Web Application — Flask Backend
Serves the frontend and provides an image processing API via OpenCV.
"""

import base64
import io

import cv2
import numpy as np
from flask import Flask, jsonify, request, send_from_directory
from PIL import Image

app = Flask(__name__, static_folder="static", static_url_path="/static")

MAX_DIMENSION = 2000  # px – cap large images for speed


# ── Helpers ─────────────────────────────────────────────────────────

def decode_image(b64: str) -> np.ndarray:
    """Base64 string → OpenCV BGR image (numpy array)."""
    img_bytes = base64.b64decode(b64)
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    # Down-scale if too large
    w, h = pil_img.size
    if max(w, h) > MAX_DIMENSION:
        scale = MAX_DIMENSION / max(w, h)
        pil_img = pil_img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def encode_image(img: np.ndarray) -> str:
    """OpenCV image → base64 PNG string."""
    _, buf = cv2.imencode(".png", img)
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def apply_canny(img: np.ndarray, low: int, high: int) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.4)
    # Ensure low <= high so both sliders always have an effect
    lo, hi = min(low, high), max(low, high)
    return cv2.Canny(blurred, lo, hi)


def apply_sobel(img: np.ndarray, low: int, high: int) -> np.ndarray:
    """Sobel with double-thresholding: strong edges (>high) are white,
    weak edges (between low and high) are gray, rest is black."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.4)
    sobel_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(sobel_x ** 2 + sobel_y ** 2)
    magnitude = np.uint8(255 * magnitude / magnitude.max()) if magnitude.max() > 0 else np.uint8(magnitude)

    lo, hi = min(low, high), max(low, high)

    # Double-threshold: strong edges white, weak edges gray
    edges = np.zeros_like(magnitude)
    edges[magnitude >= hi] = 255          # strong edges
    edges[(magnitude >= lo) & (magnitude < hi)] = 128  # weak edges
    return edges


ALGORITHMS = {
    "canny": apply_canny,
    "sobel": apply_sobel,
}


# ── Routes ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/process", methods=["POST"])
def process():
    data = request.get_json(silent=True)
    if not data or "image" not in data:
        return jsonify({"error": "No image provided"}), 400

    algorithm = data.get("algorithm", "canny").lower()
    low = int(data.get("low", 50))
    high = int(data.get("high", 150))

    if algorithm not in ALGORITHMS:
        return jsonify({"error": f"Unknown algorithm: {algorithm}"}), 400

    try:
        img = decode_image(data["image"])
        edges = ALGORITHMS[algorithm](img, low, high)
        result_b64 = encode_image(edges)
        return jsonify({"image": result_b64})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── Entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
