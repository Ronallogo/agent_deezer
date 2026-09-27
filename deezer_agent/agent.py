"""Deezer agent — built from deepagents-python-quickstart shape.

Quickstart source: https://docs.langchain.com/oss/python/deepagents/quickstart
Adaptation: provider = Groq (GROQ_API_KEY in .env), tools = Deezer public API.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# LangSmith tracing config (traces -> projet deezer_agent)
os.environ.setdefault("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
os.environ.setdefault("LANGSMITH_PROJECT", "deezer_agent")
os.environ.setdefault("LANGSMITH_TRACING", "true")

import requests
from deepagents import create_deep_agent
from langchain_groq import ChatGroq

# --- Tools Deezer (API publique, sans clé) ---
# Format compact volontaire : limite TPM Groq (erreur 413). Jamais de list/dict.


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


def top_titres_artist(nom_ou_id: str) -> str:
    """Top 5 titres d'un artiste Deezer. Input: nom ('Daft Punk') ou id ('27')."""
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


# System prompt facon quickstart "research agent", adapte musique
# Consigne anti-413 : 1 seul appel par outil, réponses courtes.
deezer_instructions = """You are an expert music researcher. Your job is to conduct thorough research on artists and songs using Deezer, then write a polished report.

You have access to Deezer search tools as your primary means of gathering information.

## `search_song`
Use this to run a song search for a given query.

## `search_artist`
Use this to run an artist search for a given name.

## `top_titres_artist`
Use this to get the top tracks of an artist (name or id).

Rules to save tokens: call each tool at most once per question, ask for top 3-5 max, keep the final report under 800 tokens.
"""

# max_tokens bas + temperature 0 = moins de TPM (erreur 413).
# gpt-oss-20b : même famille que 120b mais quota TPM bien plus élevé (anti-413).
# Surcharge possible : GROQ_MODEL=qwen/qwen3.8-27b
model = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
    temperature=0,
    max_tokens=1000,
)

# Objet expose pour langgraph.json / Studio
agent = create_deep_agent(
    model=model,
    tools=[search_song, search_artist, top_titres_artist],
    system_prompt=deezer_instructions,
)


conversation: list = []
MAX_HISTORY = 10  # fenêtre glissante anti-413 : on n'envoie que les 10 derniers messages


def send_message(text: str) -> str:
    """Envoie un message à l'agent et retourne sa réponse. Garde l'historique."""
    conversation.append({"role": "user", "content": text})
    history = conversation[-MAX_HISTORY:]
    result = agent.invoke({"messages": history}, config={"recursion_limit": 12})
    reply = result["messages"][-1].content
    # Groq refuse content vide : garde-fou
    if not isinstance(reply, str) or not reply.strip():
        reply = "Réponse vide du modèle, reformule ta question plus simplement."
    conversation.append({"role": "assistant", "content": reply})
    # borne mémoire locale aussi
    del conversation[:-MAX_HISTORY]
    return reply


if __name__ == "__main__":
    print("deezer_agent — discute (tape 'quit' pour sortir)")
    while True:
        try:
            text = input("toi> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text.lower() in ("quit", "exit", "q"):
            break
        if not text:
            continue
        print("agent>", send_message(text))
