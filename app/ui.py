import requests
import streamlit as st

st.set_page_config(page_title="Voice Call Search", page_icon="🔎", layout="centered")
st.title("🔎 Call Search (Semantic)")

API_BASE = st.secrets.get("API_BASE", "http://localhost:8000")

q = st.text_input("Search calls by meaning", "refund for leaking coffee machine")
top_k = st.number_input("Top K", min_value=1, max_value=20, value=5, step=1)

if st.button("Search"):
    with st.spinner("Searching..."):
        try:
            r = requests.get(f"{API_BASE}/search", params={"query": q, "top_k": top_k}, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            st.error(f"Request failed: {e}")
            st.stop()

    st.subheader(f"Results ({data.get('count',0)})")
    for i, item in enumerate(data.get("results", []), start=1):
        st.markdown(f"**{i}.** Call ID: `{item['call_id']}` — Score: `{item['score']:.3f}`")
        meta = []
        if item.get("customer_id"): meta.append(f"customer: {item['customer_id']}")
        if item.get("started_at"): meta.append(f"started: {item['started_at']}")
        if item.get("duration_sec"): meta.append(f"duration: {item['duration_sec']}s")
        if meta:
            st.caption(" • ".join(meta))

        # Prefer summary; fall back to first 200 chars of transcript
        if item.get("summary"):
            st.write(item["summary"])
        elif item.get("file_uri"):
            st.write("No summary yet.")

        # Play audio if available
        if item.get("audio_url"):
            st.audio(f"{API_BASE}{item['audio_url']}")
        st.divider()