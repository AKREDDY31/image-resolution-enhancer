import base64
import io
import json
import os
import time

import requests
from dotenv import load_dotenv
from flask import Flask, render_template_string, request
from PIL import Image

load_dotenv()

app = Flask(__name__)

DEEP_IMAGE_API_URL = "https://deep-image.ai/rest_api/process_result"
DEEP_IMAGE_RESULT_URL = "https://deep-image.ai/rest_api/result"
DEEP_IMAGE_API_KEY = os.getenv("DEEP_IMAGE_API_KEY", "").strip()
DEFAULT_PARAMETERS = {
    "enhancements": ["denoise", "deblur", "light"],
    "width": "200%",
}

PAGE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Image Restoration Studio</title>
  <style>
    :root {
      --bg: #f5f1ea;
      --panel: rgba(255, 252, 247, 0.88);
      --panel-strong: #fffdf9;
      --ink: #1d1713;
      --muted: #6d6256;
      --accent: #1f6c5c;
      --accent-soft: #dff0e7;
      --accent-dark: #164e42;
      --line: rgba(105, 88, 71, 0.14);
      --shadow: 0 24px 70px rgba(44, 31, 20, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Aptos", "Segoe UI", "Helvetica Neue", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(143, 199, 180, 0.28) 0, transparent 24%),
        radial-gradient(circle at top right, rgba(244, 210, 164, 0.26) 0, transparent 20%),
        linear-gradient(180deg, #faf7f1 0%, #f4eee6 100%),
        var(--bg);
      color: var(--ink);
    }
    .shell {
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }
    .hero {
      margin-bottom: 26px;
      padding: 34px;
      border: 1px solid var(--line);
      background:
        linear-gradient(135deg, rgba(255,253,249,0.95), rgba(242, 248, 245, 0.94)),
        var(--panel-strong);
      border-radius: 30px;
      box-shadow: var(--shadow);
    }
    h1 {
      margin: 0 0 12px;
      max-width: 900px;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(2.5rem, 5vw, 4.8rem);
      line-height: 0.98;
      letter-spacing: -0.04em;
    }
    .sub {
      margin: 0;
      max-width: 640px;
      color: var(--muted);
      font-size: 1.02rem;
      line-height: 1.7;
    }
    .grid {
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 24px;
      align-items: start;
    }
    .card {
      border: 1px solid var(--line);
      background: var(--panel);
      backdrop-filter: blur(14px);
      border-radius: 28px;
      padding: 24px;
      box-shadow: var(--shadow);
    }
    label {
      display: block;
      margin-bottom: 9px;
      font-size: 0.92rem;
      font-weight: 700;
      letter-spacing: 0.01em;
    }
    .field {
      margin-bottom: 20px;
    }
    input[type="file"] {
      width: 100%;
      padding: 13px 14px;
      border: 1px solid rgba(102, 85, 68, 0.18);
      border-radius: 16px;
      background: rgba(255,255,255,0.86);
      color: var(--ink);
      font: inherit;
    }
    button {
      width: 100%;
      border: 0;
      border-radius: 18px;
      padding: 15px 18px;
      background: linear-gradient(135deg, var(--accent), #4e8d74);
      color: white;
      font: inherit;
      font-weight: 700;
      letter-spacing: 0.01em;
      cursor: pointer;
      box-shadow: 0 18px 36px rgba(31, 108, 92, 0.22);
    }
    button:hover { filter: brightness(0.98); }
    .helper, .error {
      margin-bottom: 18px;
      padding: 13px 15px;
      border-radius: 16px;
      font-size: 0.95rem;
    }
    .helper {
      background: var(--accent-soft);
      color: var(--accent-dark);
      border: 1px solid rgba(31, 108, 92, 0.12);
    }
    .steps {
      display: grid;
      gap: 12px;
      margin: 18px 0 22px;
    }
    .step {
      padding: 14px 15px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: rgba(255,255,255,0.72);
    }
    .step strong {
      display: block;
      margin-bottom: 4px;
      font-size: 0.92rem;
    }
    .step span {
      color: var(--muted);
      font-size: 0.9rem;
      line-height: 1.5;
    }
    .error {
      background: #fde6e0;
      color: #8d2b1c;
      border: 1px solid #f2c0b4;
      white-space: pre-wrap;
    }
    .results {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 20px;
    }
    .preview {
      border: 1px solid var(--line);
      border-radius: 22px;
      overflow: hidden;
      background: white;
      box-shadow: 0 12px 36px rgba(44, 31, 20, 0.06);
    }
    .preview img {
      display: block;
      width: 100%;
      height: auto;
      background: #f7f4ef;
    }
    .preview .meta {
      padding: 16px 18px;
      border-top: 1px solid var(--line);
    }
    .preview h2 {
      margin: 0 0 6px;
      font-size: 1.02rem;
    }
    .preview p {
      margin: 0;
      color: var(--muted);
      font-size: 0.92rem;
      line-height: 1.55;
    }
    .download {
      display: inline-block;
      margin-top: 14px;
      color: var(--accent-dark);
      text-decoration: none;
      font-weight: 700;
    }
    .empty-state {
      min-height: 420px;
      display: grid;
      place-items: center;
      border: 1px dashed rgba(31, 108, 92, 0.18);
      border-radius: 22px;
      background:
        linear-gradient(135deg, rgba(255,255,255,0.82), rgba(241,247,244,0.9));
      color: var(--muted);
      text-align: center;
      padding: 26px;
    }
    .empty-state strong {
      display: block;
      margin-bottom: 8px;
      color: var(--ink);
      font-size: 1.1rem;
    }
    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr; }
      .results { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <h1>Image Restoration Studio</h1>
      <p class="sub">
        Upload an image, refine the restoration settings, and generate a cleaner, sharper result in seconds.
      </p>
    </section>
    <section class="grid">
      <form class="card" method="post" enctype="multipart/form-data">
        {% if not api_key_loaded %}
          <div class="error">The service is not configured correctly right now. Please try again shortly.</div>
        {% endif %}
        {% if error %}
          <div class="error">{{ error }}</div>
        {% endif %}
        <div class="helper">Upload a photo and the app will automatically clean noise, reduce blur, and enhance clarity.</div>
        <div class="steps">
          <div class="step">
            <strong>1. Upload</strong>
            <span>Add a JPG or PNG image from your device.</span>
          </div>
          <div class="step">
            <strong>2. Enhance</strong>
            <span>The image is processed with a fixed restoration preset tuned for general-quality improvement.</span>
          </div>
          <div class="step">
            <strong>3. Download</strong>
            <span>Preview the refined result and save it as a PNG.</span>
          </div>
        </div>
        <div class="field">
          <label for="file">Image</label>
          <input id="file" type="file" name="file" accept=".png,.jpg,.jpeg" required>
        </div>
        <button type="submit">Enhance Image</button>
      </form>
      <section class="card">
        {% if result_image %}
          <div class="results">
            <article class="preview">
              <img src="data:image/png;base64,{{ input_image }}" alt="Original image">
              <div class="meta">
                <h2>Original</h2>
                <p>Your uploaded image before enhancement.</p>
              </div>
            </article>
            <article class="preview">
              <img src="data:image/png;base64,{{ result_image }}" alt="Enhanced image">
              <div class="meta">
                <h2>Enhanced</h2>
                <p>The restored version is ready to preview and download.</p>
                <a class="download" href="data:image/png;base64,{{ result_image }}" download="enhanced_image.png">Download enhanced image</a>
              </div>
            </article>
          </div>
        {% else %}
          <div class="empty-state">
            <div>
              <strong>Result preview appears here</strong>
              Upload an image and run the enhancement to compare the original and restored versions side by side.
            </div>
          </div>
        {% endif %}
      </section>
    </section>
  </main>
</body>
</html>
"""


def build_deep_image_payload() -> dict:
    return dict(DEFAULT_PARAMETERS)


def poll_deep_image_result(job_id: str) -> str:
    headers = {"x-api-key": DEEP_IMAGE_API_KEY}
    for _ in range(20):
        response = requests.get(f"{DEEP_IMAGE_RESULT_URL}/{job_id}", headers=headers, timeout=60)
        response.raise_for_status()
        response_json = response.json()
        result_url = response_json.get("result_url")
        if result_url:
            return result_url
        if response_json.get("status") == "error":
            raise RuntimeError(response_json.get("description", "Image processing failed."))
        time.sleep(2)
    raise RuntimeError("Image processing timed out while waiting for the result.")


def restore_image_with_deep_image(
    image_bytes: bytes,
    file_name: str,
) -> bytes:
    if not DEEP_IMAGE_API_KEY:
        raise RuntimeError("DEEP_IMAGE_API_KEY is missing. Set it in your environment.")

    parameters = build_deep_image_payload()
    headers = {"x-api-key": DEEP_IMAGE_API_KEY}
    files = {
        "file": (file_name, image_bytes),
    }
    data = {
        "parameters": json.dumps(parameters),
    }

    response = requests.post(
        DEEP_IMAGE_API_URL,
        headers=headers,
        files=files,
        data=data,
        timeout=120,
    )
    response.raise_for_status()
    response_json = response.json()
    output_url = response_json.get("result_url")
    if not output_url:
        job_id = response_json.get("job")
        if not job_id:
            raise RuntimeError("The image service did not return a result URL or job id.")
        output_url = poll_deep_image_result(job_id)
    output_response = requests.get(output_url, timeout=120)
    output_response.raise_for_status()
    return output_response.content


def image_bytes_to_base64(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def render_page(error: str = "", input_image: str = "", result_image: str = "", form_values: dict | None = None):
    return render_template_string(
        PAGE_TEMPLATE,
        api_key_loaded=bool(DEEP_IMAGE_API_KEY),
        error=error,
        input_image=input_image,
        result_image=result_image,
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_page()

    uploaded_file = request.files.get("file")
    if uploaded_file is None or not uploaded_file.filename:
        return render_page(error="Please choose an image file before submitting.")

    input_bytes = uploaded_file.read()
    input_base64 = image_bytes_to_base64(input_bytes)

    try:
        result_bytes = restore_image_with_deep_image(
            image_bytes=input_bytes,
            file_name=uploaded_file.filename,
        )
    except requests.HTTPError as exc:
        details = exc.response.text if exc.response is not None else str(exc)
        return render_page(error=f"Image processing request failed.\n\n{details}", input_image=input_base64)
    except Exception as exc:
        return render_page(error=str(exc), input_image=input_base64)

    result_base64 = base64.b64encode(result_bytes).decode("utf-8")
    return render_page(input_image=input_base64, result_image=result_base64)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
