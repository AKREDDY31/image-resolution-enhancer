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
      grid-template-columns: 370px 1fr;
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
    input[type="file"],
    select {
      width: 100%;
      padding: 13px 14px;
      border: 1px solid rgba(102, 85, 68, 0.18);
      border-radius: 16px;
      background: rgba(255,255,255,0.86);
      color: var(--ink);
      font: inherit;
    }
    input[type="range"] {
      width: 100%;
      accent-color: var(--accent);
    }
    .range-value {
      color: var(--accent-dark);
      font-size: 1.15rem;
      font-weight: 800;
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
        <div class="helper">Balanced settings usually work best for portraits, product shots, and compressed images.</div>
        <div class="field">
          <label for="file">Image</label>
          <input id="file" type="file" name="file" accept=".png,.jpg,.jpeg" required>
        </div>
        <div class="field">
          <label for="upscale_mode">Enhancement profile</label>
          <select id="upscale_mode" name="upscale_mode">
            {% for label, value in upscale_options.items() %}
              <option value="{{ value }}" {% if form_values.upscale_mode == value %}selected{% endif %}>{{ label }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="field">
          <div class="inline">
            <label for="scale_percent">Scale</label>
            <strong class="range-value">{{ form_values.scale_percent }}%</strong>
          </div>
          <input id="scale_percent" type="range" name="scale_percent" min="100" max="400" step="50" value="{{ form_values.scale_percent }}" oninput="this.previousElementSibling.querySelector('strong').textContent = this.value + '%'">
        </div>
        <div class="field">
          <label for="decompress_mode">Compression cleanup</label>
          <select id="decompress_mode" name="decompress_mode">
            {% for label, value in decompress_options.items() %}
              <option value="{{ value }}" {% if form_values.decompress_mode == value %}selected{% endif %}>{{ label }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="field checkbox">
          <input id="polish_enabled" type="checkbox" name="polish_enabled" value="1" {% if form_values.polish_enabled %}checked{% endif %}>
          <label for="polish_enabled" style="margin: 0;">Refine fine details</label>
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
