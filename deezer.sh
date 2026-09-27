#!/usr/bin/env bash
# Usage rapide :
#   ./projet.sh start    -> lance langgraph dev en arrière-plan
#   ./projet.sh stop     -> arrête langgraph dev
#   ./projet.sh restart  -> relance
#   ./projet.sh status   -> état + URL
#   ./projet.sh logs     -> suit les logs
#   ./projet.sh chat     -> discute en CLI sans Studio
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_BIN="/home/ron-allogo/agent-env/bin"
PORT="2024"
HOST="127.0.0.1"
PIDFILE="$PROJECT_DIR/.langgraph.pid"
LOGFILE="$PROJECT_DIR/.langgraph.log"

find_pids() {
  # PID via pidfile + pgrep fallback (évite de tuer d'autres projets)
  if [ -f "$PIDFILE" ]; then
    cat "$PIDFILE" 2>/dev/null || true
  fi
  pgrep -f "langgraph dev" || true
}

is_running() {
  [ -n "$(find_pids | head -n 1)" ]
}

start() {
  if is_running; then
    echo "✅ Déjà lancé (PID: $(find_pids | tr '\n' ' ')). Studio: https://smith.langchain.com/studio/?baseUrl=http://$HOST:$PORT"
    exit 0
  fi
  if [ ! -x "$VENV_BIN/langgraph" ]; then
    echo "❌ Venv introuvable: $VENV_BIN/langgraph"
    exit 1
  fi
  if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "⚠️  Pas de .env trouvé dans $PROJECT_DIR"
  fi
  echo "🚀 Lancement: langgraph dev --port $PORT ..."
  cd "$PROJECT_DIR"
  # shellcheck disable=SC2086
  nohup "$VENV_BIN/langgraph" dev --port "$PORT" --host "$HOST" --no-browser > "$LOGFILE" 2>&1 &
  echo $! > "$PIDFILE"
  sleep 3
  if is_running; then
    echo "✅ Lancé !"
    echo "   API locale : http://$HOST:$PORT"
    echo "   Docs       : http://$HOST:$PORT/docs"
    echo "   Studio     : https://smith.langchain.com/studio/?baseUrl=http://$HOST:$PORT"
    echo "   Logs       : tail -f $LOGFILE"
  else
    echo "❌ Échec au démarrage. Voir logs :"
    tail -n 30 "$LOGFILE" || true
    exit 1
  fi
}

stop() {
  PIDS="$(find_pids)"
  if [ -z "$PIDS" ]; then
    echo "⏹️  Rien à arrêter (pas de 'langgraph dev' en cours)."
    rm -f "$PIDFILE"
    exit 0
  fi
  echo "🛑 Arrêt des PID: $PIDS ..."
  # shellcheck disable=SC2086
  kill $PIDS 2>/dev/null || true
  sleep 2
  # force si encore là
  RESTE="$(find_pids)"
  if [ -n "$RESTE" ]; then
    echo "⚠️  Forçage (kill -9): $RESTE"
    # shellcheck disable=SC2086
    kill -9 $RESTE 2>/dev/null || true
  fi
  rm -f "$PIDFILE"
  echo "✅ Arrêté."
}

status() {
  PIDS="$(find_pids)"
  if [ -n "$PIDS" ]; then
    echo "✅ EN COURS (PID: $(echo "$PIDS" | tr '\n' ' '))"
    echo "   API locale : http://$HOST:$PORT"
    echo "   Docs       : http://$HOST:$PORT/docs"
    echo "   Studio     : https://smith.langchain.com/studio/?baseUrl=http://$HOST:$PORT"
    # test HTTP rapide (ne fait pas échouer le script si down)
    if command -v curl >/dev/null 2>&1; then
      curl -s -o /dev/null -w "   HTTP /docs : %{http_code}\n" "http://$HOST:$PORT/docs" || true
    fi
  else
    echo "⏹️  ARRÊTÉ. Lance avec: ./projet.sh start"
  fi
}

logs() {
  touch "$LOGFILE"
  tail -f "$LOGFILE"
}

chat() {
  # Discussion CLI directe, sans passer par Studio
  "$VENV_BIN/python" "$PROJECT_DIR/deezer_agent/agent.py"
}

case "${1:-help}" in
  start) start ;;
  stop) stop ;;
  restart) stop; sleep 1; start ;;
  status) status ;;
  logs) logs ;;
  chat) chat ;;
  help|*) echo "Usage: ./projet.sh {start|stop|restart|status|logs|chat}" ;;
esac
