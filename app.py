"""
app.py — AgroEdge-Vision: Premium AI Plant Diagnostics App
Run: streamlit run app.py
"""

import streamlit as st
import database
import model

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgroEdge-Vision",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Seed guest_user_id FIRST — must run before any session state reads
database._init()

if "prediction" not in st.session_state:
    st.session_state["prediction"] = None
if "uploaded_file" not in st.session_state:
    st.session_state["uploaded_file"] = None
if "input_mode" not in st.session_state:
    st.session_state["input_mode"] = "camera"

# ─────────────────────────────────────────────────────────────────────────────
# STABLE CSS ARCHITECTURE
# ─────────────────────────────────────────────────────────────────────────────
st.html("""
<link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@500;600;700&display=swap" rel="stylesheet">
<style>
  /* ── GLOBAL RESET ───────────────────────────────────────────────────────── */
  * { box-sizing: border-box; font-family: 'Quicksand', sans-serif !important; }

  /* ── ROOT BACKGROUND + OVERFLOW SEAL ───────────────────────────────────── */
  html, body,
  [data-testid="stAppViewContainer"],
  [data-testid="stApp"] {
    background-color: #E4F1EB !important;
    overflow-x: hidden !important;
  }

  /* ── HIDE STREAMLIT CHROME ──────────────────────────────────────────────── */
  [data-testid="stHeader"], footer, section[data-testid="stSidebar"] {
    display: none !important;
  }

  /* ── MAIN CONTENT PADDING ───────────────────────────────────────────────── */
  [data-testid="block-container"] {
    padding-top: 100px !important;
    padding-bottom: 120px !important;
    padding-left: 16px !important;
    padding-right: 16px !important;
    max-width: 430px !important;
    margin: 0 auto !important;
    background-color: transparent !important;
    overflow-x: hidden !important;
  }

  /* ── HORIZONTAL SCROLL FOR TOGGLE BUTTONS ──────────────────────── */
  div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
  }

  div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
    flex: 1 1 0px !important;
    min-width: 0 !important;
    max-width: calc(50% - 8px) !important;
    overflow: hidden !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
  }

  div[data-testid="stColumn"] > div {
    min-width: 0 !important;
    width: 100% !important;
  }

  /* ── 1. STICKY TOP HEADER ───────────────────────────────────────────────── */
  .custom-header {
    position: fixed;
    top: 16px;
    left: 50%;
    transform: translateX(-50%);
    width: calc(100% - 32px);
    max-width: 400px;
    background: #FFFFFF !important;
    border-radius: 999px;
    padding: 12px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 20px rgba(43,91,77,0.05);
    z-index: 9999;
  }

  /* ── 2. CAMERA & UPLOAD DROPZONES ──────────────────────────────────────── */
  [data-testid="stFileUploaderDropzone"],
  [data-testid="stCameraInput"] > div {
    background: linear-gradient(145deg, #D4EAE0, #E8F5EE) !important;
    border: 2px dashed #9EDCCB !important;
    border-radius: 24px !important;
    padding: 24px 16px !important;
    width: 100% !important;
    box-sizing: border-box !important;
  }
  [data-testid="stFileUploaderDropzone"] label { display: none !important; }
  /* Clean up dropzone: hide overlapping text/descriptions and center the button */
  [data-testid="stFileUploaderDropzone"] section {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    padding: 0 !important;
  }
  [data-testid="stFileUploaderDropzone"] section > *:not(button) {
    display: none !important;
  }

  /* ── 3. PRIMARY CTA BUTTON — "Scan Plant Health" ───────────────────────── */
  button[kind="primary"],
  [data-testid="stBaseButton-primary"] {
    background-image: none !important;
    background-color: #AEE19A !important;
    background: #AEE19A !important;
    opacity: 1 !important;
    border: none !important;
    box-shadow: 0 4px 15px #c5e8b0 !important;
    border-radius: 999px !important;
    width: 100% !important;
    padding: 16px !important;
    margin-top: 8px;
    transition: background-color 0.2s ease;
  }
  button[kind="primary"] p,
  [data-testid="stBaseButton-primary"] p {
    color: #2B5B4D !important;
    font-weight: 700 !important;
    font-size: 18px !important;
    background: transparent !important;
  }
  button[kind="primary"]:hover,
  [data-testid="stBaseButton-primary"]:hover {
    background-image: none !important;
    background-color: #9cd587 !important;
    background: #9cd587 !important;
  }

  button[kind="primary"]:disabled,
  button[kind="primary"][disabled],
  [data-testid="stBaseButton-primary"]:disabled {
    background-image: none !important;
    background-color: #D4EAE0 !important;
    background: #D4EAE0 !important;
    opacity: 1 !important;
    box-shadow: none !important;
    cursor: not-allowed;
  }
  button[kind="primary"]:disabled p,
  button[kind="primary"][disabled] p {
    color: #6B9987 !important;
  }

  /* ── 4. SECONDARY BUTTONS (Take Live Photo / Upload Image) ─────────────── */
  button[kind="secondary"],
  [data-testid="stBaseButton-secondary"] {
    background-image: none !important;
    background-color: #2B5B4D !important;
    background: #2B5B4D !important;
    border: 1px solid #2B5B4D !important;
    border-radius: 999px !important;
    padding: 12px 4px !important;
    width: 100% !important;
    min-width: 0 !important;
    transition: background-color 0.2s ease;
  }
  button[kind="secondary"] p,
  [data-testid="stBaseButton-secondary"] p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    background: transparent !important;
    margin: 0 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
  }

  /* ── 5. BOTTOM NAVIGATION BAR ──────────────────────────────────────────── */
  [data-testid="stRadio"] {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    width: calc(100% - 32px);
    max-width: 400px;
    background: #FFFFFF !important;
    border-radius: 999px;
    padding: 8px 12px;
    box-shadow: 0 10px 30px rgba(43,91,77,0.12);
    z-index: 9999;
  }
  [data-testid="stRadio"] > label { display: none !important; }
  [data-testid="stRadio"] div[role="radiogroup"] {
    display: flex; flex-direction: row; justify-content: space-around; gap: 4px;
  }
  [data-testid="stRadio"] label[data-baseweb="radio"] {
    flex: 1; justify-content: center; padding: 10px 0;
    border-radius: 999px; cursor: pointer; background-color: transparent;
  }
  [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
    background: #AEE19A !important;
  }
  [data-testid="stRadio"] label[data-baseweb="radio"] p {
    font-size: 13px !important; font-weight: 700 !important;
    color: #2B5B4D !important; margin: 0; text-align: center;
    background-color: transparent !important;
  }
  [data-testid="stRadio"] div[role="radio"] { display: none !important; }

  /* ── 6. NATIVE ST.PROGRESS INTEGRATION (DIAGNOSTIC CARD) ───────────────── */
  [data-testid="stVerticalBlock"] > [data-testid="stProgress"] {
    background: #FFFFFF !important;
    padding: 0 20px 24px 20px !important;
    border-radius: 0 0 20px 20px !important;
    box-shadow: 0 8px 20px rgba(43,91,77,0.03) !important;
    margin-top: -16px !important; 
  }
  [data-testid="stProgress"] > div > div > div > div {
    background: linear-gradient(90deg, #FAD694, #F5BC5A) !important;
    border-radius: 999px !important;
    height: 12px !important;
  }
  [data-testid="stProgress"] > div > div {
    background-color: #E8F5EE !important;
    border-radius: 999px !important;
    height: 12px !important;
  }

  /* ── MISC ───────────────────────────────────────────────────────────────── */
  .scan-image img { border-radius: 20px !important; width: 100% !important; }

  /* ── ARCHIVE DELETE BUTTON ─────────────────────────────────────────────── */
  button:has(p:contains("🗑️")) {
    background: #EAF4EE !important;
    background-image: none !important;
    border: none !important;
    border-radius: 50% !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 0 !important;
    padding: 0 !important;
    box-shadow: none !important;
    margin-top: 14px !important;
  }
  button:has(p:contains("🗑️")) p {
    font-size: 16px !important;
    color: #6B9987 !important;
  }
  /* Align the delete column to center vertically */
  div[data-testid="stColumn"]:last-child {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
</style>
""")

