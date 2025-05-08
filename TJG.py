import streamlit as st
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Sample function to simulate fetching podcast data (titles, descriptions, etc.)
def get_podcast_data():
    # Placeholder for podcast data
    # In a real system, this would be fetched from the Spotify API or a database
    podcasts = [
        {"title": "Tech Innovations", "description": "Exploring the latest in technology, AI, and innovation."},
        {"title": "Travel the World", "description": "Join us as we explore different cultures and exotic locations."},
        {"title": "Healthy Living", "description": "Tips and tricks for a healthy lifestyle, fitness, and nutrition."},
        {"title": "Mindful Moments", "description": "Mindfulness practices and mental health tips."},
        {"title": "True Crime Tales", "description": "Real-life crime stories and investigations."},
    ]
    return podcasts

# Function to recommend podcasts based on user preferences
def recommend_podcasts(user_profile, podcasts):
    # Combine podcast titles and descriptions into a single string for text analysis
    podcast_texts = [podcast['title'] + ' ' + podcast['description'] for podcast in podcasts]
    
    # Initialize the TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(podcast_texts)
    
    # User preferences (mood, interests, etc.) as a search query
    user_query = ' '.join(user_profile.get('interests', [])) + ' ' + ' '.join(user_profile.get('mood', []))
    
    # Convert user preferences to a vector
    user_vector = vectorizer.transform([user_query])
    
    # Compute the cosine similarity between the user profile and the podcast descriptions
    cosine_similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()
    
    # Get the indices of the podcasts with the highest similarity
    recommended_indices = np.argsort(cosine_similarities)[::-1]
    
    # Return the top N recommended podcasts
    top_n = 3
    recommendations = [podcasts[i] for i in recommended_indices[:top_n]]
    return recommendations

# Streamlit interface
st.set_page_config(page_title="Spotify Podcast Filter", layout="centered")

# Title of the app
st.title("Spotify Podcast Filter")

# User Inputs
interests = st.text_input("Enter your interests (comma separated)", "technology, AI, innovation")
mood = st.text_input("Enter your mood (comma separated)", "curious, excited")

# Convert the user inputs into a list
user_profile = {
    "interests": [i.strip() for i in interests.split(",")],
    "mood": [m.strip() for m in mood.split(",")]
}

# Fetch podcasts (placeholder, in real code this would come from Spotify API)
podcasts = get_podcast_data()

# Get recommendations based on the user profile
recommended_podcasts = recommend_podcasts(user_profile, podcasts)

# Display the recommended podcasts
st.write("### Recommended Podcasts:")
for podcast in recommended_podcasts:
    st.write(f"**{podcast['title']}**: {podcast['description']}")

