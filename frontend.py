import base64
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="EstatiQ — Smart Real Estate AI Hub",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = "http://127.0.0.1:8000"
PAK_CITIES = [
    "Karachi",
    "Lahore",
    "Islamabad",
    "Rawalpindi",
    "Hyderabad",
    "Sukkur",
    "Ranipur",
    "Larkana",
    "Nawabshah",
    "Peshawar",
    "Quetta",
    "Multan",
    "Faisalabad",
    "Other",
]

# ==========================================
# PROFESSIONAL DARK THEME STYLING
# ==========================================
st.markdown(
    """
<style>
    /* ── Main Background ── */
    .stApp {
        background: linear-gradient(160deg, #0a0e17 0%, #131a2e 40%, #0d1520 100%);
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 60%, #0d1117 100%);
        border-right: 1px solid #21262d;
    }

    /* ── 3D Glassmorphism Cards ── */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(13, 17, 23, 0.7);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(48, 54, 61, 0.8);
        border-radius: 14px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4),
                    inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: transform 0.35s ease, box-shadow 0.35s ease;
    }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.55),
                    0 0 20px rgba(56, 189, 248, 0.08),
                    inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }

    /* ── Headings ── */
    h1 {
        background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    h2, h3 {
        background: linear-gradient(135deg, #38bdf8, #67e8f9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(13, 17, 23, 0.6);
        border-radius: 12px;
        padding: 5px;
        border: 1px solid #21262d;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        color: #8b949e;
        font-weight: 600;
        padding: 10px 28px;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1f6feb, #388bfd);
        color: #ffffff !important;
        box-shadow: 0 4px 16px rgba(56, 139, 253, 0.35);
    }

    /* ── Primary Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%);
        color: #ffffff;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        letter-spacing: 0.3px;
        box-shadow: 0 4px 14px rgba(31, 111, 235, 0.35);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 22px rgba(56, 139, 253, 0.5);
        background: linear-gradient(135deg, #388bfd 0%, #58a6ff 100%);
    }

    /* ── Form Submit Buttons ── */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: #ffffff;
        border: 1px solid #2ea043;
        border-radius: 10px;
        font-weight: 700;
        font-size: 1rem;
        box-shadow: 0 4px 16px rgba(46, 160, 67, 0.3);
        transition: all 0.3s ease;
    }
    .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #2ea043 0%, #3fb950 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 22px rgba(46, 160, 67, 0.45);
    }

    /* ── Input Fields ── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        background: rgba(22, 27, 34, 0.9) !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        color: #e6edf3 !important;
    }

    /* ── Metric Cards ── */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(31, 111, 235, 0.1), rgba(56, 189, 248, 0.08));
        border: 1px solid rgba(48, 54, 61, 0.8);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stMetric"] label {
        color: #58a6ff !important;
        font-weight: 600;
        font-size: 0.85rem;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #e6edf3 !important;
        font-weight: 700;
    }

    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #30363d, #388bfd40, #30363d, transparent);
    }
    .stCaption { color: #8b949e !important; }
</style>
""",
    unsafe_allow_html=True,
)

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "username" not in st.session_state:
  st.session_state.username = ""
if "full_name" not in st.session_state:
  st.session_state.full_name = ""


