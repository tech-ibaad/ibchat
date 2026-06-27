import os
import re
import streamlit as st
from openai import OpenAI
from g4f.client import Client as G4FClient

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="IBChat",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 IBChat")

# ---------------------------------------------------
# API
# ---------------------------------------------------

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

if not NVIDIA_API_KEY:
    st.error("NVIDIA_API_KEY environment variable not found.")
    st.stop()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY,
)

g4f = G4FClient()

# ---------------------------------------------------
# SESSION
# ---------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

with st.sidebar:
    st.header("Settings")

    st.markdown("**Model:** Kimi k2.6")

    temperature = st.slider(
        "Temperature",
        0.0,
        2.0,
        0.7
    )

    max_tokens = st.slider(
        "Max Tokens",
        256,
        32768,
        4096
    )

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------
# TABS
# ---------------------------------------------------

chat_tab, image_tab = st.tabs(["💬 Chat", "🎨 Image"])

# ===================================================
# CHAT
# ===================================================

with chat_tab:

    for msg in st.session_state.messages:

        with st.chat_message(msg["role"]):

            if msg["role"] == "assistant":

                if msg.get("reasoning"):
                    with st.expander("🧠 Reasoning"):
                        st.markdown(msg["reasoning"])

            st.markdown(msg["content"])

    prompt = st.chat_input("Message...")

    if prompt:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            reasoning_box = st.empty()
            response_box = st.empty()

            stream = client.chat.completions.create(
                model="moonshotai/kimi-k2.6",
                messages=st.session_state.messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            full = ""

            for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
            
                if getattr(delta, "content", None):
                    full += delta.content
                    response_box.markdown(full)

            

            reasoning = ""

            think = re.search(
                r"<think>(.*?)</think>",
                full,
                re.DOTALL
            )

            if think:
                reasoning = think.group(1).strip()
                answer = re.sub(
                    r"<think>.*?</think>",
                    "",
                    full,
                    flags=re.DOTALL
                ).strip()

                reasoning_box.expander(
                    "🧠 Reasoning",
                    expanded=False
                ).markdown(reasoning)

                response_box.markdown(answer)

            else:
                answer = full

            st.download_button(
                "⬇ Download",
                answer,
                "response.md",
                "text/markdown"
            )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "reasoning": reasoning
            }
        )

# ===================================================
# IMAGE
# ===================================================

with image_tab:

    st.subheader("Generate Image")

    img_prompt = st.text_area(
        "Prompt",
        height=150
    )

    if st.button("Generate Image"):

        with st.spinner("Generating..."):

            try:

                result = g4f.images.generate(
                    model="flux",
                    prompt=img_prompt,
                    response_format="url"
                )

                if hasattr(result, "data"):

                    image_url = result.data[0].url

                else:

                    image_url = result[0]

                st.image(
                    image_url,
                    use_container_width=True
                )

                st.markdown(image_url)

            except Exception as e:

                st.error(str(e))
