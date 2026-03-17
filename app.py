import base64
import io
import json
import os

import requests
from dotenv import load_dotenv
from flask import Flask, render_template_string, request
from PIL import Image

load_dotenv()

app = Flask(__name__)

CLAID_API_URL = "https://api.claid.ai/v1/image/edit/upload"
CLAID_API_KEY = os.getenv("CLAID_API_KEY", "").strip()
UPSCALE_OPTIONS = {
    "Faces": "faces",
    "Photo": "photo",
    "Smart Enhance": "smart_enhance",
    "Smart Resize": "smart_resize",
    "Digital Art": "digital_art",
}
DECOMPRESS_OPTIONS = {
    "Off": "off",
    "Auto": "auto",
    "Moderate": "moderate",
    "Strong": "strong",
}

PAGE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Image Restoration</title>
  <style>
    :root {
      --bg: #f4efe3;
      --panel: #fffaf2;
      --ink: #1f1b16;
      --muted: #736658;
      --accent: #d55d3a;
      --accent-dark: #8f341f;
      --line: #e7d7c5;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top left, #f9d7b8 0, transparent 26%),
        radial-gradient(circle at bottom right, #efd7b8 0, transparent 24%),
        var(--bg);
      color: var(--ink);
    }
    .shell {
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }
    .hero {
      margin-bottom: 24px;
      padding: 28px;
      border: 1px solid var(--line);
      background: linear-gradient(135deg, rgba(255,250,242,0.98), rgba(245,229,206,0.92));
      border-radius: 24px;
      box-shadow: 0 18px 60px rgba(93, 53, 31, 0.10);
    }
    .eyebrow {
      display: inline-block;
      margin-bottom: 10px;
      padding: 6px 10px;
      border-radius: 999px;
      background: #f3dfcc;
      color: var(--accent-dark);
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    h1 {
      margin: 0 0 10px;
      font-size: clamp(2.2rem, 5vw, 4.4rem);
      line-height: 0.95;
    }
    .sub {
      margin: 0;
      max-width: 720px;
      color: var(--muted);
      font-size: 1.05rem;
    }
    .grid {
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 24px;
      align-items: start;
    }
    .card {
      border: 1px solid var(--line);
      background: rgba(255, 250, 242, 0.94);
      border-radius: 24px;
      padding: 22px;
      box-shadow: 0 12px 40px rgba(93, 53, 31, 0.08);
    }
    label {
      display: block;
      margin-bottom: 8px;
      font-size: 0.95rem;
      font-weight: 700;
    }
    .field {
      margin-bottom: 18px;
    }
    input[type="file"],
    select {
      width: 100%;
      padding: 12px 14px;
      border: 1px solid #d9c5ae;
      border-radius: 14px;
      background: white;
      color: var(--ink);
      font: inherit;
    }
    input[type="range"] {
      width: 100%;
      accent-color: var(--accent);
    }
    .inline {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }
    .checkbox {
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--muted);
      font-size: 0.95rem;
    }
    button {
      width: 100%;
      border: 0;
      border-radius: 16px;
      padding: 14px 18px;
      background: linear-gradient(135deg, var(--accent), #ef8b57);
      color: white;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }
    button:hover { filter: brightness(0.98); }
    .note, .error {
      margin-bottom: 18px;
      padding: 12px 14px;
      border-radius: 14px;
      font-size: 0.95rem;
    }
    .note {
      background: #fff1dc;
      color: #76461e;
      border: 1px solid #efd1a7;
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
      border-radius: 20px;
      overflow: hidden;
      background: white;
    }
    .preview img {
      display: block;
      width: 100%;
      height: auto;
    }
    .preview .meta {
      padding: 14px 16px;
      border-top: 1px solid var(--line);
    }
    .preview h2 {
      margin: 0 0 6px;
      font-size: 1rem;
    }
    .preview p {
      margin: 0;
      color: var(--muted);
      font-size: 0.92rem;
    }
    .download {
      display: inline-block;
      margin-top: 14px;
      color: var(--accent-dark);
      text-decoration: none;
      font-weight: 700;
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
      <div class="eyebrow">Claid.ai Powered</div>
      <h1>Restore images without running heavy local models.</h1>
      <p class="sub">
        Upload a photo, choose the enhancement style, and let Claid handle restoration and upscaling.
      </p>
    </section>
    <section class="grid">
      <form class="card" method="post" enctype="multipart/form-data">
        {% if not api_key_loaded %}
          <div class="error">CLAID_API_KEY is not configured on the server.</div>
        {% else %}
          <div class="note">CLAID_API_KEY is loaded from environment variables.</div>
        {% endif %}
        {% if error %}
          <div class="error">{{ error }}</div>
        {% endif %}
        <div class="field">
          <label for="file">Upload image</label>
          <input id="file" type="file" name="file" accept=".png,.jpg,.jpeg" required>
        </div>
        <div class="field">
          <label for="upscale_mode">Upscale model</label>
          <select id="upscale_mode" name="upscale_mode">
            {% for label, value in upscale_options.items() %}
              <option value="{{ value }}" {% if form_values.upscale_mode == value %}selected{% endif %}>{{ label }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="field">
          <div class="inline">
            <label for="scale_percent">Scale</label>
            <strong>{{ form_values.scale_percent }}%</strong>
          </div>
          <input id="scale_percent" type="range" name="scale_percent" min="100" max="400" step="50" value="{{ form_values.scale_percent }}" oninput="this.previousElementSibling.querySelector('strong').textContent = this.value + '%'">
        </div>
        <div class="field">
          <label for="decompress_mode">JPEG artifact removal</label>
          <select id="decompress_mode" name="decompress_mode">
            {% for label, value in decompress_options.items() %}
              <option value="{{ value }}" {% if form_values.decompress_mode == value %}selected{% endif %}>{{ label }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="field checkbox">
          <input id="polish_enabled" type="checkbox" name="polish_enabled" value="1" {% if form_values.polish_enabled %}checked{% endif %}>
          <label for="polish_enabled" style="margin: 0;">Polish fine details</label>
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
                <p>Uploaded image before Claid restoration.</p>
              </div>
            </article>
            <article class="preview">
              <img src="data:image/png;base64,{{ result_image }}" alt="Enhanced image">
              <div class="meta">
                <h2>Enhanced</h2>
                <p>Restored using Claid.ai API.</p>
                <a class="download" href="data:image/png;base64,{{ result_image }}" download="enhanced_image.png">Download enhanced image</a>
              </div>
            </article>
          </div>
        {% else %}
          <div class="note">Upload an image on the left to generate a restored version here.</div>
        {% endif %}
      </section>
    </section>
  </main>
</body>
</html>
"""


def build_claid_payload(
    upscale_mode: str,
    scale_percent: int,
    decompress_mode: str,
    polish_enabled: bool,
) -> dict:
    operations = {
        "restorations": {
            "upscale": upscale_mode,
            "polish": polish_enabled,
        },
        "resizing": {
            "width": f"{scale_percent}%",
            "height": f"{scale_percent}%",
        },
    }
    if decompress_mode != "off":
        operations["restorations"]["decompress"] = decompress_mode

    return {
        "operations": operations,
        "output": {
            "format": {
                "type": "png",
            }
        },
    }


def extract_output_url(response_json: dict) -> str:
    data = response_json.get("data", {})
    output = data.get("output", {})
    tmp_url = output.get("tmp_url")
    if tmp_url:
        return tmp_url

    outputs = data.get("outputs", [])
    if outputs and isinstance(outputs[0], dict):
        tmp_url = outputs[0].get("tmp_url")
        if tmp_url:
            return tmp_url

    raise RuntimeError("Claid response did not include a downloadable output URL.")


def restore_image_with_claid(
    image_bytes: bytes,
    file_name: str,
    upscale_mode: str,
    scale_percent: int,
    decompress_mode: str,
    polish_enabled: bool,
) -> bytes:
    if not CLAID_API_KEY:
        raise RuntimeError("CLAID_API_KEY is missing. Set it in your environment.")

    payload = build_claid_payload(
        upscale_mode=upscale_mode,
        scale_percent=scale_percent,
        decompress_mode=decompress_mode,
        polish_enabled=polish_enabled,
    )
    files = {
        "file": (file_name, image_bytes),
        "data": (None, json.dumps(payload), "application/json"),
    }
    headers = {
        "Authorization": f"Bearer {CLAID_API_KEY}",
    }

    response = requests.post(CLAID_API_URL, headers=headers, files=files, timeout=120)
    response.raise_for_status()

    output_url = extract_output_url(response.json())
    output_response = requests.get(output_url, timeout=120)
    output_response.raise_for_status()
    return output_response.content


def image_bytes_to_base64(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def render_page(error: str = "", input_image: str = "", result_image: str = "", form_values: dict | None = None):
    values = {
        "upscale_mode": UPSCALE_OPTIONS["Faces"],
        "scale_percent": 200,
        "decompress_mode": DECOMPRESS_OPTIONS["Auto"],
        "polish_enabled": True,
    }
    if form_values:
        values.update(form_values)

    return render_template_string(
        PAGE_TEMPLATE,
        api_key_loaded=bool(CLAID_API_KEY),
        error=error,
        input_image=input_image,
        result_image=result_image,
        upscale_options=UPSCALE_OPTIONS,
        decompress_options=DECOMPRESS_OPTIONS,
        form_values=values,
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_page()

    uploaded_file = request.files.get("file")
    if uploaded_file is None or not uploaded_file.filename:
        return render_page(error="Please choose an image file before submitting.")

    upscale_mode = request.form.get("upscale_mode", UPSCALE_OPTIONS["Faces"])
    decompress_mode = request.form.get("decompress_mode", DECOMPRESS_OPTIONS["Auto"])
    scale_percent = int(request.form.get("scale_percent", "200"))
    polish_enabled = request.form.get("polish_enabled") == "1"
    form_values = {
        "upscale_mode": upscale_mode,
        "scale_percent": scale_percent,
        "decompress_mode": decompress_mode,
        "polish_enabled": polish_enabled,
    }

    input_bytes = uploaded_file.read()
    input_base64 = image_bytes_to_base64(input_bytes)

    try:
        result_bytes = restore_image_with_claid(
            image_bytes=input_bytes,
            file_name=uploaded_file.filename,
            upscale_mode=upscale_mode,
            scale_percent=scale_percent,
            decompress_mode=decompress_mode,
            polish_enabled=polish_enabled,
        )
    except requests.HTTPError as exc:
        details = exc.response.text if exc.response is not None else str(exc)
        return render_page(error=f"Claid API request failed.\n\n{details}", input_image=input_base64, form_values=form_values)
    except Exception as exc:
        return render_page(error=str(exc), input_image=input_base64, form_values=form_values)

    result_base64 = base64.b64encode(result_bytes).decode("utf-8")
    return render_page(input_image=input_base64, result_image=result_base64, form_values=form_values)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