# ==========================================
# AUTHENTICATION WALL
# ==========================================
if not st.session_state.logged_in:
  st.markdown(
      """
        <div style="text-align:center; padding: 30px 10px 10px;">
            <div style="font-size: 4rem; margin-bottom: 8px;">🏡</div>
            <h1 style="font-size: 2.4rem; margin: 0; background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                EstatiQ
            </h1>
            <p style="color: #8b949e; font-size: 1.05rem; margin-top: 6px;">
                Intelligent Real Estate Platform — Powered by AI
            </p>
        </div>
        """,
      unsafe_allow_html=True,
  )

  st.divider()

  tab_signin, tab_signup = st.tabs(["🔑  Sign In", "📝  Create Account"])

  # ── SIGN IN ──
  with tab_signin:
    _left, col_form, _right = st.columns([1, 2, 1])
    with col_form:
      with st.container(border=True):
        st.markdown(
            """
                    <div style="text-align:center; margin-bottom: 6px;">
                        <span style="font-size: 2.5rem;">🔐</span>
                        <h3 style="margin: 8px 0 2px; background: linear-gradient(135deg, #38bdf8, #67e8f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                            Welcome Back
                        </h3>
                        <p style="color: #8b949e; font-size: 0.9rem;">
                            Sign in to access your dashboard
                        </p>
                    </div>
                    """,
            unsafe_allow_html=True,
        )
        with st.form("wall_signin_form"):
          s_user = st.text_input(
              "Username", placeholder="Enter your username"
          )
          s_pass = st.text_input(
              "Password", type="password", placeholder="Enter your password"
          )
          st.markdown("")
          s_btn = st.form_submit_button("🚀  Sign In", use_container_width=True)
          if s_btn:
            if not s_user or not s_pass:
              st.warning("Please enter both username and password.")
            else:
              try:
                r = requests.post(
                    f"{API_BASE}/signin",
                    json={"username": s_user, "password": s_pass},
                    timeout=5,
                )
                if r.status_code == 200:
                  res_data = r.json()
                  if "username" in res_data:
                    st.session_state.logged_in = True
                    st.session_state.username = res_data["username"]
                    st.session_state.full_name = res_data["full_name"]
                    st.success("✅ Authenticated! Redirecting...")
                    st.rerun()
                  else:
                    st.error(
                        res_data.get("error", "Invalid username or password.")
                    )
                else:
                  st.error("⚠️ Server returned an error. Please try again.")
              except requests.exceptions.ConnectionError:
                st.error(
                    "⚠️ Backend server is not running. Please start it with:"
                    " `python file.py`"
                )
              except Exception as e:
                st.error(f"Connection error: {e}")

        st.caption(
            "Don't have an account? Switch to the **Create Account** tab."
        )

  # ── SIGN UP ──
  with tab_signup:
    _left2, col_form2, _right2 = st.columns([1, 2, 1])
    with col_form2:
      with st.container(border=True):
        st.markdown(
            """
                    <div style="text-align:center; margin-bottom: 6px;">
                        <span style="font-size: 2.5rem;">📋</span>
                        <h3 style="margin: 8px 0 2px; background: linear-gradient(135deg, #38bdf8, #67e8f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                            Create Your Account
                        </h3>
                        <p style="color: #8b949e; font-size: 0.9rem;">
                            Join EstatiQ and start exploring properties
                        </p>
                    </div>
                    """,
            unsafe_allow_html=True,
        )
        with st.form("wall_signup_form"):
          u_user = st.text_input(
              "Username", placeholder="Choose a unique username"
          )
          u_name = st.text_input("Full Name", placeholder="Your full name")

          col_ph, col_ct = st.columns(2)
          u_phone = col_ph.text_input("Phone", placeholder="03001234567")
          u_city = col_ct.selectbox("City", PAK_CITIES)

          u_email = st.text_input(
              "Email Address", placeholder="you@example.com"
          )
          u_pass = st.text_input(
              "Password", type="password", placeholder="Create a strong password"
          )
          st.markdown("")
          u_btn = st.form_submit_button(
              "✨  Create Account", use_container_width=True
          )
          if u_btn:
            if not all([u_user, u_name, u_phone, u_email, u_pass]):
              st.warning("All fields are required.")
            else:
              try:
                r = requests.post(
                    f"{API_BASE}/signup",
                    json={
                        "username": u_user,
                        "full_name": u_name,
                        "phone": u_phone,
                        "city": u_city,
                        "email": u_email,
                        "password": u_pass,
                    },
                    timeout=5,
                )
                if r.status_code == 200:
                  res_data = r.json()
                  if "message" in res_data:
                    st.session_state.logged_in = True
                    st.session_state.username = u_user
                    st.session_state.full_name = u_name
                    st.success(
                        "🎉 Account created successfully! Logging you in..."
                    )
                    st.rerun()
                  else:
                    st.error(res_data.get("error", "Signup failed."))
                else:
                  st.error("⚠️ Server returned an error. Please try again.")
              except requests.exceptions.ConnectionError:
                st.error(
                    "⚠️ Backend server is not running. Please start it with:"
                    " `python file.py`"
                )
              except Exception as e:
                st.error(f"Connection error: {e}")

        st.caption("Already registered? Switch to the **Sign In** tab.")

  st.stop()


# ==========================================
# MAIN APP — AFTER LOGIN
# ==========================================

try:
  res = requests.get(f"{API_BASE}/properties", timeout=5)
  properties_db = res.json() if res.status_code == 200 else []
