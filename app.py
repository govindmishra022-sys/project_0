import os
import io
import datetime
from PIL import Image
import streamlit as st

# Configure Streamlit page layout and appearance
st.set_page_config(
    page_title="Gemini Multimodal AI & Image Classifier",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Helper: Read .env file without external dependencies
# ---------------------------------------------------------
def load_dotenv_fallback(filepath=".env"):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

load_dotenv_fallback()

# ---------------------------------------------------------
# Custom Modern UI Styling
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    h1, h2, h3, .brand-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Main banner styling */
    .hero-container {
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.12) 0%, rgba(147, 51, 234, 0.12) 50%, rgba(236, 72, 153, 0.08) 100%);
        border: 1px solid rgba(147, 51, 234, 0.25);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        backdrop-filter: blur(10px);
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 16px;
    }

    .hero-title {
        font-size: 1.85rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, #4f46e5 0%, #9333ea 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        color: #64748b;
        font-size: 0.95rem;
        margin-top: 4px;
        margin-bottom: 0;
    }

    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        background: rgba(99, 102, 241, 0.15);
        color: #6366f1;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }

    /* Classification Card */
    .classify-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.7) 100%);
        border: 1px solid rgba(147, 51, 234, 0.3);
        border-radius: 16px;
        padding: 20px;
        margin-top: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }

    .classify-step {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 14px;
    }

    .step-badge {
        background: linear-gradient(135deg, #4f46e5, #9333ea);
        color: white;
        border-radius: 50%;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: bold;
        flex-shrink: 0;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 10px;
        transition: all 0.2s ease-in-out;
        font-weight: 500;
    }

    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

if "active_model" not in st.session_state:
    st.session_state.active_model = None

# Classification tab state
if "classify_result" not in st.session_state:
    st.session_state.classify_result = None

# ---------------------------------------------------------
# Sidebar: Settings & API Configuration
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Gemini Settings")

    # API Key Configuration
    default_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    api_key_input = st.text_input(
        "🔑 Gemini API Key",
        value=default_key,
        type="password",
        help="Get your Gemini API Key from Google AI Studio: https://aistudio.google.com/app/apikey"
    )

    if api_key_input:
        st.caption("🟢 API Key configured")
    else:
        st.warning("⚠️ Enter your Gemini API key to start chatting.")
        st.markdown("[👉 Get a free Gemini API Key](https://aistudio.google.com/app/apikey)")

    st.markdown("---")

    # Model Selection
    model_options = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]
    selected_model = st.selectbox(
        "🧠 Gemini Model",
        options=model_options,
        index=0,
        help="Gemini 2.5 Flash is recommended for high speed and state-of-the-art multimodal reasoning."
    )

    # System Instructions Persona
    st.markdown("#### 🎭 Persona & Instructions")
    persona_choice = st.selectbox(
        "Select Persona Preset",
        [
            "Image Classification Specialist (Object, Category & Evidence)",
            "General Helpful AI",
            "Multimodal Vision & OCR Expert",
            "Senior Software Architect & Code Reviewer",
            "Creative Storyteller & Analyst",
            "Custom Instructions..."
        ]
    )

    if persona_choice == "Image Classification Specialist (Object, Category & Evidence)":
        default_system_prompt = (
            "You are an expert computer vision and image classification assistant. "
            "When classifying images, provide a structured breakdown with:\n"
            "1. Main Object Identification\n"
            "2. Category / Taxonomy\n"
            "3. Visual Evidence (colors, shapes, textures, parts, and context)."
        )
    elif persona_choice == "Multimodal Vision & OCR Expert":
        default_system_prompt = (
            "You are a specialized vision analyst and multimodal assistant. "
            "When presented with images, provide structured, comprehensive observations, "
            "transcribe any visible text (OCR), and answer queries with sharp attention to visual detail."
        )
    elif persona_choice == "Senior Software Architect & Code Reviewer":
        default_system_prompt = (
            "You are a principal software engineer. You analyze architecture diagrams, UI mockups, "
            "code screenshots, and system specifications. Produce clean, idiomatic code."
        )
    elif persona_choice == "Creative Storyteller & Analyst":
        default_system_prompt = (
            "You are an engaging, imaginative, and analytical assistant. Analyze visual media with nuance, "
            "creativity, vivid descriptions, and insightful commentary."
        )
    elif persona_choice == "Custom Instructions...":
        default_system_prompt = ""
    else:
        default_system_prompt = (
            "You are a friendly, highly capable, and accurate multimodal AI assistant powered by Google Gemini. "
            "You can analyze both text and images seamlessly."
        )

    system_instruction = st.text_area(
        "System Instruction",
        value=default_system_prompt,
        height=100,
        help="Defines how the Gemini model behaves across the chat."
    )

    # Generation Parameters
    with st.expander("🎛️ Model Hyperparameters", expanded=False):
        temperature = st.slider("Temperature (Creativity)", min_value=0.0, max_value=2.0, value=0.4, step=0.05)
        top_p = st.slider("Top-P (Nucleus Sampling)", min_value=0.0, max_value=1.0, value=0.95, step=0.05)
        max_output_tokens = st.slider("Max Output Tokens", min_value=256, max_value=8192, value=2048, step=256)

    st.markdown("---")

    # Chat Actions & Utilities
    st.markdown("#### 🗂️ Conversation Controls")
    
    col_clear, col_stats = st.columns([1, 1])
    with col_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_session = None
            st.session_state.uploaded_image = None
            st.session_state.uploader_key += 1
            st.rerun()

    total_msgs = len(st.session_state.messages)
    image_msgs = sum(1 for m in st.session_state.messages if m.get("image") is not None)
    st.caption(f"📊 Messages: **{total_msgs}** | 🖼️ Images analyzed: **{image_msgs}**")

    # Export Chat
    if st.session_state.messages:
        export_text = "# Chat Transcript - Gemini Multimodal Assistant\n\n"
        for msg in st.session_state.messages:
            role = "User" if msg["role"] == "user" else "Gemini"
            timestamp = msg.get("timestamp", "")
            has_img = " [Attached Image]" if msg.get("image") is not None else ""
            export_text += f"### {role} ({timestamp}){has_img}\n\n{msg['content']}\n\n---\n\n"

        st.download_button(
            label="📥 Export Chat (Markdown)",
            data=export_text,
            file_name=f"gemini_chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )


# ---------------------------------------------------------
# Main Chat Header Banner
# ---------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div>
        <h1 class="hero-title">✨ Gemini Multimodal Assistant</h1>
        <p class="hero-subtitle">Chat and classify images with Google Gemini using Text & Vision</p>
    </div>
    <div>
        <span class="badge-pill">⚡ Multimodal Active (Vision + Text)</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Navigation Tabs: Multimodal Chat & Dedicated Classifier
# ---------------------------------------------------------
tab_chat, tab_classify = st.tabs(["💬 Multimodal Chatbot", "🏷️ Image Classifier (Object, Category & Evidence)"])

# =========================================================
# TAB 1: MULTIMODAL CHATBOT
# =========================================================
with tab_chat:
    # Image Attachment Section
    with st.expander("📷 **Attach Image to Next Message** (Optional)", expanded=(st.session_state.uploaded_image is not None)):
        col_upload, col_preview = st.columns([3, 2])
        
        with col_upload:
            uploaded_file = st.file_uploader(
                "Upload an image (PNG, JPG, JPEG, WEBP, BMP)",
                type=["png", "jpg", "jpeg", "webp", "bmp"],
                key=f"image_uploader_{st.session_state.uploader_key}",
                help="Upload an image to ask questions about it, extract text, or run image classification."
            )

            if uploaded_file is not None:
                try:
                    pil_image = Image.open(uploaded_file)
                    st.session_state.uploaded_image = pil_image
                except Exception as e:
                    st.error(f"Error opening image: {e}")
                    st.session_state.uploaded_image = None
            else:
                if f"image_uploader_{st.session_state.uploader_key}" in st.session_state and st.session_state[f"image_uploader_{st.session_state.uploader_key}"] is None:
                    st.session_state.uploaded_image = None

        with col_preview:
            if st.session_state.uploaded_image is not None:
                st.markdown("**Image Preview:**")
                st.image(st.session_state.uploaded_image, caption="Ready to send with your prompt", use_container_width=True)
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🏷️ Classify This", key="btn_quick_classify", use_container_width=True):
                        st.session_state.preset_prompt = (
                            "Classify this image\n\n"
                            "1. Identify the main object\n"
                            "2. Give its category\n"
                            "3. Briefly explain the visual evidence"
                        )
                        st.rerun()
                with col_btn2:
                    if st.button("❌ Remove", key="btn_remove_image", use_container_width=True):
                        st.session_state.uploaded_image = None
                        st.session_state.uploader_key += 1
                        st.rerun()
            else:
                st.info("💡 No image attached. Type text directly below, or upload an image to analyze.")

    # Starter Prompts when conversation is empty
    if len(st.session_state.messages) == 0:
        st.markdown("#### 💡 Quick Starters")
        st.caption("Click any suggestion to get started or upload an image above:")

        cols = st.columns(4)
        starter_prompts = [
            ("🏷️ Classify Image", "Classify this image\n\n1. Identify the main object\n2. Give its category\n3. Briefly explain the visual evidence"),
            ("📝 OCR & Extract Text", "Extract all text, numbers, and tabular data from this image in formatted markdown."),
            ("💻 Convert UI to Code", "Analyze this interface/wireframe and generate clean, responsive HTML and CSS to recreate it."),
            ("📊 Explain Diagram", "Break down this diagram or chart step-by-step, explaining the workflow and key takeaways.")
        ]

        for idx, (label, prompt_text) in enumerate(starter_prompts):
            with cols[idx]:
                if st.button(label, use_container_width=True, key=f"starter_{idx}"):
                    if not api_key_input:
                        st.error("Please enter your Gemini API key in the sidebar first!")
                    else:
                        st.session_state.preset_prompt = prompt_text
                        st.rerun()

    # Display Chat Messages
    for msg in st.session_state.messages:
        role = msg["role"]
        avatar = "👤" if role == "user" else "✨"
        with st.chat_message(role, avatar=avatar):
            if msg.get("image") is not None:
                st.image(
                    msg["image"],
                    caption=f"Attached Media ({msg['image'].size[0]}×{msg['image'].size[1]}px)",
                    use_container_width=True
                )
            st.markdown(msg["content"])
            if "timestamp" in msg:
                st.caption(f"*{msg['timestamp']}*")

    # Chat Input & Response Generation
    preset = st.session_state.pop("preset_prompt", None)
    user_input = st.chat_input("Ask a question, describe the image, or request classification...")

    prompt = preset or user_input

    if prompt:
        if not api_key_input:
            st.error("🔑 Please provide your Gemini API key in the sidebar to chat.")
        else:
            current_image = st.session_state.uploaded_image
            now_str = datetime.datetime.now().strftime("%I:%M %p")

            # Record user message in history
            user_message_record = {
                "role": "user",
                "content": prompt,
                "image": current_image,
                "timestamp": now_str
            }
            st.session_state.messages.append(user_message_record)

            # Clear staged image after sending
            if current_image is not None:
                st.session_state.uploaded_image = None
                st.session_state.uploader_key += 1

            # Display user message immediately
            with st.chat_message("user", avatar="👤"):
                if current_image is not None:
                    st.image(current_image, caption="Attached Media", use_container_width=True)
                st.markdown(prompt)
                st.caption(f"*{now_str}*")

            # Stream assistant response
            with st.chat_message("assistant", avatar="✨"):
                response_placeholder = st.empty()
                
                try:
                    from google import genai
                    from google.genai import types

                    client = genai.Client(api_key=api_key_input)

                    config = types.GenerateContentConfig(
                        temperature=temperature,
                        top_p=top_p,
                        max_output_tokens=max_output_tokens,
                        system_instruction=system_instruction.strip() if system_instruction.strip() else None
                    )

                    if (
                        st.session_state.chat_session is None
                        or st.session_state.active_model != selected_model
                    ):
                        st.session_state.chat_session = client.chats.create(
                            model=selected_model,
                            config=config
                        )
                        st.session_state.active_model = selected_model

                    chat = st.session_state.chat_session

                    if current_image is not None:
                        message_payload = [prompt, current_image]
                    else:
                        message_payload = prompt

                    stream = chat.send_message_stream(message=message_payload)

                    full_response = ""
                    for chunk in stream:
                        if chunk.text:
                            full_response += chunk.text
                            response_placeholder.markdown(full_response + " ▌")

                    response_placeholder.markdown(full_response)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "timestamp": datetime.datetime.now().strftime("%I:%M %p")
                    })

                except Exception as e:
                    error_msg = str(e)
                    if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
                        st.error("❌ **Invalid API Key**: Please verify your Gemini API key in the sidebar.")
                    elif "RESOURCE_EXHAUSTED" in error_msg or "Quota" in error_msg:
                        st.error("⏳ **Quota Exceeded**: Rate limit reached. Please wait a moment or check quota.")
                    elif "MODEL_NOT_FOUND" in error_msg or "not found" in error_msg.lower():
                        st.error(f"⚠️ **Model Not Found**: '{selected_model}' not available. Switch to 'gemini-1.5-flash'.")
                    else:
                        st.error(f"⚠️ **Error generating response**: {error_msg}")


