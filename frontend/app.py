import sys
from pathlib import Path

import streamlit as st

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from frontend.api_client import APIClient, APIClientError  # noqa: E402

# Page Config
st.set_page_config(
    page_title="Zomato AI Restaurant Recommendations",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS Styling
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        color: #E23744;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #555555;
        margin-bottom: 1.5rem;
    }
    .card-container {
        background-color: #FFFFFF;
        border: 1px solid #EAEAEA;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
    }
    .rank-badge {
        background-color: #E23744;
        color: white;
        font-weight: 700;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    .rating-badge {
        background-color: #24963F;
        color: white;
        font-weight: 700;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.9rem;
    }
    .cuisine-tag {
        background-color: #F4F4F6;
        color: #333333;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        margin-right: 0.4rem;
        display: inline-block;
    }
    .explanation-box {
        background-color: #F8F9FA;
        border-left: 4px solid #E23744;
        padding: 0.8rem 1rem;
        border-radius: 4px;
        margin-top: 0.8rem;
        font-size: 0.95rem;
        color: #2D3748;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

api_client = APIClient()


@st.cache_data(ttl=600)
def load_cities():
    try:
        return api_client.get_cities()
    except APIClientError:
        return []


@st.cache_data(ttl=600)
def load_cuisines():
    try:
        return api_client.get_cuisines()
    except APIClientError:
        return []


def load_locations(city):
    if not city:
        return []
    return api_client.get_locations(city)


# Main Header
st.markdown(
    '<div class="main-title">🍽️ Zomato AI Restaurant Recommender</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-title">'
    "Discover personalized recommendations powered by Zomato dataset & AI ranking."
    "</div>",
    unsafe_allow_html=True,
)

# Sidebar Preference Form
st.sidebar.header("🎯 Preferences & Filters")

cities = load_cities()
if not cities:
    st.sidebar.error(
        "⚠️ Unable to connect to backend server. "
        "Please ensure FastAPI is running on http://localhost:8000"
    )
    selected_city = None
else:
    selected_city = st.sidebar.selectbox("Select City *", options=cities, index=0)

locations = load_locations(selected_city) if selected_city else []
selected_location = st.sidebar.selectbox(
    "Specific Location / Neighborhood (Optional)",
    options=["All Locations"] + locations,
)
if selected_location == "All Locations":
    selected_location = None

budget_options = {
    "Any Budget": None,
    "Low (≤ ₹500 for two)": "low",
    "Medium (₹501–₹1500 for two)": "medium",
    "High (> ₹1500 for two)": "high",
}
budget_label = st.sidebar.radio("Budget Tier", options=list(budget_options.keys()))
selected_budget = budget_options[budget_label]

all_cuisines = load_cuisines()
selected_cuisines = st.sidebar.multiselect(
    "Preferred Cuisines (Optional)", options=all_cuisines
)

min_rating = st.sidebar.slider(
    "Minimum Rating", min_value=0.0, max_value=5.0, value=0.0, step=0.1
)
if min_rating == 0.0:
    min_rating = None

col1, col2 = st.sidebar.columns(2)
online_order = col1.checkbox("Online Order")
book_table = col2.checkbox("Book Table")

additional_notes = st.sidebar.text_area(
    "Special Notes / Dietary Preferences",
    placeholder="e.g. Cozy outdoor seating with vegan pizza options...",
    max_chars=500,
)

top_k = st.sidebar.slider(
    "Number of Recommendations", min_value=1, max_value=15, value=5
)

submit_btn = st.sidebar.button("✨ Get AI Recommendations", use_container_width=True)

# Processing & Display Results
if submit_btn:
    if not selected_city:
        st.error("Please select a valid city before submitting.")
    else:
        clean_notes = additional_notes.strip() if additional_notes.strip() else None
        payload = {
            "city": selected_city,
            "location": selected_location,
            "budget": selected_budget,
            "cuisines": selected_cuisines,
            "min_rating": min_rating,
            "online_order": online_order if online_order else None,
            "book_table": book_table if book_table else None,
            "additional_notes": clean_notes,
            "top_k": top_k,
        }

        with st.spinner("🤖 Consulting AI recommendation engine..."):
            try:
                response = api_client.get_recommendations(payload)

                relaxed = response.get("relaxed_constraints", [])
                if relaxed:
                    relaxed_str = ", ".join(relaxed)
                    st.warning(
                        "ℹ️ **Notice:** Fewer than 5 matches found with exact criteria. "
                        f"Relaxed constraint(s): **{relaxed_str}**."
                    )

                summary = response.get("summary")
                if summary:
                    st.info(f"📌 **Summary:** {summary}")

                recommendations = response.get("recommendations", [])
                if not recommendations:
                    st.error(
                        "No matching restaurants found. Try broadening your selections."
                    )
                else:
                    st.subheader(
                        f"Top {len(recommendations)} Recommendations for you"
                    )

                    for item in recommendations:
                        rest = item["restaurant"]
                        rank = item["rank"]
                        explanation = item.get("explanation")

                        rating_display = (
                            f"★ {rest['rating']:.1f}/5.0"
                            if rest.get("rating") is not None
                            else "★ Unrated"
                        )
                        cost_val = rest.get("cost_for_two")
                        cost_display = (
                            f"₹{cost_val} for two" if cost_val else "Cost N/A"
                        )
                        budget_val = rest.get("budget_tier")
                        tier_display = (
                            f"({budget_val.capitalize()} budget)" if budget_val else ""
                        )

                        cuisines_list = rest.get("cuisines", [])
                        cuisines_html = "".join(
                            [
                                f'<span class="cuisine-tag">{c.title()}</span>'
                                for c in cuisines_list
                            ]
                        )

                        ai_exp_html = (
                            f'<div class="explanation-box">🤖 '
                            f"<strong>AI Note:</strong> {explanation}</div>"
                            if explanation
                            else ""
                        )

                        loc_str = rest.get("location", "")
                        city_str = rest.get("city", "")
                        votes_cnt = rest.get("votes", 0)
                        rest_name = rest["name"]

                        card_html = (
                            '<div class="card-container">\n'
                            f'  <div class="rank-badge">#{rank} PICK</div>\n'
                            '  <div style="display: flex; justify-content:'
                            ' space-between; align-items: baseline;">\n'
                            '    <h3 style="margin: 0; color: #111111;">'
                            f"{rest_name}</h3>\n"
                            f'    <span class="rating-badge">{rating_display}'
                            "</span>\n"
                            "  </div>\n"
                            '  <p style="color: #666666; margin: 0.3rem 0;">\n'
                            f"    📍 <strong>{loc_str}</strong> ({city_str})\n"
                            f"    &nbsp;|&nbsp; 💰 {cost_display} {tier_display}\n"
                            f"    &nbsp;|&nbsp; 🗳️ {votes_cnt} votes\n"
                            "  </p>\n"
                            "  <div style=\"margin-top: 0.5rem;\">"
                            f"{cuisines_html}</div>\n"
                            f"  {ai_exp_html}\n"
                            "</div>"
                        )

                        st.markdown(card_html, unsafe_allow_html=True)


                        if rest.get("url"):
                            st.link_button("🔗 View on Zomato", rest["url"])
                        st.write("---")

            except APIClientError as e:
                st.error(f"❌ {e}")
else:
    st.info(
        "👈 Select your dining preferences in the sidebar "
        "and click **Get AI Recommendations** to begin!"
    )
