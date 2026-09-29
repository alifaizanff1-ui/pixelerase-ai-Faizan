# PixelErase AI

Production-oriented, single-file frontend plus a local FastAPI/rembg background-removal API.

## Run locally

Python 3.10–3.12 is recommended for the broadest ONNX Runtime compatibility.

```bash
cd pixelerase-ai
python -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend:app --host 127.0.0.1 --port 8000
```

In another terminal, serve the frontend:

```bash
cd pixelerase-ai
python -m http.server 5500
```

Open `http://127.0.0.1:5500`. The first processed image downloads the selected rembg model (U²-Net by default), so it can take longer. Later requests reuse the in-memory session.

## API

- `GET /health` — readiness check.
- `POST /api/remove-background` — multipart field `file`; accepts JPG, PNG, or WEBP up to 15 MB; returns an `image/png` response.

The self-contained `index.html` calls `http://127.0.0.1:8000` by default. Before its script runs, set `window.PIXELERASE_API_URL` to use another API origin, or run this in the browser console once:

```js
localStorage.setItem('pixelerase_api', 'https://api.example.com')
```

For production: serve both components over HTTPS, set `ALLOWED_ORIGINS` to the exact frontend origin, add authentication/rate limiting, review infrastructure logs and retention, scan uploads, cap dimensions as well as bytes, and confirm the rembg/model licenses fit your use.

Example:

```bash
ALLOWED_ORIGINS=https://app.example.com REMBG_MODEL=u2net uvicorn backend:app --host 0.0.0.0 --port 8000
```
