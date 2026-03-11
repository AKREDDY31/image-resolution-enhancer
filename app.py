import os
import urllib.request

import cv2
import numpy as np
import streamlit as st
import torch
from PIL import Image

from basicsr.archs.rrdbnet_arch import RRDBNet
from gfpgan import GFPGANer
from realesrgan import RealESRGANer

st.set_page_config(page_title="AI Image Restoration", layout="wide")
st.title("AI Image Restoration Platform")
st.write("Enhance blurry and low-resolution images using AI")

LOW_MEMORY_MODE = os.getenv("LOW_MEMORY_MODE", "0") == "1"
MAX_INPUT_DIM = int(os.getenv("MAX_INPUT_DIM", "1024" if LOW_MEMORY_MODE else "2048"))

# Keep CPU thread count low on small instances.
torch.set_num_threads(1)

os.makedirs("models", exist_ok=True)
os.makedirs("gfpgan/weights", exist_ok=True)

realesrgan_path = "models/RealESRGAN_x4plus.pth"
gfpgan_path = "models/GFPGANv1.4.pth"
detector_path = "gfpgan/weights/detection_Resnet50_Final.pth"
parsing_path = "gfpgan/weights/parsing_parsenet.pth"


def is_lfs_pointer_or_invalid(path, min_size_bytes=1024 * 1024):
    if not os.path.exists(path):
        return True
    if os.path.getsize(path) >= min_size_bytes:
        return False
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            header = f.read(200)
        return "git-lfs.github.com/spec/v1" in header or os.path.getsize(path) < min_size_bytes
    except OSError:
        return True


def ensure_model(path, url, label):
    if is_lfs_pointer_or_invalid(path):
        if os.path.exists(path):
            os.remove(path)
        st.write(f"Downloading {label} model...")
        urllib.request.urlretrieve(url, path)


ensure_model(
    realesrgan_path,
    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
    "RealESRGAN_x4plus",
)

ensure_model(
    gfpgan_path,
    "https://github.com/TencentARC/GFPGAN/releases/download/v1.4/GFPGANv1.4.pth",
    "GFPGANv1.4",
)
ensure_model(
    detector_path,
    "https://github.com/xinntao/facexlib/releases/download/v0.2.5/detection_Resnet50_Final.pth",
    "Face detector",
)
ensure_model(
    parsing_path,
    "https://github.com/xinntao/facexlib/releases/download/v0.2.5/parsing_parsenet.pth",
    "Face parser",
)

device = "cuda" if torch.cuda.is_available() else "cpu"


@st.cache_resource
def load_upsampler(tile_size):
    model = RRDBNet(
        num_in_ch=3,
        num_out_ch=3,
        num_feat=64,
        num_block=23,
        num_grow_ch=32,
        scale=4,
    )

    return RealESRGANer(
        scale=4,
        model_path=realesrgan_path,
        model=model,
        tile=tile_size,
        tile_pad=10,
        pre_pad=0,
        half=device == "cuda",
        device=device,
    )


@st.cache_resource
def load_face_enhancer(tile_size):
    upsampler = load_upsampler(tile_size)
    return GFPGANer(
        model_path=gfpgan_path,
        upscale=2,
        arch="clean",
        channel_multiplier=2,
        bg_upsampler=upsampler,
    )


def resize_for_memory(img_bgr, max_dim):
    h, w = img_bgr.shape[:2]
    longest = max(h, w)
    if longest <= max_dim:
        return img_bgr
    scale = max_dim / float(longest)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)


uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])

if LOW_MEMORY_MODE:
    st.info("Low-memory mode is enabled for this deployment. Face restoration is disabled to avoid Render memory crashes.")

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Input Image")
        st.image(image, use_container_width=True)

    use_face_restore = st.checkbox(
        "Enable face restoration (higher RAM)",
        value=True,
        disabled=LOW_MEMORY_MODE,
    )

    if st.button("Enhance Image"):
        with st.spinner("Enhancing image..."):
            try:
                img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                img = resize_for_memory(img, MAX_INPUT_DIM)

                tile_size = 64 if LOW_MEMORY_MODE else 200

                if use_face_restore:
                    face_enhancer = load_face_enhancer(tile_size)
                    _, _, output = face_enhancer.enhance(
                        img,
                        has_aligned=False,
                        only_center_face=False,
                        paste_back=True,
                    )
                else:
                    upsampler = load_upsampler(tile_size)
                    output, _ = upsampler.enhance(img, outscale=4)

                enhanced = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)

                with col2:
                    st.subheader("Enhanced Image")
                    st.image(enhanced, use_container_width=True)

                st.success("Enhancement completed")
                result_bytes = cv2.imencode(".png", output)[1].tobytes()
                st.download_button(
                    "Download Enhanced Image",
                    data=result_bytes,
                    file_name="enhanced_image.png",
                )
            except Exception as exc:
                st.error("Enhancement failed due to memory or model runtime issue.")
                st.code(str(exc))
