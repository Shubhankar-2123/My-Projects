import streamlit as st
import pandas as pd
from recommender.hybrid import HybridRecommender

# Load data
games = pd.read_csv('data/Game_processed_data.csv')
ratings = pd.read_csv('data/ratings.csv')

# Initialize recommender
recommender = HybridRecommender(games, ratings)

# Streamlit UI
st.title('🎮 Game Recommendation Engine')

def display_recommendations(recs):
    """Helper function to safely display recommendations"""
    if recs.empty:
        st.warning("No recommendations found. Try selecting a different game or user.")
        return
    
    # Check which columns are available to display
    available_columns = []
    for col in ['Name', 'Primary Genre', 'Average User Rating', 'URL', 'Icon URL']:
        if col in recs.columns:
            available_columns.append(col)
    
    if not available_columns:
        st.error("No valid data to display")
        return
    
    st.dataframe(recs[available_columns])

col1, col2 = st.columns(2)

with col1:
    st.header('For New Users')
    selected_game = st.selectbox('Select a game you like:', [''] + games['Name'].tolist())
    if selected_game:
        game_url = games[games['Name'] == selected_game]['URL'].values[0]
        recs = recommender.recommend(game_url=game_url)
        display_recommendations(recs)

with col2:
    st.header('For Existing Users')
    user_id = st.selectbox('Select your user ID:', [''] + ratings['user_id'].unique().tolist())
    if user_id:
        recs = recommender.recommend(user_id=user_id)
        display_recommendations(recs)

st.header('Popular Games')
popular_recs = recommender.recommend()
display_recommendations(popular_recs)