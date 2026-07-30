import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# 1. Page Configuration & Creative Title
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="CommodityIQ | Enterprise Matrix",
    page_icon="⚡",
    layout="wide"
)

# Creative Branding Header
st.title("⚡ CommodityIQ Matrix")
st.caption("Global Procurement & Sourcing Intelligence Platform | Enterprise Taxonomy Search & Document Analysis")

st.divider()

# -----------------------------------------------------------------------------
# 2. Data Loading & Initialization
# -----------------------------------------------------------------------------
@st.cache_data
def load_commodity_data():
    # Replace 'commodities_data.csv' with your local file path if different
    # If using TSV from Google Sheets export, use sep='\t'
    try:
        return pd.read_csv("commodity_matrix_dataset.csv")
    except Exception:
        # Fallback dummy data structure if file isn't created yet
        return pd.DataFrame(columns=[
            "old_family", "new_family", "commodity_type", 
            "spend_category_workday_gl_code", "commodity_group", 
            "financial_treatment", "description"
        ])

df = load_commodity_data()

DATASET_PATH = "commodity_matrix_dataset.csv"
GEMINI_MODEL = "gemini-2.5-flash"


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


@st.cache_data
def load_csv_system_instruction(path: str = DATASET_PATH) -> str:
    with open(path, encoding="utf-8") as f:
        csv_content = f.read()
    return (
        "You are the CommodityIQ procurement assistant. Answer questions using "
        "only the commodity matrix dataset below. When mapping spend, cite the "
        "relevant GL codes, commodity groups, and financial treatment (CapEx/OpEx). "
        "If the dataset does not contain the answer, say so clearly.\n\n"
        f"Commodity matrix dataset (CSV):\n{csv_content}"
    )


def get_gemini_chat():
    if "gemini_chat" not in st.session_state:
        client = get_gemini_client()
        st.session_state.gemini_chat = client.chats.create(
            model=GEMINI_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=load_csv_system_instruction(),
                temperature=0.2,
            ),
        )
    return st.session_state.gemini_chat

# -----------------------------------------------------------------------------
# 3. Sidebar: File Upload Section (Invoices / Quotes)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("📄 Document Intake")
    st.write("Upload invoices, supplier quotes, or POs to analyze against the matrix.")
    
    uploaded_files = st.file_uploader(
        "Drop files here (PDF, CSV, PNG, XLSX)", 
        accept_multiple_files=True,
        type=["pdf", "csv", "xlsx", "png", "jpg"]
    )
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) attached for processing:")
        for file in uploaded_files:
            st.caption(f"• **{file.name}** ({file.size / 1000:.1f} KB)")
            
    st.divider()
    st.markdown("### Quick Stats")
    st.metric("Total Taxonomies", len(df))
    if not df.empty and "financial_treatment" in df.columns:
        st.metric("CapEx Categories", len(df[df["financial_treatment"] == "CapEx"]))
        st.metric("OpEx Categories", len(df[df["financial_treatment"] == "OpEx"]))

# -----------------------------------------------------------------------------
# 4. Search Bar & Matrix Viewer Section
# -----------------------------------------------------------------------------
st.subheader("🔍 Commodity Search & Lookup")

# Main search bar
search_query = st.text_input(
    "Search across families, GL codes, commodity types, or descriptions:",
    placeholder="Type e.g., 'Software', 'CapEx', '60010', or 'Hardware'..."
)

# Filtering logic across all columns
if search_query and not df.empty:
    # Filter rows where any column contains the search query string (case-insensitive)
    filtered_df = df[df.apply(
        lambda row: row.astype(str).str.contains(search_query, case=False).any(), 
        axis=1
    )]
    st.caption(f"Showing {len(filtered_df)} matching records out of {len(df)}")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
else:
    st.caption("Displaying full commodity matrix (Use search bar above to filter):")
    st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# -----------------------------------------------------------------------------
# 5. Interactive Chat Bar (Bottom of Screen)
# -----------------------------------------------------------------------------
st.subheader("💬 Procurement Assistant Chat")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I can help you map spend categories, lookup GL codes, or review uploaded invoices. What are you looking for today?"}
    ]

# Display prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Bottom chat input bar
if user_prompt := st.chat_input("Ask a question about commodities, GL codes, or uploaded files..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Querying CommodityIQ..."):
            try:
                chat = get_gemini_chat()
                gemini_response = chat.send_message(user_prompt)
                response = gemini_response.text
            except Exception as exc:
                response = (
                    "Sorry, I couldn't reach Gemini right now. "
                    f"Please verify your API key in `.streamlit/secrets.toml`. ({exc})"
                )

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})