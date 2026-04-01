"""
Edge Detection Web Application — Flask Backend
Serves the frontend and provides an image processing API via OpenCV.
Optimised for deployment on Render free tier (512 MB RAM).
"""

import base64
import gc
import io
import logging

import cv2
import numpy as np
from flask import Flask, jsonify, request, send_from_directory
from PIL import Image

# ── App setup ───────────────────────────────────────────────────────

app = Flask(__name__, static_folder="static", static_url_path="/static")

# Cap very large images to keep memory in check on Render free tier.
# The optimised Sobel (float32 + in-place) handles 2000px fine within 512 MB.
MAX_DIMENSION = 2000  # px

# Make sure errors/info show up in Render's log viewer
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    lo, hi = min(low, high), max(low, high)
    return cv2.Canny(blurred, lo, hi)


def apply_sobel(img: np.ndarray, low: int, high: int) -> np.ndarray:
    """Memory-optimised Sobel with double-thresholding.

    Uses CV_32F instead of CV_64F (halves memory) and accumulates
    magnitude in-place to avoid holding 4+ large arrays at once.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.4)

    # Use float32 instead of float64 — same visual result, half the RAM
    sobel_x = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)

    # Compute magnitude in-place
    np.multiply(sobel_x, sobel_x, out=sobel_x)
    np.multiply(sobel_y, sobel_y, out=sobel_y)
    np.add(sobel_x, sobel_y, out=sobel_x)  # sobel_x now holds x²+y²
    del sobel_y                              # free immediately
    np.sqrt(sobel_x, out=sobel_x)           # sobel_x now holds magnitude

    mag_max = sobel_x.max()
    if mag_max > 0:
        np.multiply(sobel_x, 255.0 / mag_max, out=sobel_x)

    magnitude = sobel_x.astype(np.uint8)
    del sobel_x
    gc.collect()

    lo, hi = min(low, high), max(low, high)

    edges = np.zeros_like(magnitude)
    edges[magnitude >= hi] = 255
    edges[(magnitude >= lo) & (magnitude < hi)] = 128
    return edges


ALGORITHMS = {
    "canny": apply_canny,
    "sobel": apply_sobel,
}


def intensity_to_thresholds(intensity: int) -> tuple[int, int]:
    """Map a 1-100 intensity slider to (low, high) thresholds.

    intensity  1  → very few edges   → high thresholds (low=200, high=250)
    intensity 50  → balanced          → (low=105, high=155)
    intensity 100 → maximum detail    → low thresholds  (low=10, high=60)
    """
    intensity = max(1, min(100, intensity))
    # Linear interpolation: intensity 1→100  maps  low 200→10, high 250→60
    t = (intensity - 1) / 99.0  # normalise to 0..1
    low  = int(200 - t * 190)   # 200 → 10
    high = int(250 - t * 190)   # 250 → 60
    return low, high


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
    intensity = int(data.get("intensity", 50))
    low, high = intensity_to_thresholds(intensity)

    logger.info("Processing: algorithm=%s  intensity=%s  → low=%s high=%s",
                algorithm, intensity, low, high)

    if algorithm not in ALGORITHMS:
        return jsonify({"error": f"Unknown algorithm: {algorithm}"}), 400

    try:
        img = decode_image(data["image"])
        edges = ALGORITHMS[algorithm](img, low, high)
        del img  # free original image immediately
        gc.collect()
        result_b64 = encode_image(edges)
        del edges
        gc.collect()
        return jsonify({"image": result_b64})
    except Exception as exc:
        logger.exception("Image processing failed")
        return jsonify({"error": str(exc)}), 500


# ── Entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
