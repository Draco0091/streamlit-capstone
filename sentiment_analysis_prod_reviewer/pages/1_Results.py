import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
import re
import random
from datetime import datetime

# Add the project root to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.web.app import AmazonReviewScraper, extract_price, predict_sentiment_from_reviews, get_exact_and_alternative_products

# Banner/Header
st.markdown(
    '<div class="main-header">'
    '<h1>🛒 E-commerce Product Analyzer</h1>'
    '<p style="font-size:1.2rem;">'
    'Analyze product sentiment and discover the best shopping options!'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

# Check for submitted link
link = st.session_state.get('submitted_link', None)
if not link:
    st.warning("No product link submitted. Please go to the main page and enter a link.")
    st.stop()

# Extract product price and reviews
try:
    product_price = extract_price(link)
except Exception as e:
    product_price = None
with st.spinner("Scraping Amazon reviews (up to 5 pages)..."):
    try:
        scraper = AmazonReviewScraper(headless=True)
        reviews = scraper.get_reviews(link, max_pages=5, max_reviews=50)
        scraper.close_browser()
    except Exception as e:
        st.error(f"Error scraping reviews: {e}")
        reviews = []
if reviews:
    sentiment, score, pos_count, neg_count, detailed_results, model_name = predict_sentiment_from_reviews(reviews)
    product_title = reviews[0].get('product_title', 'Amazon Product')
else:
    st.warning("No reviews found or failed to scrape reviews.")
    sentiment, score, pos_count, neg_count, detailed_results, model_name = "neutral", 0.5, 0, 0, [], "No Model"
    product_title = "Amazon Product"

# --- Results Layout ---
st.markdown(f"## Results Report")
st.markdown(f"**Product:** {product_title}")
st.markdown("---")
# Sample Reviews
st.markdown("### 📝 Sample Reviews")
for i, review in enumerate(reviews[:5]):
    st.write(f"**Review {i+1}:** {review.get('body', '')}")
st.markdown("---")
# Plots side by side
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Plot 1")
    if 'sentiment_distribution' in st.session_state:
        st.plotly_chart(st.session_state['sentiment_distribution'], use_container_width=True)
with col2:
    st.markdown("#### Plot 2")
    if 'sentiment_score' in st.session_state:
        st.plotly_chart(st.session_state['sentiment_score'], use_container_width=True)
st.markdown("---")
# Suggestions/Links
st.markdown("### 💡 Suggestions & Links")
st.write("Product recommendations and links will appear here.")
st.markdown("---")
# Try Again button
if st.button("Try Again"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun() 