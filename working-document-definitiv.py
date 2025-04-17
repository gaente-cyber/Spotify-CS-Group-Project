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

# Spotify Authentifizierung
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="",
    client_secret="",
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-library-read"
))

# Sprachcode-Vereinheitlichung
@st.cache_data
def map_sprache(code):
    code = code.lower()
    if code.startswith("de"):
        return "Deutsch"
    elif code.startswith("en"):
        return "Englisch"
    elif code.startswith("fr"):
        return "Französisch"
    elif code.startswith("es"):
        return "Spanisch"
    elif code.startswith("it"):
        return "Italienisch"
    else:
        return "Andere"

profil_datei = "user_profile.json"
if os.path.exists(profil_datei):
    with open(profil_datei, "r") as f:
        user_profile = json.load(f)
        first_time = False
else:
    user_profile = {}
    first_time = True

if first_time:
    st.title("👋 Willkommen bei deiner Podcast-App!")
    st.markdown("Lass uns zuerst ein paar Dinge über deine Interessen herausfinden, um dir später bessere Empfehlungen geben zu können.")

    interessen = ["True Crime", "Wissenschaft", "Comedy", "Sport", "Business", "Technologie", "Gesellschaft", "Gesundheit", "Kunst", "Musik", "Spiritualität"]
    ausgewaehlt = st.multiselect("Was interessiert dich besonders?", interessen)

    sprachen = ["Deutsch", "Englisch", "Französisch", "Spanisch", "Italienisch"]
    sprache = st.multiselect("Welche Sprachen bevorzugst du?", sprachen)

    dauer = st.slider("Wie lange sollte eine ideale Folge für dich dauern? (Minuten)", 5, 120, (20, 60))

    stimmung = st.multiselect("Welche Stimmung soll ein Podcast erzeugen?", ["Entspannung", "Lernen", "Lachen", "Inspiration", "Konzentration", "Ablenkung"])

    ort = st.selectbox("Wo hörst du Podcasts am häufigsten?", ["Zuhause", "Unterwegs", "Im Auto", "Beim Sport"])

    if st.button("✅ Profil speichern & starten"):
        user_profile = {
            "interessen": ausgewaehlt,
            "sprache": sprache,
            "dauer": dauer,
            "stimmung": stimmung,
            "ort": ort
        }
        with open(profil_datei, "w") as f:
            json.dump(user_profile, f)
        st.success("🎉 Dein Profil wurde gespeichert! Starte die App jetzt neu.")
        st.stop()

