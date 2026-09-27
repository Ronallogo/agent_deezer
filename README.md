# agent_deezer

Agent de recherche musicale (Deezer) construit avec Deep Agents + Groq.

## Tools Deezer (API publique, sans clé)
- `search_song` — cherche un titre
- `search_artist` — cherche un artiste
- `top_titres_artist` — top 10 titres d'un artiste

## Lancer
```bash
/home/ron-allogo/agent-env/bin/python deezer_agent/agent.py
```

## Variables d'environnement
Copier et remplir (ne jamais commiter le vrai `.env`) :
```
GROQ_API_KEY=...
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=deezer_agent
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
```

## Studio
```bash
/home/ron-allogo/agent-env/bin/langgraph dev
```
