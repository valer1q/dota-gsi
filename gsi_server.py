#!/usr/bin/env python3
"""
Dota 2 GSI server (spectator mode) -> предметы всех игроков обеих команд.

Запуск:
    pip install flask
    python gsi_server.py                 # поднять сервер на 127.0.0.1:3000
    python gsi_server.py --make-config   # сгенерить .cfg в текущую папку

Как это работает:
  - Спектатишь матч в клиенте Доты с установленным конфигом (см. --make-config).
  - Клиент шлёт POST с JSON на http://127.0.0.1:3000/.
  - В режиме спектатора приходит блок allplayers/items по всем 10 игрокам.
    team2 = Radiant, team3 = Dire; player0..player4 = Radiant, player5..player9 = Dire.

ВАЖНО: Valve может молча менять ключи между патчами. Поэтому первый
полученный payload целиком сохраняется в raw_payload.json — открой и сверь
структуру, если что-то не парсится.
"""

import argparse
import json
import os
import sys
import threading
import time
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))

RAW_DUMP = "raw_payload.json"
_dumped = False

# Последнее распарсенное состояние, отдаётся через GET /state.
# Защищено локом, т.к. Flask может обрабатывать запросы в разных потоках.
_state_lock = threading.Lock()
_latest_state = {
    "ts": None,          # unix-время последнего апдейта
    "clock_time": None,  # игровое время из map.clock_time
    "spectating": False, # пришли ли спектатор-данные
    "players": [],       # список игроков с предметами
}

# Конфиг, который кладётся в game/dota/cfg/gamestate_integration/
CFG_CONTENT = '''"dota2-gsi Configuration"
{
    "uri"        "http://127.0.0.1:3000/"
    "timeout"    "5.0"
    "buffer"     "0.1"
    "throttle"   "0.1"
    "heartbeat"  "30.0"
    "data"
    {
        "provider"      "1"
        "map"           "1"
        "player"        "1"
        "hero"          "1"
        "abilities"     "1"
        "items"         "1"
        "allplayers"    "1"
    }
}
'''

# слоты основного инвентаря (то, что носит герой при себе)
MAIN_SLOTS = [f"slot{i}" for i in range(6)]
BACKPACK_SLOTS = [f"slot{i}" for i in range(6, 9)]


def collect_items(items_for_player: dict) -> dict:
    """Из блока items одного игрока вытаскивает непустые предметы по категориям."""
    if not isinstance(items_for_player, dict):
        return {}

    def names(keys):
        out = []
        for k in keys:
            entry = items_for_player.get(k)
            if isinstance(entry, dict):
                name = entry.get("name")
                if name and name != "empty":
                    charges = entry.get("charges")
                    out.append(f"{name}" + (f" (x{charges})" if charges else ""))
        return out

    neutral = []
    n = items_for_player.get("neutral0")
    if isinstance(n, dict) and n.get("name") not in (None, "empty"):
        neutral.append(n["name"])

    return {
        "inventory": names(MAIN_SLOTS),
        "backpack": names(BACKPACK_SLOTS),
        "neutral": neutral,
    }


def extract(gamestate: dict):
    """Возвращает список игроков (dict) или None если структура не спектаторская.

    Каждый игрок: {team, slot, player, hero, items: {inventory, backpack, neutral}}.
    """
    items = gamestate.get("items")
    hero = gamestate.get("hero")
    player = gamestate.get("player")

    # признак спектатор-структуры: items разложен по team2/team3
    if not isinstance(items, dict) or not any(t in items for t in ("team2", "team3")):
        return None

    rows = []
    for team_key in ("team2", "team3"):
        team_label = "Radiant" if team_key == "team2" else "Dire"
        team_items = items.get(team_key, {})
        team_heroes = hero.get(team_key, {}) if isinstance(hero, dict) else {}
        team_players = player.get(team_key, {}) if isinstance(player, dict) else {}

        for pkey in sorted(team_items.keys()):
            hero_name = ""
            h = team_heroes.get(pkey)
            if isinstance(h, dict):
                hero_name = h.get("name", "")
            pname = ""
            pl = team_players.get(pkey)
            if isinstance(pl, dict):
                pname = pl.get("name", "")

            rows.append({
                "team": team_label,
                "slot": pkey,
                "player": pname,
                "hero": hero_name,
                "items": collect_items(team_items[pkey]),
            })
    return rows


def render(rows):
    lines = []
    current_team = None
    for r in rows:
        if r["team"] != current_team:
            lines.append(f"\n=== {r['team']} ===")
            current_team = r["team"]
        it = r["items"]
        who = f"{r['slot']} {r['player'] or '?'} [{r['hero'] or '?'}]"
        inv = ", ".join(it["inventory"]) or "-"
        line = f"  {who}\n      inv: {inv}"
        if it["backpack"]:
            line += f"\n      bp:  {', '.join(it['backpack'])}"
        if it["neutral"]:
            line += f"\n      neu: {', '.join(it['neutral'])}"
        lines.append(line)
    return "\n".join(lines)


@app.route("/", methods=["POST"])
def gsi():
    global _dumped
    data = request.get_json(force=True, silent=True) or {}

    if not _dumped:
        with open(RAW_DUMP, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        _dumped = True
        print(f"[i] Первый payload сохранён в {RAW_DUMP} — сверь структуру при необходимости.")

    rows = extract(data)
    clock = (data.get("map") or {}).get("clock_time")

    with _state_lock:
        _latest_state["ts"] = time.time()
        _latest_state["clock_time"] = clock
        _latest_state["spectating"] = rows is not None
        _latest_state["players"] = rows or []

    if rows is None:
        print(f"[{clock}] Спектатор-данных нет (одиночный режим или матч ещё не начался).")
    else:
        os.system("clear" if os.name != "nt" else "cls")
        print(f"clock_time: {clock}")
        print(render(rows))

    return "", 200


@app.route("/", methods=["GET"])
def overlay():
    """Веб-оверлей: опрашивает /state и рисует предметы команд."""
    return send_from_directory(HERE, "overlay.html")


@app.route("/state", methods=["GET"])
def state():
    """Текущее состояние всех игроков в JSON. Источник для оверлея/аналитики."""
    with _state_lock:
        return jsonify(_latest_state)


def make_config():
    fname = "gamestate_integration_items.cfg"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(CFG_CONTENT)
    print(f"[i] Создан {fname}")
    print("    Скопируй его в:")
    print("    <Steam>/steamapps/common/dota 2 beta/game/dota/cfg/gamestate_integration/")
    print("    (папку gamestate_integration создай, если её нет), затем перезапусти Доту.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--make-config", action="store_true", help="сгенерировать .cfg и выйти")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=3000)
    args = ap.parse_args()

    if args.make_config:
        make_config()
        sys.exit(0)

    print(f"[i] Слушаю GSI на http://{args.host}:{args.port}/  (Ctrl+C для выхода)")
    app.run(host=args.host, port=args.port)
