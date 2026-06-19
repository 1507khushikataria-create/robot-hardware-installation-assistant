import streamlit as st
import requests

API_URL = "https://robot-hardware-installation-assistant-production.up.railway.app"

st.set_page_config(
    page_title="AI Robot Hardware Installation Assistant",
    layout="wide"
)

# ==========================
# 10. Hide Streamlit Branding
# ==========================
hide_streamlit = """
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
</style>
"""
st.markdown(hide_streamlit, unsafe_allow_html=True)

# ==========================
# 2. Light Blue Theme
# ==========================
st.markdown("""
<style>

.main {
    background-color: #F5FAFF;
}

div[data-testid="metric-container"] {
    background-color: #E3F2FD;
    border: 2px solid #90CAF9;
    padding: 15px;
    border-radius: 15px;
}

.stButton button {
    background-color: #42A5F5;
    color: white;
    border-radius: 10px;
}

.stButton button:hover {
    background-color: #1E88E5;
}

</style>
""", unsafe_allow_html=True)

# ==========================
# Session State
# ==========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False

# ==========================
# 5. Sidebar
# ==========================
with st.sidebar:
    st.image(
        "https://img.icons8.com/color/96/robot.png",
        width=120
    )
    st.title("Robot Assistant")
    st.success("Online AI System")
    st.info("PDF → RAG → Flowchart")

# ==========================
# 1. Hero Header
# ==========================
st.markdown("""
<h1 style='text-align:center;color:#1976D2;'>
🤖 AI Robot Hardware Installation Assistant
</h1>
<h4 style='text-align:center;color:#64B5F6;'>
Online RAG System for Industrial Robot Manuals
</h4>
""", unsafe_allow_html=True)

# ==========================
# 3. Dashboard Cards
# ==========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📄 Manuals", "Ready")

with col2:
    st.metric("🤖 Chatbot", "Active")

with col3:
    st.metric("📈 Flowcharts", "Enabled")

# ==========================
# 4. Tabs
# ==========================
tab1, tab2, tab3 = st.tabs(
    [
        "📄 Upload",
        "💬 Chat",
        "📈 Flowcharts"
    ]
)

# ==========================
# TAB 1: PDF UPLOAD
# ==========================
with tab1:
    # 6. Better Section Titles
    st.subheader("📄 Upload Robot Manual")

    uploaded_file = st.file_uploader(
        "Choose a PDF",
        type=["pdf"]
    )

    if uploaded_file is not None and not st.session_state.pdf_uploaded:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "application/pdf"
            )
        }

        try:
            response = requests.post(
                f"{API_URL}/upload-pdf",
                files=files,
                timeout=300
            )

            st.success("PDF uploaded successfully")
            st.json(response.json())
            st.session_state.pdf_uploaded = True

        except Exception as e:
            st.error(f"Upload Error: {str(e)}")

# ==========================
# TAB 2: CHAT
# ==========================
with tab2:
    st.subheader("💬 Chat with Your Manual")

    # Chat History
    for message in st.session_state.messages:
        with st.chat_message("user"):
            st.write(message["question"])

        with st.chat_message("assistant"):
            st.write(message["answer"])

    # Chat Input
    question = st.chat_input("Ask a question about the uploaded manual...")

    if question:
        with st.chat_message("user"):
            st.write(question)

        try:
            # 7. Better Loading Messages
            with st.spinner("🤖 Consulting robot manuals..."):
                response = requests.post(
                    f"{API_URL}/chat",
                    json={
                        "prompt": question
                    },
                    timeout=300
                )
                result = response.json()

            answer = result.get("response", "No response returned.")

            with st.chat_message("assistant"):
                st.write(answer)

            st.session_state.messages.append({
                "question": question,
                "answer": answer
            })

            if "retrieved_chunks" in result:
                # 9. Expanders for Technical Details
                with st.expander("📚 Retrieved Manual Sections"):
                    for chunk in result["retrieved_chunks"]:
                        st.write(chunk)
                        st.divider()

        except Exception as e:
            st.error(f"Chat Error: {str(e)}")

# ==========================
# TAB 3: FLOWCHART GENERATOR
# ==========================
with tab3:
    # 6. Better Section Titles
    st.subheader("📈 Engineering Flowchart Generator")

    flowchart_topic = st.text_input(
        "Enter Manual Section",
        placeholder="e.g. Servo Installation, Robot Assembly, Calibration Procedure"
    )

    if st.button("Generate Flowchart"):
        if not flowchart_topic:
            st.error("Please enter a manual section topic.")
        else:
            try:
                # 7. Better Loading Messages
                with st.spinner("⚙️ Generating engineering workflow..."):
                    response = requests.post(
                        f"{API_URL}/generate-flowchart",
                        json={
                            "topic": flowchart_topic
                        },
                        timeout=300
                    )

                    result = response.json()

                if "error" in result:
                    st.error(result["error"])
                else:
                    st.subheader("Procedure Steps")

                    for step in result["steps"]:
                        st.write(f"• {step}")

                    st.image(result["image_path"])

                    # 8. Download Flowchart Button
                    with open(result["image_path"], "rb") as file:
                        st.download_button(
                            "⬇ Download Flowchart",
                            file,
                            file_name="flowchart.png"
                        )

            except Exception as e:
                st.error(f"Flowchart Error: {str(e)}")