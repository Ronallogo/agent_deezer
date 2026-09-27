from dotenv import load_dotenv

load_dotenv()

import os

import requests
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool


@tool
def search_song(query: str) -> str:
    """Cherche un titre/musique sur Deezer. Ex: 'Daft Punk Get Lucky'. Retourne max 3 résultats compacts."""
    r = requests.get("https://api.deezer.com/search", params={"q": query}, timeout=10)
    r.raise_for_status()
    data = r.json().get("data", [])[:3]
    if not data:
        return f"Aucun titre trouvé pour '{query}'."
    lines = []
    for i, t in enumerate(data, 1):
        lines.append(f"{i}. {t['title']} - {t['artist']['name']} [{t['album']['title']}] (id={t['id']})")
    return "\n".join(lines)


@tool
def search_artist(nom: str) -> str:
    """Cherche un artiste sur Deezer. Ex: 'Daft Punk'. Retourne max 3 résultats compacts."""
    r = requests.get("https://api.deezer.com/search/artist", params={"q": nom}, timeout=10)
    r.raise_for_status()
    data = r.json().get("data", [])[:3]
    if not data:
        return f"Artiste '{nom}' introuvable."
    lines = []
    for i, a in enumerate(data, 1):
        lines.append(f"{i}. {a['name']} (id={a['id']}, {a['nb_fan']} fans, {a['nb_album']} albums)")
    return "\n".join(lines)


@tool
def top_titres_artist(nom_ou_id: str) -> str:
    """Donne le top 5 titres d'un artiste Deezer. Input: nom ('Daft Punk') ou id ('27')."""
    artist_id = nom_ou_id
    if not str(nom_ou_id).isdigit():
        s = requests.get(
            "https://api.deezer.com/search/artist", params={"q": nom_ou_id}, timeout=10
        ).json()
        if not s.get("data"):
            return f"Artiste '{nom_ou_id}' introuvable."
        artist_id = s["data"][0]["id"]
    r = requests.get(f"https://api.deezer.com/artist/{artist_id}/top", params={"limit": 5}, timeout=10)
    r.raise_for_status()
    data = r.json().get("data", [])[:5]
    if not data:
        return f"Aucun top titre trouvé pour '{nom_ou_id}'."
    lines = []
    for i, t in enumerate(data, 1):
        lines.append(f"{i}. {t['title']} - {t['album']['title']}")
    return "\n".join(lines)


# max_tokens + temperature bas = moins de TPM (erreur 413).
# gpt-oss-20b : même famille que 120b mais quota TPM bien plus élevé (anti-413).
# Surcharge possible : GROQ_MODEL=qwen/qwen3.8-27b
model = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
    temperature=0,
    max_tokens=1000,
)

agent = create_react_agent(model, tools=[search_song, search_artist, top_titres_artist])
