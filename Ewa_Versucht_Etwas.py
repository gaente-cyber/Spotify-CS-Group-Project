import streamlit as st
st.set_page_config(page_title="Spotify Podcast Filter", layout="centered")

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Spotify Authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="",
    client_secret="",
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-library-read"
))

# Language Code Mapping
@st.cache_data
def map_language(code):
    code = code.lower()
    if code.startswith("de"):
        return "German"
    elif code.startswith("en"):
        return "English"
    elif code.startswith("fr"):
        return "French"
    elif code.startswith("es"):
        return "Spanish"
    elif code.startswith("it"):
        return "Italian"
    else:
        return "Other"

profile_file = "user_profile.json"
if os.path.exists(profile_file):
    with open(profile_file, "r") as f:
        user_profile = json.load(f)
        first_time = False
else:
    user_profile = {}
    first_time = True

if first_time:
    st.title("👋 Welcome to your Podcast App!")
    st.markdown("Let's first learn a bit about your interests to give you better recommendations later.")

    interests = ["True Crime", "Science", "Comedy", "Sports", "Business", "Technology", "Society", "Health", "Art", "Music", "Spirituality"]
    selected_interests = st.multiselect("What are you particularly interested in?", interests)

    languages = ["German", "English", "French", "Spanish", "Italian"]
    preferred_languages = st.multiselect("Which languages do you prefer?", languages)

    duration = st.slider("How long should an ideal episode be for you? (minutes)", 5, 120, (20, 60))

    mood = st.multiselect("What mood should the podcast create?", ["Relaxation", "Learning", "Laughter", "Inspiration", "Focus", "Distraction"])

    location = st.selectbox("Where do you most often listen to podcasts?", ["At home", "On the go", "In the car", "During sports"])

    if st.button("✅ Save profile & start"):
        user_profile = {
            "interests": selected_interests,
            "language": preferred_languages,
            "duration": duration,
            "mood": mood,
            "location": location
        }
        with open(profile_file, "w") as f:
            json.dump(user_profile, f)
        st.success("🎉 Your profile has been saved! Please restart the app.")
        st.stop()

if not first_time:
    st.title("🎵 Smart Spotify Podcast Filter")

    st.markdown("""
    ### ❗ Problem Statement
    Users spend a lot of time finding the right podcast episodes on Spotify. The platform lacks precise filters or personalized recommendations on the episode level. Our app solves this with an intelligent filtering system and personalized matching.

    **🎯 Solution:**
    The app combines your interests with smart filters (e.g. duration, language, host) and machine learning to recommend podcasts – for a perfect podcast-consumer fit.
    """)

    topics = ["True Crime", "Science", "Comedy", "Sports", "Business", "Health", "Technology", "Society"]
    selected_topics = st.multiselect("🎙️ Topics / Genres", topics)
    language_filter = st.multiselect("🌍 Language(s)", ["German", "English", "French", "Spanish", "Italian"])
    country_code = st.selectbox("🌐 Which country do you want to search in?", ["CH", "DE", "AT", "US", "GB", "FR", "IT", "ES"], index=0)
    rating = st.slider("⭐ Minimum rating (0 = unknown, 100 = super popular)", 0, 100, 50)
    host_name = st.text_input("👤 Podcast host name (optional)")
    guests = st.text_input("🧑‍🤝‍🧑 Guest name(s) (optional)")
    min_duration, max_duration = st.slider("⏱️ Episode duration (in minutes)", 5, 180, (10, 60))

    if st.button("🔍 Start search"):
        with st.spinner("Loading suitable podcasts..."):
            profile_text = " ".join(user_profile["interests"] + user_profile["mood"])
            profile_text += " " + user_profile["location"]
            profile_text += f" Duration {user_profile['duration'][0]} to {user_profile['duration'][1]} minutes"
            profile_text += " " + " ".join(selected_topics)
            profile_text += " " + host_name + " " + guests

            query = " ".join(user_profile["interests"] + selected_topics)
            results = sp.search(q=query, type="show", limit=20, market=country_code)

            show_texts = []
            show_info = []
            avg_durations = []
            language_list = []

            for show in results["shows"]["items"]:
                name = show["name"]
                description = show["description"]
                publisher = show["publisher"]
                show_language = show.get("languages", [""])[0]
                show_id = show["id"]
                link = show["external_urls"]["spotify"]
                image_url = show["images"][0]["url"] if show.get("images") else ""

                if not any(map_language(show_language) == l for l in language_filter):
                    continue

                episodes = sp.show_episodes(show_id, limit=3)["items"]
                episodes_text = " ".join([ep["description"] for ep in episodes if ep and "description" in ep])
                episode_durations = [int(ep["duration_ms"] / 60000) for ep in episodes if ep and "duration_ms" in ep]

                if not any(min_duration <= d <= max_duration for d in episode_durations):
                    continue

                full_text = description + " " + episodes_text
                show_texts.append(full_text)
                show_info.append((name, publisher, description, link, image_url))
                if episode_durations:
                    avg_durations.append((name, sum(episode_durations) / len(episode_durations)))
                language_list.append(map_language(show_language))

            if show_texts:
                texts = show_texts + [profile_text]
                tfidf = TfidfVectorizer(stop_words='english')
                matrix = tfidf.fit_transform(texts)
                similarities = cosine_similarity(matrix[-1], matrix[:-1])[0]

                top_n = 5
                top_indices = similarities.argsort()[-top_n:][::-1]

                st.subheader("🎙️ Recommended Podcasts for You:")
                for idx in top_indices:
                    name, publisher, description, link, image_url = show_info[idx]
                    st.image(image_url, width=200)
                    st.markdown(f"**🎧 {name}** – by *{publisher}*")
                    st.write(f"📝 {description[:250]}...")
                    st.markdown(f"[🔗 Go to show on Spotify]({link})")
                    st.markdown("---")

                if avg_durations:
                    names, values = zip(*avg_durations)
                    st.subheader("⏱️ Average Episode Duration")
                    fig1, ax1 = plt.subplots()
                    ax1.barh(names, values, color="lightgreen")
                    ax1.set_xlabel("Minutes")
                    ax1.set_title("Average Episode Duration")
                    ax1.invert_yaxis()
                    st.pyplot(fig1)

                if selected_topics:
                    topic_counts = {t: selected_topics.count(t) for t in set(selected_topics)}
                    st.subheader("📚 Selected Topics")
                    fig2, ax2 = plt.subplots()
                    ax2.bar(topic_counts.keys(), topic_counts.values(), color="lightblue")
                    ax2.set_ylabel("Count")
                    ax2.set_title("Distribution of Selected Topics")
                    st.pyplot(fig2)

                if language_list:
                    language_counts = pd.Series(language_list).value_counts()
                    st.subheader("🌐 Languages of Recommended Podcasts")
                    fig3, ax3 = plt.subplots()
                    language_counts.plot(kind="bar", color="lightcoral", ax=ax3)
                    ax3.set_ylabel("Count")
                    ax3.set_title("Language Distribution")
                    st.pyplot(fig3)
            else:
                st.warning("⚠️ No suitable podcasts were found. Please adjust your filters.")