# ─────────────────────────────────────────────────────────────────────────────
# DYNAMIC TOGGLE CSS (highlights the active input-mode button)
# ─────────────────────────────────────────────────────────────────────────────
active_btn = "📸 Take Live Photo" if st.session_state["input_mode"] == "camera" else "⬆ Upload Image"
st.html(f"""
<style>
  button[kind="secondary"]:has(p:contains("{active_btn}")),
  [data-testid="stBaseButton-secondary"]:has(p:contains("{active_btn}")) {{
    background-image: none !important;
    background-color: #387361 !important;
    background: #387361 !important;
    border-color: #387361 !important;
  }}
</style>
""")

# ─────────────────────────────────────────────────────────────────────────────
# VECTOR ASSETS & REUSABLE HTML COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────
SVG_ICONS = {
    "menu": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2B5B4D" stroke-width="2.5" stroke-linecap="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>',
    "avatar": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'
}

def render_sticky_header():
    st.html(f"""
    <div class="custom-header">
      <div style="cursor:pointer; display:flex; background:transparent;">{SVG_ICONS['menu']}</div>
      <div style="font-size:20px; font-weight:700; color:#2B5B4D; letter-spacing:-0.5px; background:transparent;">AgroEdge-Vision</div>
      <div style="width:36px; height:36px; border-radius:50%; background:#6B9987; display:flex; align-items:center; justify-content:center;">
        {SVG_ICONS['avatar']}
      </div>
    </div>
    """)