except Exception:
  properties_db = []
  st.error(
      "⚠️ Backend server is offline. Start it by running `python file.py` in your"
      " terminal."
  )

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.markdown("## 👤 Profile")
st.sidebar.markdown(
    f"""
    <div style="background: rgba(31,111,235,0.08); padding: 14px 16px; border-radius: 12px; border: 1px solid #21262d;">
        <p style="margin:0; color:#58a6ff; font-size:0.78rem; font-weight:600; text-transform:uppercase; letter-spacing:1px;">Logged In</p>
        <p style="margin:4px 0 0; color:#e6edf3; font-size:1.05rem; font-weight:700;">🧑‍💼 {st.session_state.full_name}</p>
        <p style="margin:2px 0 0; color:#8b949e; font-size:0.85rem;">@{st.session_state.username}</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown("")
if st.sidebar.button("🚪  Logout", use_container_width=True):
  st.session_state.logged_in = False
  st.session_state.username = ""
  st.session_state.full_name = ""
  st.rerun()

st.sidebar.divider()
st.sidebar.markdown("## 🔍 Filters")
available_props = [
    p for p in properties_db if p.get("status", "Available") == "Available"
]

filter_purpose = st.sidebar.selectbox(
    "Purpose", ["All", "For Sale", "For Rent"]
)
filter_city = st.sidebar.selectbox("City", ["All"] + PAK_CITIES)
max_budget = st.sidebar.slider(
    "Max Budget (Rs.)",
    min_value=10_000,
    max_value=100_000_000,
    step=50_000,
    value=100_000_000,
)

filtered_properties = [
    p for p in available_props if p["asking_price"] <= max_budget
]
if filter_purpose != "All":
  filtered_properties = [
      p for p in filtered_properties if p.get("purpose") == filter_purpose
  ]
if filter_city != "All":
  filtered_properties = [
      p for p in filtered_properties if p["city"] == filter_city
  ]

# AI Assistant
st.sidebar.divider()
st.sidebar.markdown("## 🤖 AI Assistant")
user_help_query = st.sidebar.text_input(
    "Ask a question...",
    key="help_query_input",
    placeholder="e.g. How to list a property?",
)
if st.sidebar.button("Get Answer", use_container_width=True):
  if user_help_query:
    with st.sidebar.spinner("Analyzing..."):
      try:
        h_res = requests.post(
            f"{API_BASE}/help_chat",
            json={"question": user_help_query},
            timeout=10,
        )
        if h_res.status_code == 200:
          st.sidebar.info(h_res.json().get("answer"))
      except Exception:
        st.sidebar.error("Connection error.")


# ==========================================
# MAIN HEADER
# ==========================================
st.markdown("# 🏡 EstatiQ — AI Real Estate Platform")
st.caption(
    "Intelligent property discovery, AI-driven price analysis, and seamless"
    " listing management."
)
st.divider()

tab_buy, tab_sell = st.tabs(["🛒  Explore Properties", "💰  Post a New Listing"])

# ==========================================
# TAB 1: EXPLORE
# ==========================================
with tab_buy:
  col_m1, col_m2, col_m3 = st.columns(3)
  col_m1.metric("📊 Listings", len(filtered_properties))
  avg_price = (
      sum(p["asking_price"] for p in filtered_properties)
      / len(filtered_properties)
      if filtered_properties
      else 0
  )
  col_m2.metric("💵 Avg Price", f"Rs. {avg_price:,.0f}")
  col_m3.metric("📍 City", filter_city)

  st.divider()

  if filtered_properties:
    st.markdown("##### 🗺️ Map View")
    map_data = pd.DataFrame(
        [{"lat": p["lat"], "lon": p["lon"]} for p in filtered_properties]
    )
    st.map(map_data, zoom=10)
  else:
    st.info("No properties found matching your filters. Try adjusting search.")

  st.divider()

  for prop in reversed(filtered_properties):
    with st.container(border=True):
      if prop.get("is_suspicious", False):
        st.error(
            "🚨 **AI Fraud Alert:** This listing's price appears unusual for"
            " its specifications."
        )

      price_label = (
          f"Rs. {prop['asking_price']:,} / month"
          if prop.get("purpose") == "For Rent"
          else f"Rs. {prop['asking_price']:,}"
      )

      st.markdown(
          f"### 🏠 {prop['bedrooms']} BHK — {prop['purpose']}"
          f" in {prop['society']}, {prop['city']}"
      )
      col_a, col_p = st.columns(2)
      col_a.markdown(f"📐 **Area:** {prop['area_sqft']} Sq.Ft")
      col_p.markdown(f"💰 **Price:** {price_label}")

      st.divider()

      col_details, col_actions = st.columns([2, 1])

      with col_details:
        st.markdown(
            f"👤 **Owner:** {prop['owner']} &nbsp;|&nbsp; 🆔"
            f" `{prop.get('owner_username', 'N/A')}`"
        )
        st.markdown(f"📞 **Contact:** {prop['contact']}")
        if prop.get("email"):
          st.markdown(f"✉️ **Email:** {prop['email']}")

      with col_actions:
        if st.button(
            "🧠 AI Price Insight",
            key=f"btn_{prop['id']}",
            use_container_width=True,
        ):
          with st.spinner("Analyzing..."):
            try:
              response = requests.post(
                  f"{API_BASE}/predict",
                  json={
                      "area_sqft": prop["area_sqft"],
                      "bedrooms": prop["bedrooms"],
                      "asking_price": prop["asking_price"],
                  },
                  timeout=15,
              )
              if response.status_code == 200:
                result = response.json()
                st.success(
                    f"**Predicted Value:** Rs. {result['predicted_price']:,.0f}"
                )
                st.info(f"**AI Insight:** {result['ai_insight']}")
            except Exception:
              st.error("Unable to reach AI backend.")

        is_owner = (
            prop.get("owner_username") == st.session_state.username
        ) or (prop.get("owner") == st.session_state.full_name)
        if is_owner:
          col_sold, col_del = st.columns(2)
          with col_sold:
            if st.button(
                "🤝 Mark Sold", key=f"sold_{prop['id']}", use_container_width=True
            ):
              requests.put(f"{API_BASE}/mark_sold/{prop['id']}")
              st.rerun()
          with col_del:
            if st.button(
                "🗑️ Delete",
                key=f"del_{prop['id']}",
                type="primary",
                use_container_width=True,
            ):
              requests.delete(f"{API_BASE}/delete_property/{prop['id']}")
              st.rerun()
        else:
          st.caption(
              "🔒 *Only the property creator can modify or delete this listing.*"
          )

      # Media Gallery
      images_list = prop.get("images", []) or []
      videos_list = prop.get("videos", []) or []

      if images_list or videos_list:
        with st.expander(
            f"📸 Media — {len(images_list)} Photos, {len(videos_list)} Videos"
        ):
          if images_list:
            st.markdown("##### 🖼️ Photos")
            img_cols = st.columns(min(len(images_list), 4))
            for idx, img_b64 in enumerate(images_list):
              try:
                img_bytes = base64.b64decode(img_b64)
                img_cols[idx % 4].image(img_bytes, use_container_width=True)
              except Exception:
                pass
          if videos_list:
            st.markdown("##### 🎥 Videos")
            for vid_b64 in videos_list:
              try:
                vid_bytes = base64.b64decode(vid_b64)
                st.video(vid_bytes)
              except Exception:
                pass

      # Ratings & Comments
      with st.expander("⭐ Ratings, Reviews & Recommendations"):
        c_rate, c_comm = st.columns(2)

        with c_rate:
          st.markdown("##### ⭐ Ratings")
          p_ratings = prop.get("ratings", []) or []
          if p_ratings:
            avg_r = sum(p_ratings) / len(p_ratings)
            st.markdown(
                f"**Average:** {avg_r:.1f} ⭐ ({len(p_ratings)} ratings)"
            )
          else:
            st.caption("No ratings yet.")

          new_rating = st.selectbox(
              "Rate:", [5, 4, 3, 2, 1], key=f"rate_box_{prop['id']}"
          )
          if st.button(
              "Submit", key=f"rate_btn_{prop['id']}", use_container_width=True
          ):
            requests.post(
                f"{API_BASE}/add_rating/{prop['id']}",
                json={"rating": new_rating},
            )
            st.rerun()

        with c_comm:
          st.markdown("##### 💬 Discussion")
          p_comments = prop.get("comments", []) or []
          for idx, c in enumerate(p_comments):
            col_c1, col_c2 = st.columns([4, 1])
            col_c1.markdown(f"🗣️ **{c['name']}:** {c['text']}")
            if col_c2.button(
                f"👍 {c.get('likes', 0)}", key=f"like_{prop['id']}_{idx}"
            ):
              requests.put(f"{API_BASE}/like_comment/{prop['id']}/{idx}")
              st.rerun()

          with st.form(
              key=f"comment_form_{prop['id']}", clear_on_submit=True
          ):
            st.caption(f"As: **{st.session_state.username}**")
            c_text = st.text_input(
                "Comment...", placeholder="Share your thoughts..."
            )
            if (
                st.form_submit_button("Post", use_container_width=True)
                and c_text
            ):
              requests.post(
                  f"{API_BASE}/add_comment/{prop['id']}",
                  json={"name": st.session_state.username, "text": c_text},
              )
              st.rerun()

        st.divider()
        st.markdown("##### ✨ Similar Properties (AI)")
        try:
          rec_res = requests.post(
              f"{API_BASE}/recommendations/{prop['id']}", timeout=5
          )
          if rec_res.status_code == 200:
            recs = rec_res.json()
            if recs:
              for r in recs:
                st.markdown(
                    f"- 🏡 **{r['bedrooms']} BHK in {r['society']},"
                    f" {r['city']}** — Rs. {r['asking_price']:,}"
                    f" ({r['area_sqft']} Sq.Ft)"
                )
            else:
              st.caption("No similar properties found.")
        except Exception:
          pass


# ==========================================
# TAB 2: POST LISTING
# ==========================================
with tab_sell:
  st.markdown("## 📢 List Your Property")
  st.caption("Complete the form below to publish your listing on EstatiQ.")
  st.divider()

  with st.form("sell_property_form", clear_on_submit=True):
    st.markdown("#### 📍 Location")
    col_purp, col_c, col_city = st.columns(3)
    purpose = col_purp.selectbox("Type", ["For Sale", "For Rent"])
    country = col_c.selectbox("Country", ["Pakistan", "UAE", "UK", "USA"])
    city = col_city.selectbox("City", PAK_CITIES)
    society = st.text_input(
        "Society / Area", placeholder="e.g. DHA Phase 8, Gulshan-e-Iqbal"
    )

    st.divider()
    st.markdown("#### 📸 Media")
    col_img, col_vid = st.columns(2)
    uploaded_images = col_img.file_uploader(
        "Photos", type=["jpg", "png", "jpeg"], accept_multiple_files=True
    )
    uploaded_videos = col_vid.file_uploader(
        "Videos", type=["mp4", "mov", "avi"], accept_multiple_files=True
    )

    st.divider()
    st.markdown("#### 🏠 Specifications")
    col_area, col_bed = st.columns(2)
    area_sqft = col_area.number_input(
        "Area (Sq.ft)", min_value=100, step=50, value=1000
    )
    bedrooms = col_bed.number_input("Bedrooms", min_value=1, step=1, value=2)
    price_raw = st.text_input(
        "Price / Rent (Rs.)", value="1500000", help="Enter numeric value"
    )

    col_lat, col_lon = st.columns(2)
    lat = col_lat.number_input("Latitude", value=24.8607, format="%.4f")
    lon = col_lon.number_input("Longitude", value=67.0011, format="%.4f")

    st.divider()
    st.markdown("#### 📞 Contact")
    col_n, col_ph, col_em = st.columns(3)
    owner_name = col_n.text_input("Name", value=st.session_state.full_name)
    contact_number = col_ph.text_input("Phone", placeholder="03001234567")
    email_address = col_em.text_input("Email", placeholder="you@example.com")

    st.markdown("")
    submitted = st.form_submit_button(
        "🚀  Publish Listing", use_container_width=True
    )

    if submitted:
      if owner_name and contact_number and society and price_raw:
        try:
          asking_price = float(price_raw.replace(",", "").strip())
        except ValueError:
          st.error("Invalid price value.")
          asking_price = 0.0

        if asking_price > 0:
          encoded_images = [
              base64.b64encode(img.read()).decode("utf-8")
              for img in uploaded_images
          ] if uploaded_images else []
          encoded_videos = [
              base64.b64encode(vid.read()).decode("utf-8")
              for vid in uploaded_videos
          ] if uploaded_videos else []

          payload = {
              "owner_username": st.session_state.username,
              "owner": owner_name,
              "contact": contact_number,
              "email": email_address,
              "purpose": purpose,
              "country": country,
              "city": city,
              "society": society,
              "area_sqft": float(area_sqft),
              "bedrooms": int(bedrooms),
              "asking_price": asking_price,
              "lat": float(lat),
              "lon": float(lon),
              "images": encoded_images,
              "videos": encoded_videos,
          }

          try:
            res = requests.post(
                f"{API_BASE}/add_property", json=payload, timeout=10
            )
            if res.status_code == 200:
              st.success(
                  f"🎉 Listed! {len(encoded_images)} photos &"
                  f" {len(encoded_videos)} videos uploaded."
              )
              st.balloons()
            else:
              st.error("Failed to save. Try again.")
          except Exception:
            st.error("Server connection failed.")
      else:
        st.error("Please fill: Name, Contact, Society, and Price.")