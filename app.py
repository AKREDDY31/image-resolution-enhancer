import streamlit as st
import cv2
import numpy as np
from PIL import Image
import torch
import os
import urllib.request

from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
from gfpgan import GFPGANer


st.set_page_config(page_title="AI Image Restoration", layout="wide")

st.title("AI Image Restoration Platform")
st.write("Enhance blurry and low-resolution images using AI")


# ---------------- CREATE MODEL DIRECTORY ----------------

os.makedirs("models", exist_ok=True)

realesrgan_path = "models/RealESRGAN_x4plus.pth"
gfpgan_path = "models/GFPGANv1.4.pth"


# ---------------- DOWNLOAD MODELS IF MISSING ----------------

if not os.path.exists(realesrgan_path):

    st.write("Downloading RealESRGAN model...")

    urllib.request.urlretrieve(
        "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
        realesrgan_path
    )


if not os.path.exists(gfpgan_path):

    st.write("Downloading GFPGAN model...")

    urllib.request.urlretrieve(
        "https://github.com/TencentARC/GFPGAN/releases/download/v1.4/GFPGANv1.4.pth",
        gfpgan_path
    )


# ---------------- DEVICE ----------------

device = "cuda" if torch.cuda.is_available() else "cpu"


# ---------------- LOAD MODELS ----------------

@st.cache_resource
def load_models():

    model = RRDBNet(
        num_in_ch=3,
        num_out_ch=3,
        num_feat=64,
        num_block=23,
        num_grow_ch=32,
        scale=4
    )

    upsampler = RealESRGANer(
        scale=4,
        model_path=realesrgan_path,
        model=model,
        tile=200,
        tile_pad=10,
        pre_pad=0,
        half=True if device == "cuda" else False,
        device=device
    )

    face_enhancer = GFPGANer(
        model_path=gfpgan_path,
        upscale=2,
        arch="clean",
        channel_multiplier=2,
        bg_upsampler=upsampler
    )

    return face_enhancer


face_enhancer = load_models()


# ---------------- IMAGE INPUT ----------------

uploaded_file = st.file_uploader(
    "Upload Image",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file:

    image = Image.open(uploaded_file)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Input Image")
        st.image(image, use_column_width=True)

    if st.button("Enhance Image"):

        with st.spinner("Enhancing image..."):

            img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            cropped_faces, restored_faces, output = face_enhancer.enhance(
                img,
                has_aligned=False,
                only_center_face=False,
                paste_back=True
            )

            enhanced = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)

            with col2:
                st.subheader("Enhanced Image")
                st.image(enhanced, use_column_width=True)

            st.success("Enhancement completed")

            result_bytes = cv2.imencode(".png", output)[1].tobytes()

            st.download_button(
                "Download Enhanced Image",
                data=result_bytes,
                file_name="enhanced_image.png"
            )