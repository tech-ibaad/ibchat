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
# SESSION STATE
# ---------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

with st.sidebar:

    st.header("Settings")

    st.markdown("**Model:** Kimi K2.6")

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
    )

    max_tokens = st.slider(
        "Max Tokens",
        min_value=256,
        max_value=32768,
        value=4096,
        step=256,
    )

    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------
# TABS
# ---------------------------------------------------

chat_tab, image_tab = st.tabs(
    [
        "💬 Chat",
        "🎨 Image Generator",
    ]
)

# ===================================================
# CHAT
# ===================================================

with chat_tab:

    # Scrollable history container.
    # This keeps chat_input fixed at the bottom.
    history = st.container(height=650)

    with history:

        for msg in st.session_state.messages:

            with st.chat_message(msg["role"]):

                if (
                    msg["role"] == "assistant"
                    and msg.get("reasoning")
                ):
                    with st.expander("🧠 Reasoning"):
                        st.markdown(msg["reasoning"])

                st.markdown(msg["content"])

    # IMPORTANT:
    # chat_input MUST be the last widget so it remains pinned.
    prompt = st.chat_input("Message...")

    if prompt:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with history:

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):

                reasoning_placeholder = st.empty()
                response_placeholder = st.empty()

                stream = client.chat.completions.create(
                    model="moonshotai/kimi-k2.6",
                    messages=st.session_state.messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )

                full_text = ""

                for chunk in stream:

                    if not chunk.choices:
                        continue

                    delta = chunk.choices[0].delta

                    if getattr(delta, "content", None):

                        full_text += delta.content

                        cleaned = re.sub(
                            r"<think>.*",
                            "",
                            full_text,
                            flags=re.DOTALL,
                        )

                        response_placeholder.markdown(cleaned)
                                        reasoning = ""
                answer = full_text.strip()

                think_match = re.search(
                    r"<think>(.*?)</think>",
                    full_text,
                    flags=re.DOTALL,
                )

                if think_match:

                    reasoning = think_match.group(1).strip()

                    answer = re.sub(
                        r"<think>.*?</think>",
                        "",
                        full_text,
                        flags=re.DOTALL,
                    ).strip()

                    with reasoning_placeholder.expander(
                        "🧠 Reasoning",
                        expanded=False,
                    ):
                        st.markdown(reasoning)

                response_placeholder.markdown(answer)

                st.download_button(
                    label="⬇ Download Response",
                    data=answer,
                    file_name="response.md",
                    mime="text/markdown",
                    key=f"download_{len(st.session_state.messages)}",
                )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "reasoning": reasoning,
            }
        )

# ===================================================
# IMAGE GENERATOR
# ===================================================

with image_tab:

    st.subheader("🎨 Generate Image")

    img_prompt = st.text_area(
        "Prompt",
        height=150,
        placeholder="Describe the image you want...",
    )

    if st.button(
        "Generate Image",
        use_container_width=True,
    ):

        if not img_prompt.strip():
            st.warning("Please enter a prompt.")
            st.stop()

        with st.spinner("Generating image..."):

            try:

                result = g4f.images.generate(
                    model="flux",
                    prompt=img_prompt,
                    response_format="url",
                )

                if hasattr(result, "data"):
                    image_url = result.data[0].url
                else:
                    image_url = result[0]

                st.image(
                    image_url,
                    use_container_width=True,
                )

                st.markdown("### Image URL")
                st.code(image_url)

            except Exception as e:

                st.error(str(e))