if not first_time:
    st.title("🎵 Intelligenter Spotify Podcast-Filter")

    st.markdown("""
    ### ❗ Problemstellung
    Nutzer:innen verbringen viel Zeit damit, passende Podcast-Episoden auf Spotify zu finden. Die Plattform bietet kaum präzise Filter oder personalisierte Empfehlungen auf Episodenebene. Unsere App behebt dieses Problem durch ein intelligentes Filtersystem mit personalisiertem Matching.

    **🎯 Lösung:**
    Die App kombiniert deine angegebenen Interessen mit intelligenten Filteroptionen (z. B. Dauer, Sprache, Host) und Machine Learning zur Empfehlung von Podcasts – für einen perfekten Podcast-Consumer Fit.
    """)

    themen = ["True Crime", "Wissenschaft", "Comedy", "Sport", "Business", "Gesundheit", "Technologie", "Gesellschaft"]
    ausgewaehlte_themen = st.multiselect("🎙️ Themen / Genres", themen)
    sprachen_filter = st.multiselect("🌍 Sprache(n)", ["Deutsch", "Englisch", "Französisch", "Spanisch", "Italienisch"])
    land_code = st.selectbox("🌐 In welchem Land möchtest du suchen?", ["CH", "DE", "AT", "US", "GB", "FR", "IT", "ES"], index=0)
    bewertung = st.slider("⭐ Mindestbewertung (0 = unbekannt, 100 = super beliebt)", 0, 100, 50)
    host_name = st.text_input("👤 Name des Podcast-Hosts (optional)")
    gaeste = st.text_input("🧑‍🤝‍🧑 Name(n) von Gästen (optional)")
    min_dauer, max_dauer = st.slider("⏱️ Episodendauer (in Minuten)", 5, 180, (10, 60))

    if st.button("🔍 Suche starten"):
        with st.spinner("Lade passende Podcasts..."):
            profil_text = " ".join(user_profile["interessen"] + user_profile["stimmung"])
            profil_text += " " + user_profile["ort"]
            profil_text += f" Dauer {user_profile['dauer'][0]} bis {user_profile['dauer'][1]} Minuten"
            profil_text += " " + " ".join(ausgewaehlte_themen)
            profil_text += " " + host_name + " " + gaeste

            query = " ".join(user_profile["interessen"] + ausgewaehlte_themen)
            results = sp.search(q=query, type="show", limit=20, market=land_code)

            show_texts = []
            show_info = []
            dauer_durchschnitt = []
            sprachen_liste = []

            for show in results["shows"]["items"]:
                name = show["name"]
                beschreibung = show["description"]
                publisher = show["publisher"]
                sprache_show = show.get("languages", [""])[0]
                show_id = show["id"]
                link = show["external_urls"]["spotify"]
                image_url = show["images"][0]["url"] if show.get("images") else ""

                if not any(map_sprache(sprache_show) == s for s in sprachen_filter):
                    continue

                episoden = sp.show_episodes(show_id, limit=3)["items"]
                episoden_text = " ".join([ep["description"] for ep in episoden if ep and "description" in ep])
                episodendauer = [int(ep["duration_ms"] / 60000) for ep in episoden if ep and "duration_ms" in ep]

                if not any(min_dauer <= d <= max_dauer for d in episodendauer):
                    continue

                full_text = beschreibung + " " + episoden_text
                show_texts.append(full_text)
                show_info.append((name, publisher, beschreibung, link, image_url))
                if episodendauer:
                    dauer_durchschnitt.append((name, sum(episodendauer) / len(episodendauer)))
                sprachen_liste.append(map_sprache(sprache_show))

            if show_texts:
                texte = show_texts + [profil_text]
                tfidf = TfidfVectorizer(stop_words='english')
                matrix = tfidf.fit_transform(texte)
                similarities = cosine_similarity(matrix[-1], matrix[:-1])[0]

                top_n = 5
                top_indices = similarities.argsort()[-top_n:][::-1]

                st.subheader("🎙️ Für dich empfohlene Podcasts:")
                for idx in top_indices:
                    name, publisher, beschreibung, link, image_url = show_info[idx]
                    st.image(image_url, width=200)
                    st.markdown(f"**🎧 {name}** – von *{publisher}*")
                    st.write(f"📝 {beschreibung[:250]}...")
                    st.markdown(f"[🔗 Zur Show auf Spotify]({link})")
                    st.markdown("---")

                if dauer_durchschnitt:
                    namen_dauer, werte_dauer = zip(*dauer_durchschnitt)
                    st.subheader("⏱️ Durchschnittliche Episodendauer")
                    fig1, ax1 = plt.subplots()
                    ax1.barh(namen_dauer, werte_dauer, color="lightgreen")
                    ax1.set_xlabel("Minuten")
                    ax1.set_title("Durchschnittliche Episodendauer")
                    ax1.invert_yaxis()
                    st.pyplot(fig1)

                if ausgewaehlte_themen:
                    thema_counts = {t: ausgewaehlte_themen.count(t) for t in set(ausgewaehlte_themen)}
                    st.subheader("📚 Gewählte Themen")
                    fig2, ax2 = plt.subplots()
                    ax2.bar(thema_counts.keys(), thema_counts.values(), color="lightblue")
                    ax2.set_ylabel("Anzahl")
                    ax2.set_title("Verteilung deiner gewählten Themen")
                    st.pyplot(fig2)

                if sprachen_liste:
                    sprachen_counts = pd.Series(sprachen_liste).value_counts()
                    st.subheader("🌐 Sprachen der empfohlenen Podcasts")
                    fig3, ax3 = plt.subplots()
                    sprachen_counts.plot(kind="bar", color="lightcoral", ax=ax3)
                    ax3.set_ylabel("Anzahl")
                    ax3.set_title("Sprachverteilung")
                    st.pyplot(fig3)
            else:
                st.warning("⚠️ Es konnten keine passenden Podcasts gefunden werden. Bitte ändere deine Filter.")