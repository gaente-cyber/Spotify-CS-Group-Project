import streamlit as st
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Grundsätzliche Konfiguration/Vorbereitug für Streamlit
st.set_page_config(page_title="Spotify Podcast Filter", layout="centered")

# Initialize session state
if "page_number" not in st.session_state:
    st.session_state.page_number = 0
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "interests": [],
        "languages": [],
        "duration": (20, 60),
        "mood": [],
        "location": ""
    }

profile_file = "user_profile.json"

# Spotify Authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="554c66803ecd4fe5ae23039953589266",  # Replace with real
    client_secret="42c3865847ef4b1885776511a21290f4",  # Replace with real
    redirect_uri="https://spotify-cs-group-project-xqcsina62p4b8jsffzagp3.streamlit.app",
    scope="user-library-read"
))

# Step definitions
steps = ["Welcome", "Interests", "Languages", "Duration", "Mood", "Location"]

def next_page():
    st.session_state.page_number += 1

def prev_page():
    if st.session_state.page_number > 0:
        st.session_state.page_number -= 1

# Progress
progress = min((st.session_state.page_number + 1) / len(steps), 1.0)
st.progress(progress)

# Step 0: Welcome
if st.session_state.page_number == 0:
    st.title("🎉 Welcome to Your Personalized Podcast Experience!")
    st.markdown("Let's set up your profile to get the best recommendations!")

    if st.button("🚀 Get Started"):
        next_page()

# Step 1: Interests
elif st.session_state.page_number == 1:
    st.title("🎯 Select Your Interests")

    interest_options = {
        "True Crime": "🕵️‍♂️",
        "Science": "🔬",
        "Comedy": "🎭",
        "Sports": "🏅",
        "Business": "💼",
        "Technology": "💻",
        "Society": "🏛️",
        "Health": "🧘",
        "Art": "🎨",
        "Music": "🎵",
        "Spirituality": "🧘‍♂️"
    }

    selected = []
    cols = st.columns(3)
    for idx, (interest, emoji) in enumerate(interest_options.items()):
        with cols[idx % 3]:
            if st.checkbox(f"{emoji} {interest}"):
                selected.append(interest)

    st.session_state.user_profile["interests"] = selected

# Step 2: Languages
elif st.session_state.page_number == 2:
    st.title("🌍 Select Your Preferred Languages")

    language_options = {
        "German": "🇩🇪",
        "English": "🇬🇧",
    }

    selected_langs = []
    cols = st.columns(3)
    for idx, (language, flag) in enumerate(language_options.items()):
        with cols[idx % 3]:
            if st.checkbox(f"{flag} {language}"):
                selected_langs.append(language)

    st.session_state.user_profile["languages"] = selected_langs

# Step 3: Duration
elif st.session_state.page_number == 3:
    st.title("🕒 Select Your Ideal Episode Length")

    st.session_state.user_profile["duration"] = st.slider(
        "Select the duration range (minutes)",
        min_value=5,
        max_value=120,
        value=st.session_state.user_profile["duration"]
    )

# Step 4: Mood
elif st.session_state.page_number == 4:
    st.title("😊 Choose the Mood of Podcasts")

    mood_options = [
        "Relaxation", "Learning", "Laughter",
        "Inspiration", "Focus", "Distraction"
    ]

    selected_moods = st.multiselect("Select one or more moods:", mood_options)
    st.session_state.user_profile["mood"] = selected_moods

# Step 5: Location
elif st.session_state.page_number == 5:
    st.title("📍 Where Do You Usually Listen?")

    st.session_state.user_profile["location"] = st.selectbox(
        "Select your main listening location:",
        ["At home", "On the go", "In the car", "While exercising"]
    )

    if st.button("✅ Save Profile & Start App"):
        with open(profile_file, "w") as f:
            json.dump(st.session_state.user_profile, f)
        st.success("🎉 Your profile has been saved! Starting the app...")
        next_page()

# Navigation buttons
if 0 < st.session_state.page_number < len(steps):
    col1, col2 = st.columns(2)
    with col1:
        st.button("⬅️ Back", on_click=prev_page)
    with col2:
        if st.session_state.page_number < len(steps) - 1:
            st.button("➡️ Next", on_click=next_page)

