import streamlit as st
import g4f
from io import BytesIO

st.set_page_config(
    page_title="IBChat",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 IBChat")
st.caption("Powered by g4f")

if "messages" not in st.session_state:
    st.session_state.messages = []

tab1, tab2 = st.tabs(["💬 Chat", "🎨 Image Generator"])

###########################
# CHAT
###########################

with tab1:

    col1, col2 = st.columns([8,1])

    with col2:
        if st.button("🗑"):
            st.session_state.messages = []
            st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask anything...")

    if prompt:

        st.session_state.messages.append(
            {
                "role":"user",
                "content":prompt
            }
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            placeholder = st.empty()

            response = ""

            try:

                stream = g4f.ChatCompletion.create(
                    model="gpt-4",
                    messages=st.session_state.messages,
                    stream=True
                )

                for chunk in stream:
                    response += chunk
                    placeholder.markdown(response)

            except:

                response = g4f.ChatCompletion.create(
                    model="gpt-4",
                    messages=st.session_state.messages
                )

                placeholder.markdown(response)

        st.session_state.messages.append(
            {
                "role":"assistant",
                "content":response
            }
        )

    if st.session_state.messages:

        history = ""

        for m in st.session_state.messages:
            history += f"{m['role'].upper()}:\n{m['content']}\n\n"

        st.download_button(
            "📥 Download Chat",
            history,
            "conversation.txt"
        )

###########################
# IMAGE GENERATOR
###########################

with tab2:

    prompt = st.text_area(
        "Image Prompt",
        height=150
    )

    if st.button("Generate Image"):

        if prompt.strip() == "":
            st.warning("Enter a prompt.")
        else:

            with st.spinner("Generating..."):

                try:

                    image_url = g4f.Image.create(
                        prompt=prompt
                    )

                    st.image(image_url)

                    st.markdown(f"[Open Image]({image_url})")

                except Exception as e:
                    st.error(e)
