import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
import re
import time
import random
from datetime import datetime

# Add the project root to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Create output directory for saved data if it doesn't exist
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../output/data'))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Import from the new directory structure using absolute imports
from src.scraper.amazon_review_scraper import AmazonReviewScraper
from src.scraper.amazon_price_extractor import extract_price
from src.models.model_integration import SentimentAnalyzer
from src.api.serp_api_integration import get_exact_and_alternative_products

# Initialize the sentiment analyzer
analyzer = SentimentAnalyzer()

def predict_sentiment_from_reviews(reviews):
    """
    Analyze reviews using the trained model
    """
    results = analyzer.analyze_reviews(reviews)
    sentiment = results['overall_sentiment']
    score = results['score']
    pos_count = results['positive_count']
    neg_count = results['negative_count']
    model_name = results.get('model_name', 'Sentiment Model')
    avg_confidence = results.get('average_confidence', None)
    
    # Create visualizations
    fig1, fig2 = analyzer.create_visualizations(results)
    
    # Store visualizations in session state
    st.session_state['sentiment_distribution'] = fig1
    st.session_state['sentiment_score'] = fig2
    st.session_state['model_name'] = model_name
    
    if avg_confidence:
        st.session_state['avg_confidence'] = f"{avg_confidence:.2f}"
    
    return sentiment, score, pos_count, neg_count, results['detailed_results'], model_name

def show_input_page():
    """Show the input page where users can enter a product link"""
    st.markdown(
        '<div class="main-header">'
        '<h1>🛒 E-commerce Product Analyzer</h1>'
        '<p style="font-size:1.2rem;">'
        'Analyze product sentiment and discover the best shopping options!'
        '</p>'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div style='text-align:center;'>
        <span style='font-size:1.5rem;'>🔗 Paste a product link below to get started!</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---")
    
    link = st.text_input("Enter product link:", key="product_link", label_visibility="visible")
    if st.button("Submit", key="submit_button"):
        if link:
            st.session_state['submitted_link'] = link
            st.session_state['current_view'] = 'results'
            st.session_state['page_refresh'] = True  # Trigger page refresh
        else:
            st.error("Please enter a product link first!")

def show_results_page():
    """Show the results page with analysis"""
    if 'submitted_link' not in st.session_state:
        st.error("No product link submitted. Please go back and enter a link.")
        return
    
    link = st.session_state['submitted_link']
    
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
            if key != 'current_view':  # Keep current_view
                del st.session_state[key]
        st.session_state['current_view'] = 'input'
        st.session_state['page_refresh'] = True  # Trigger page refresh

# Set page config for custom title and icon
st.set_page_config(
    page_title="E-commerce Product Analyzer",
    page_icon="🛒",
    layout="wide"
)

# Initialize session state
if 'current_view' not in st.session_state:
    st.session_state['current_view'] = 'input'
    st.session_state['page_refresh'] = False

# Show appropriate view based on session state
if st.session_state['current_view'] == 'input':
    show_input_page()
elif st.session_state['current_view'] == 'results':
    show_results_page()

# Handle page refresh
if st.session_state.get('page_refresh'):
    st.session_state['page_refresh'] = False

# Footer
st.markdown(
    '<div class="footer">'
    'Amazon E-Commerce Product Analyzer &copy; 2025 &mdash;'
    '</div>',
    unsafe_allow_html=True
)

# Modern, professional CSS (light theme)
st.markdown(
    """
    <style>
    body, .stApp {
        background: #f7fafd !important;
        color: #222 !important;
    }
    .main-header {
        background: linear-gradient(90deg, #1976d2 0%, #42a5f5 100%);
        color: white;
        padding: 2rem 1rem 1rem 1rem;
        border-radius: 14px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 24px rgba(25, 118, 210, 0.08);
    }
    .stTextInput > div > div > input {
        background-color: #fff;
        color: #222;
        border-radius: 8px;
        border: 1.5px solid #1976d2;
        font-size: 1.1rem;
        padding: 0.5rem 1rem;
        margin-bottom: 0.5rem;
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
    }
    .stButton > button {
        background: linear-gradient(90deg, #1976d2 0%, #42a5f5 100%);
        color: #fff;
        border: none;
        border-radius: 8px;
        font-size: 1.1rem;
        padding: 0.5rem 2.5rem;
        margin-top: 0.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(25, 118, 210, 0.08);
        transition: background 0.2s;
        width: 180px !important;
        min-width: 120px !important;
        max-width: 220px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        display: block;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #1565c0 0%, #2196f3 100%);
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background: #e3eafc;
        color: #1976d2;
        text-align: center;
        padding: 0.5rem 0;
        font-size: 0.95rem;
        border-top: 1px solid #bbdefb;
    }
    </style>
    """,
    unsafe_allow_html=True
) 