# ─────────────────────────────────────────────────────────────────────────────
# SCREENS
# ─────────────────────────────────────────────────────────────────────────────
def screen_scanner():
    render_sticky_header()

    st.html("""
    <div style="background: #FFFFFF !important; border-radius: 20px; padding: 20px; margin-bottom: 16px; box-shadow: 0 4px 20px rgba(43,91,77,0.03);">
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px; background:transparent;">
        <span style="font-size:16px; background:transparent;">🌿</span>
        <span style="font-size:12px; font-weight:700; color:#6B9987; letter-spacing:1px; text-transform:uppercase; background:transparent;">GARDEN STATUS</span>
      </div>
      <div style="font-size:18px; font-weight:600; color:#2B5B4D; line-height:1.4; background:transparent;">
        Welcome back! Let's check on your garden health today.
      </div>
    </div>
    """)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📸 Take Live Photo", type="secondary", use_container_width=True):
            st.session_state["input_mode"] = "camera"
            st.rerun()
    with col2:
        if st.button("⬆ Upload Image", type="secondary", use_container_width=True):
            st.session_state["input_mode"] = "upload"
            st.rerun()

    st.html('<div style="height:8px; background:transparent;"></div>')

    if st.session_state["input_mode"] == "camera":
        file_input = st.camera_input("", label_visibility="collapsed")
    else:
        file_input = st.file_uploader("", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")

    if file_input:
        st.session_state["uploaded_file"] = file_input
        st.session_state["prediction"] = None

    has_file = st.session_state.get("uploaded_file") is not None
    if st.button("⚡ Scan Plant Health", type="primary", use_container_width=True, disabled=not has_file):
        with st.spinner("Analyzing plant biomatter..."):
            result = model.analyze_leaf_image(st.session_state["uploaded_file"])
        # Map structured output fields including top 3 predictions and cropped image
        st.session_state["prediction"] = {
            "label": result["disease_name"],
            "confidence": result["confidence"],
            "top_predictions": result.get("top_predictions", []),
            "cropped_image": result.get("cropped_image", None)
        }
        database.add_log(result["disease_name"], result["confidence"])
        st.rerun()


def screen_diagnostic_report():
    render_sticky_header()
    prediction = st.session_state["prediction"]

    if st.button("← Back to Scanner", type="secondary", use_container_width=True):
        st.session_state["uploaded_file"] = None
        st.session_state["prediction"] = None
        st.rerun()

    st.html('<div style="height:12px; background:transparent;"></div>')

    st.html('<div class="scan-image">')
    st.image(st.session_state["uploaded_file"], use_container_width=True)
    st.html('</div>')



    # Convert Float (0.8834) to Percentage String (88)
    conf_decimal = float(prediction["confidence"])
    conf_pct_str = f"{int(conf_decimal * 100)}%"

    # SMART CONFIDENCE THRESHOLD (80% / 0.80)
    if conf_decimal >= 0.80:
        # High confidence mode: Show only the top match
        st.html(f"""
        <div style="background: #FFFFFF !important; border-radius: 20px 20px 0 0; padding: 24px 20px 12px 20px; margin-top: 16px; box-shadow: 0 -4px 20px rgba(43,91,77,0.03);">
          <div style="text-align:center; margin-bottom:4px; background:transparent;">
            <span style="font-size:12px; font-weight:700; color:#6B9987; letter-spacing:1px; text-transform:uppercase; background:transparent;">Diagnosis Result</span>
          </div>
          <div style="text-align:center; margin-bottom:6px; background:transparent;">
            <span style="font-size:22px; font-weight:700; color:#2B5B4D; background:transparent;">{prediction['label']}</span>
          </div>
          <div style="text-align:center; margin-bottom:0px; background:transparent;">
            <span style="font-size:16px; font-weight:700; color:#2B5B4D; background:transparent;">{conf_pct_str} Confidence Match</span>
          </div>
        </div>
        """)
        st.progress(conf_decimal)
    else:
        # Low confidence mode: Show top 3 matches
        top_preds = prediction.get("top_predictions", [])
        
        # Fallback if top_predictions is empty (e.g. legacy DB log data)
        if not top_preds:
            top_preds = [{"label": prediction["label"], "confidence": conf_decimal}]
            
        rows_html = ""
        for i, pred in enumerate(top_preds):
            p_val = float(pred["confidence"])
            p_pct = int(p_val * 100)
            rows_html += f"""
            <div style="margin-top: 14px; background:transparent;">
              <div style="display:flex; justify-content:space-between; margin-bottom:4px; background:transparent;">
                <span style="font-size:14px; font-weight:700; color:#2B5B4D; background:transparent;">{i+1}. {pred['label']}</span>
                <span style="font-size:14px; font-weight:700; color:#6B9987; background:transparent;">{p_pct}%</span>
              </div>
              <div style="width: 100%; background-color: #E8F5EE; border-radius: 999px; height: 10px; overflow: hidden; margin-top: 4px;">
                <div style="width: {p_pct}%; height: 100%; background: linear-gradient(90deg, #FAD694, #F5BC5A); border-radius: 999px;"></div>
              </div>
            </div>
            """
            
        st.html(f"""
        <div style="background: #FFFFFF !important; border-radius: 20px; padding: 24px 20px; margin-top: 16px; box-shadow: 0 4px 20px rgba(43,91,77,0.03);">
          <div style="text-align:center; margin-bottom:4px; background:transparent;">
            <span style="font-size:12px; font-weight:700; color:#6B9987; letter-spacing:1px; text-transform:uppercase; background:transparent;">Uncertain Diagnosis</span>
          </div>
          <div style="text-align:center; margin-bottom:6px; background:transparent;">
            <span style="font-size:20px; font-weight:700; color:#E07070; background:transparent;">Potential Conditions</span>
          </div>
          <div style="text-align:center; margin-bottom:12px; background:transparent;">
            <span style="font-size:13px; font-weight:600; color:#6B9987; background:transparent;">Please review the top potential matches:</span>
          </div>
          <hr style="border: none; border-top: 1px solid #E8F5EE; margin: 12px 0;">
          {rows_html}
        </div>
        """)


def _build_donut_chart_html(logs: list) -> str:
    PALETTE = [
        "#84dcc6", "#a5ffd6", "#ffa69e", "#ff686b", 
        "#8bbfb5", "#b8dfd8", "#d4b8e0", "#c9f0c8", "#f0efc8",
    ]
    HEALTHY_COLOR = "#84dcc6"

    if not logs:
        return """
        <div style="background:#FFFFFF;border-radius:20px;padding:20px;margin-bottom:16px;box-shadow:0 4px 20px rgba(43,91,77,0.03);">
          <div style="font-size:15px;font-weight:700;color:#2B5B4D;margin-bottom:16px;background:transparent;">Health Breakdown</div>
          <div style="text-align:center;color:#6B9987;padding:20px;background:transparent;">No scan data yet.</div>
        </div>"""

    from collections import Counter
    counts = Counter(e.get("disease_name", "Unknown") for e in logs)
    total = sum(counts.values())

    items = sorted(counts.items(), key=lambda x: (0 if "healthy" in x[0].lower() else 1, x[0]))

    colour_map = {}
    disease_palette = [c for c in PALETTE if c != HEALTHY_COLOR]
    disease_idx = 0
    for label, _ in items:
        if "healthy" in label.lower():
            colour_map[label] = HEALTHY_COLOR
        else:
            colour_map[label] = disease_palette[disease_idx % len(disease_palette)]
            disease_idx += 1

    cx, cy, r_outer, r_inner = 90, 90, 72, 44
    circumference = 2 * 3.14159265 * r_outer
    gap = 3
    stroke_w = r_outer - r_inner

    segments_svg = ""
    current_offset = 0.0

    for label, count in items:
        fraction = count / total
        arc_len = circumference * fraction
        dash_len = max(arc_len - gap, 0)
        color = colour_map[label]

        segments_svg += (
            f'<circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_w}" '
            f'stroke-dasharray="{dash_len:.2f} {circumference - dash_len:.2f}" '
            f'stroke-dashoffset="{-current_offset:.2f}" '
            f'stroke-linecap="butt"/>\n'
        )
        current_offset += arc_len

    centre_label_svg = f"""
      <text x="{cx}" y="{cy - 8}" text-anchor="middle" font-size="22" font-weight="700"
            font-family="Quicksand,sans-serif" fill="#2B5B4D">{total}</text>
      <text x="{cx}" y="{cy + 10}" text-anchor="middle" font-size="9" font-weight="600"
            font-family="Quicksand,sans-serif" fill="#6B9987" letter-spacing="1">TOTAL SCANS</text>
    """

    legend_rows = ""
    for label, count in items:
        pct = round(count / total * 100)
        color = colour_map[label]
        display = label if len(label) <= 28 else label[:26] + "…"
        legend_rows += f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;background:transparent;">
          <div style="width:12px;height:12px;border-radius:3px;background:{color};flex-shrink:0;"></div>
          <div style="flex:1;font-size:12px;font-weight:600;color:#2B5B4D;background:transparent;
                      white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{display}</div>
          <div style="font-size:12px;font-weight:700;color:#6B9987;background:transparent;">{pct}%</div>
        </div>"""

    return f"""
    <div style="background:#FFFFFF !important;border-radius:20px;padding:20px;
                margin-bottom:16px;box-shadow:0 4px 20px rgba(43,91,77,0.03);">
      <div style="font-size:15px;font-weight:700;color:#2B5B4D;margin-bottom:16px;
                  background:transparent;">Health Breakdown</div>
      <div style="display:flex;align-items:center;gap:20px;background:transparent;">
        <div style="flex-shrink:0;background:transparent;">
          <svg width="180" height="180" viewBox="0 0 180 180" xmlns="http://www.w3.org/2000/svg">
            <circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="none" stroke="#E8F5EE" stroke-width="{stroke_w}"/>
            <g transform="rotate(-90 {cx} {cy})">{segments_svg}</g>
            {centre_label_svg}
          </svg>
        </div>
        <div style="flex:1;min-width:0;background:transparent;">
          {legend_rows}
        </div>
      </div>
    </div>"""

def screen_archive():
    render_sticky_header()
    logs = database.get_all_logs()

    # TEMP DEBUG
    st.html(f"""<div style="font-size:20px; font-weight:700; color:#2B5B4D; margin-bottom: 16px; background:transparent;">Archive ({len(logs)})</div>""")

    if not logs:
        st.html("""<div style="text-align:center; color:#6B9987; padding: 20px; background:transparent;">No scans yet.</div>""")

    for entry in logs:
        label     = entry.get("disease_name", "Unknown")
        status    = entry.get("status", "")
        record_id = entry.get("id")

        try:
            from datetime import datetime
            dt = datetime.fromisoformat(entry.get("created_at", ""))
            timestamp_str = dt.strftime("%b %d, %Y  %H:%M")
        except Exception:
            timestamp_str = str(entry.get("created_at", ""))[:16]

        tint_color = "#E07070" if status in ("disease", "unhealthy") else "#7CC96E"
        conf_pct   = int(float(entry.get("confidence", 0)) * 100)

        # Inject CSS to style this specific button as a round icon
        st.markdown(f"""
        <style>
          div[data-testid="stButton"] button[kind="secondary"]#btn_del_{record_id},
          [key="del_{record_id}"] button {{
            background: #EAF4EE !important;
            border: none !important;
            border-radius: 50% !important;
            width: 34px !important; height: 34px !important;
            padding: 0 !important; min-width: 0 !important;
            box-shadow: none !important;
          }}
        </style>
        """, unsafe_allow_html=True)

        col_card, col_btn = st.columns([11, 1])
        with col_card:
            st.html(f"""
            <div style="background:#FFFFFF !important; border-radius:20px; padding:16px 18px;
                        margin-bottom:4px; display:flex; align-items:center; gap:14px;
                        box-shadow:0 4px 20px rgba(43,91,77,0.03); width:100%; box-sizing:border-box;">
              <div style="width:12px; height:12px; border-radius:50%; background:{tint_color}; flex-shrink:0;"></div>
              <div style="background:transparent; flex:1; min-width:0;">
                <div style="font-size:15px; font-weight:700; color:#2B5B4D; background:transparent;
                            white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{label}</div>
                <div style="font-size:12px; color:#6B9987; font-weight:600; margin-top:3px; background:transparent;">
                  {timestamp_str} &nbsp;•&nbsp; <span style="color:#2B5B4D; font-weight:700;">{conf_pct}% Match</span>
                </div>
              </div>
            </div>
            """)
        with col_btn:
            if st.button("🗑️", key=f"del_{record_id}"):
                database.delete_log(int(record_id))
                st.session_state["bottom_nav"] = "Archive"
                st.rerun()

def screen_analytics():
    render_sticky_header()
    logs = database.get_all_logs()
    total = len(logs)
    healthy = sum(1 for e in logs if e["status"] == "healthy")
    pct = int((healthy / total) * 100) if total > 0 else 0

    st.html("""<div style="font-size:20px; font-weight:700; color:#2B5B4D; margin-bottom: 16px; background:transparent;">Garden Health</div>""")

    st.html(f"""
    <div style="background: #FFFFFF !important; border-radius: 20px; padding: 20px; margin-bottom: 16px; box-shadow: 0 4px 20px rgba(43,91,77,0.03);">
      <div style="font-size:15px; font-weight:700; color:#2B5B4D; margin-bottom:12px; background:transparent;">Healthy Plants vs Infections</div>
      <div style="background:#E8F5EE; border-radius:999px; height:14px; overflow:hidden;">
        <div style="width:{pct}%; height:100%; background:#7CC96E; border-radius:999px;"></div>
      </div>
      <div style="font-size:13px; color:#6B9987; font-weight:600; margin-top:10px; background:transparent;">{pct}% Total Optimal Health</div>
    </div>
    """)

    st.html(_build_donut_chart_html(logs))

    st.html(f"""
    <div style="background: #FFFFFF !important; border-radius: 20px; padding: 20px; box-shadow: 0 4px 20px rgba(43,91,77,0.03);">
      <div style="font-size:15px; font-weight:700; color:#2B5B4D; margin-bottom:12px; background:transparent;">Insights Overview</div>
      <div style="font-size:14px; color:#6B9987; line-height:1.5; font-weight:500; background:transparent;">
        You have scanned a total of <b style="background:transparent;">{total}</b> plants. Your current garden health metric indicates that <b style="background:transparent;">{healthy}</b> scans came back clean. Keep an eye out for changes in leaf discoloration or spotting!
      </div>
    </div>
    """)

# ─────────────────────────────────────────────────────────────────────────────
# CORE ROUTER
# ─────────────────────────────────────────────────────────────────────────────
def main():
    current_nav = st.session_state.get("bottom_nav", "Scanner")

    if current_nav == "Scanner":
        if st.session_state.get("prediction") is not None:
            screen_diagnostic_report()
        else:
            screen_scanner()
    elif current_nav == "Archive":
        screen_archive()
    elif current_nav == "Analytics":
        screen_analytics()

    _nav_options = ["Scanner", "Archive", "Analytics"]
    _nav_index = _nav_options.index(st.session_state.get("bottom_nav", "Scanner"))
    nav_selection = st.radio(
        "bottom_nav_menu",
        _nav_options,
        index=_nav_index,
        horizontal=True,
        label_visibility="collapsed",
        key="nav_radio_router"
    )

    if nav_selection != st.session_state.get("bottom_nav", "Scanner"):
        st.session_state["bottom_nav"] = nav_selection
        st.rerun()


if __name__ == "__main__":
    main()