# AFTER Onboarding: Main App
if st.session_state.page_number >= len(steps):
    if os.path.exists(profile_file):
        with open(profile_file, "r") as f:
            user_profile = json.load(f)

        st.title("🎵 Intelligent Spotify Podcast Filter")

        st.markdown("""
        ### Your Personal Podcast Search
        Please fill out the brackets below to get your personal podcast suggestions, tailored to your personal preferences.
        """)

        topics = ["True Crime", "Science", "Comedy", "Sports", "Business", "Health", "Technology", "Society"]
        selected_topics = st.multiselect("🎙️ Choose Topics", topics)
        language_filter = st.multiselect("🌍 Choose Language(s)", ["German", "English"])
        country_code = st.selectbox("🌐 Search in which country?", ["CH", "DE", "AT", "US", "GB"], index=0)
        host_name = st.text_input("👤 Host name (optional)")
        guest_name = st.text_input("🧑‍🤝‍🧑 Guest name(s) (optional)")
        min_duration, max_duration = st.slider("⏱️ Episode Duration (Minutes)", 5, 180, (10, 60))

        if st.button("🔍 Start Search"):
            profile_text = " ".join(user_profile.get("interests", []) + user_profile.get("mood", []))
            profile_text += " " + user_profile.get("location", "")
            profile_text += f" Duration {user_profile.get('duration', [0, 0])[0]} to {user_profile.get('duration', [0, 0])[1]} minutes"
            profile_text += " " + " ".join(selected_topics)
            profile_text += " " + host_name + " " + guest_name

            query = " ".join(user_profile.get("interests", []) + selected_topics)

            if not query.strip():
                st.warning("⚠️ Please select at least one interest or topic!")
            else:
                with st.spinner("🔎 Searching..."):
                    results = sp.search(q=query, type="show", limit=20, market=country_code)

                    show_texts = []
                    show_info = []
                    average_duration = []
                    language_list = []

                    language_map = {
                        "German": "de",
                        "English": "en",
                    }

                    allowed_language_codes = [language_map[l] for l in language_filter if l in language_map]

                    for show in results["shows"]["items"]:
                        name = show["name"]
                        description = show["description"]
                        publisher = show["publisher"]
                        show_language = show.get("languages", [""])[0].lower()
                        show_id = show["id"]
                        link = show["external_urls"]["spotify"]
                        image_url = show["images"][0]["url"] if show.get("images") else ""

                        if allowed_language_codes and show_language not in allowed_language_codes:
                            continue

                        episodes = sp.show_episodes(show_id, limit=3)["items"]
                        episodes_text = " ".join([ep["description"] for ep in episodes if ep and "description" in ep])
                        episodes_duration = [int(ep["duration_ms"] / 60000) for ep in episodes if ep and "duration_ms" in ep]

                        if not any(min_duration <= d <= max_duration for d in episodes_duration):
                            continue

                        full_text = description + " " + episodes_text
                        show_texts.append(full_text)
                        show_info.append((name, publisher, description, link, image_url))
                        if episodes_duration:
                            average_duration.append((name, sum(episodes_duration) / len(episodes_duration)))
                        language_list.append(show_language)

                    if show_texts:
                        texts = show_texts + [profile_text]
                        tfidf = TfidfVectorizer(stop_words='english')
                        matrix = tfidf.fit_transform(texts)
                        similarities = cosine_similarity(matrix[-1], matrix[:-1])[0]

                        top_n = 15
                        top_indices = similarities.argsort()[-top_n:][::-1]

                        st.subheader("🎙️ Recommended Podcasts for You:")
                        for idx in top_indices:
                            name, publisher, description, link, image_url = show_info[idx]
                            st.image(image_url, width=200)
                            st.markdown(f"**🎧 {name}** – by *{publisher}*")
                            st.write(f"📝 {description[:250]}...")
                            st.markdown(f"[🔗 Go to show on Spotify]({link})")
                            st.markdown("---")

                        # 📈 Visualization of the Search Results
                        st.subheader("📊 Your Search Insights")
                        if average_duration:
                            names, durations = zip(*average_duration)
                            fig, ax = plt.subplots()
                            ax.barh(names, durations, color="skyblue")
                            ax.set_xlabel("Minutes")
                            ax.set_title("Average Episode Duration")
                            ax.invert_yaxis()
                            st.pyplot(fig)

                        if language_list:
                            lang_counts = pd.Series(language_list).value_counts()
                            fig2, ax2 = plt.subplots()
                            lang_counts.plot(kind="bar", color="lightgreen", ax=ax2)
                            ax2.set_ylabel("Count")
                            ax2.set_title("Languages of Recommended Shows")
                            ax2.set_yticks(range(1, lang_counts.max() + 1))
                            st.pyplot(fig2)
                    else:
                        st.warning("⚠️ No matching podcasts found. Please adjust your filters.")

