# EdgeVision 🔍

> A real-time, browser-based edge detection web app powered by Flask and OpenCV.

Upload any image and instantly visualize its edges using **Canny** or **Sobel** algorithms — with adjustable thresholds and a premium glassmorphism UI. No installation needed on the client side; just a browser.

---

## ✨ Features

- **Two edge detection algorithms** — Canny (multi-stage, single-pixel edges) and Sobel (gradient magnitude with weak/strong edge classification)
- **Real-time controls** — dual threshold sliders with 300ms debounce for smooth, live feedback
- **Side-by-side comparison** — original and processed images displayed together
- **Dark / Light theme** — persistent via `localStorage`, toggled with one click
- **Drag & drop upload** — or click to browse; supports PNG, JPG, WEBP up to 10 MB
- **One-click download** — saves the processed edge map as a timestamped PNG
- **Fully responsive** — works on desktop and mobile

---

## 🛠️ Tech Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Backend   | Python 3, Flask 3.1                 |
| CV Engine | OpenCV 4.11 (headless), NumPy 2.2   |
| Imaging   | Pillow 11.1                         |
| Frontend  | Vanilla HTML5, CSS3, JavaScript     |
| Fonts     | Inter (Google Fonts)                |

---

## 📁 Project Structure

```
Edge detection project/
├── app.py                  # Flask app — API routes & algorithm logic
├── requirements.txt        # Pinned Python dependencies
└── static/
    ├── index.html          # Single-page UI markup
    ├── style.css           # Glassmorphism design system + theme tokens
    └── script.js           # Frontend logic: upload, API calls, controls
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
# 1. Clone or extract the project
cd "Edge detection project"

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

---

## 🔌 API Reference

### `POST /api/process`

Processes an image and returns the edge-detected result.

**Request body (JSON):**

```json
{
  "image":     "<base64-encoded image string>",
  "algorithm": "canny",
  "low":       50,
  "high":      150
}
```

| Field       | Type    | Default    | Description                              |
|-------------|---------|------------|------------------------------------------|
| `image`     | string  | *required* | Raw base64 image (no `data:` prefix)     |
| `algorithm` | string  | `"canny"`  | `"canny"` or `"sobel"`                   |
| `low`       | integer | `50`       | Lower threshold (0–255)                  |
| `high`      | integer | `150`      | Upper threshold (0–255)                  |

**Success response (200):**

```json
{ "image": "<base64-encoded PNG>" }
```

**Error responses:** `400` for missing/invalid input, `500` for processing failures.

---

## 🧠 How the Algorithms Work

### Canny
1. Convert to greyscale
2. Apply 5×5 Gaussian blur (σ = 1.4)
3. Compute gradient magnitude and direction
4. Non-maximum suppression (thin edges to 1px)
5. Hysteresis thresholding — pixels above `high` are strong edges; pixels between `low` and `high` are weak edges (kept only if connected to a strong edge)

### Sobel
1. Convert to greyscale + Gaussian blur
2. Compute horizontal (Gx) and vertical (Gy) gradients
3. Magnitude M = √(Gx² + Gy²), normalised to 0–255
4. Three-class map: **strong** (M ≥ high → white), **weak** (low ≤ M < high → grey), **background** (M < low → black)

---

## ⚙️ Configuration

In `app.py`, one constant controls processing behaviour:

```python
MAX_DIMENSION = 2000  # px — images larger than this are proportionally downscaled
```

Reduce this value on memory-constrained hosts.

> **Production note:** The app runs in Flask's debug mode on port 5000 by default. For production, set `debug=False` and serve via Gunicorn or a similar WSGI server.

---

## 📦 Dependencies

| Package                      | Version     | License        |
|------------------------------|-------------|----------------|
| `flask`                      | 3.1.0       | BSD-3-Clause   |
| `opencv-python-headless`     | 4.11.0.86   | Apache-2.0     |
| `numpy`                      | 2.2.4       | BSD-3-Clause   |
| `pillow`                     | 11.1.0      | HPND           |

---

## 🗺️ Roadmap

- [ ] Laplacian of Gaussian (LoG) algorithm option
- [ ] Live webcam feed support
- [ ] Gradient magnitude histogram overlay on sliders
- [ ] Async processing with a task queue (Celery + Redis)
- [ ] Docker image for one-command deployment
- [ ] Interactive before/after slider (CSS clip-path drag)

---

## 📄 License

This project is open source. Feel free to use, modify, and distribute it.
