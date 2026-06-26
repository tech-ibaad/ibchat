import streamlit as st
import requests
from g4f.client import Client

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

st.set_page_config(
    page_title="IBChat",
    page_icon="🤖",
    layout="wide"
)

client = Client(provider=ApiAirforce)

# -------------------------------------------------
# SESSION
# -------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------

with st.sidebar:
    st.title("🤖 IBChat")
    st.write("Streamlit + g4f")

    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# -------------------------------------------------
# TABS
# -------------------------------------------------

chat_tab, image_tab = st.tabs([
    "💬 Chat",
    "🎨 Image Generator"
])

# =================================================
# CHAT
# =================================================

with chat_tab:

    st.title("💬 IBChat")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Send a message...")

    if prompt:

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            reasoning_expander = st.expander(
                "🧠 Reasoning",
                expanded=False
            )

            response_placeholder = st.empty()

            reasoning = ""
            response = ""

            try:

                stream = client.chat.completions.create(
                    model="kimi-k2",
                    messages=st.session_state.messages,
                    stream=True
                )

                for chunk in stream:

                    delta = chunk.choices[0].delta

                    # --------------------------
                    # Reasoning
                    # --------------------------

                    if hasattr(delta, "reasoning"):
                        if delta.reasoning:

                            reasoning += delta.reasoning

                            with reasoning_expander:
                                st.markdown(reasoning)

                    # --------------------------
                    # Response
                    # --------------------------

                    if hasattr(delta, "content"):
                        if delta.content:

                            response += delta.content

                            response_placeholder.markdown(response)

                if reasoning == "":
                    with reasoning_expander:
                        st.info(
                            "This provider/model does not expose reasoning."
                        )

            except Exception as e:

                response = f"Error:\n\n{e}"

                response_placeholder.error(response)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

        st.download_button(
            "⬇ Download Response",
            response,
            file_name="response.md",
            mime="text/markdown"
        )

# =================================================
# IMAGE
# =================================================

with image_tab:

    st.title("🎨 Image Generator")

    prompt = st.text_area(
        "Image Prompt",
        height=150
    )

    if st.button("Generate Image"):

        if prompt.strip() == "":
            st.warning("Enter a prompt.")
            st.stop()

        with st.spinner("Generating..."):

            try:

                image = client.images.generate(
                    prompt=prompt,
                    response_format="url"
                )

                url = image.data[0].url

                img = requests.get(url).content

                st.image(img)

                st.download_button(
                    "⬇ Download Image",
                    img,
                    file_name="image.png",
                    mime="image/png"
                )

            except Exception as e:

                st.error(e)