# =========================================================
# TAB 2: DEDICATED IMAGE CLASSIFIER
# =========================================================
with tab_classify:
    st.markdown("### 🏷️ Structured Image Classification")
    st.markdown("""
    Upload any image and click **Classify Image** to automatically:
    1. **Identify the main object**
    2. **Determine its category**
    3. **Explain the visual evidence**
    """)

    col_cls_input, col_cls_output = st.columns([1, 1], gap="large")

    with col_cls_input:
        cls_file = st.file_uploader(
            "Select image for classification",
            type=["png", "jpg", "jpeg", "webp", "bmp"],
            key="classifier_tab_uploader"
        )

        custom_prompt_addon = st.text_input(
            "Optional specific question / focus area",
            value="",
            placeholder="e.g. Focus on the vehicle in the foreground"
        )

        cls_image = None
        if cls_file is not None:
            cls_image = Image.open(cls_file)
            st.image(cls_image, caption=f"Uploaded Image ({cls_image.size[0]}×{cls_image.size[1]}px)", use_container_width=True)

        btn_run_classify = st.button("🚀 Classify Image", type="primary", use_container_width=True, disabled=(cls_image is None))

    with col_cls_output:
        st.markdown("#### 📋 Classification Results")
        
        if btn_run_classify:
            if not api_key_input:
                st.error("🔑 Please provide your Gemini API key in the sidebar to run classification.")
            elif cls_image is None:
                st.warning("Please upload an image first.")
            else:
                with st.spinner("Analyzing visual features with Gemini..."):
                    try:
                        from google import genai
                        from google.genai import types

                        client = genai.Client(api_key=api_key_input)
                        
                        classify_prompt = (
                            "Classify this image\n\n"
                            "1. Identify the main object\n"
                            "2. Give its category\n"
                            "3. Briefly explain the visual evidence"
                        )
                        if custom_prompt_addon.strip():
                            classify_prompt += f"\n\nAdditional Focus: {custom_prompt_addon.strip()}"

                        config = types.GenerateContentConfig(
                            temperature=temperature,
                            top_p=top_p,
                            max_output_tokens=max_output_tokens,
                            system_instruction=(
                                "You are a professional image classification and visual reasoning AI. "
                                "Always provide a clear, well-structured response organized as:\n"
                                "1. Identify the main object\n"
                                "2. Give its category\n"
                                "3. Briefly explain the visual evidence\n"
                                "Use clear formatting, bold titles, and bullet points."
                            )
                        )

                        response = client.models.generate_content(
                            model=selected_model,
                            contents=[classify_prompt, cls_image],
                            config=config
                        )

                        st.session_state.classify_result = response.text

                    except Exception as e:
                        st.error(f"Error during classification: {e}")

        if st.session_state.classify_result:
            st.markdown(st.session_state.classify_result)
            
            st.download_button(
                label="📥 Download Classification Report",
                data=f"# Image Classification Report\n\nGenerated by Gemini ({selected_model}) on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{st.session_state.classify_result}",
                file_name=f"classification_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        else:
            if not btn_run_classify:
                st.info("Upload an image on the left and click **'🚀 Classify Image'** to see structured results.")
