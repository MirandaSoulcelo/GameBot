from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3

app = FastAPI()

def get_db():
    conn = sqlite3.connect("saves.db")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS saves (
        user_id TEXT,
        game    TEXT,
        type    TEXT,
        data    TEXT,
        PRIMARY KEY (user_id, game, type)
    )
                 """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS game_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        game TEXT,
        opened_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        feedback_asked INTEGER DEFAULT 0
    )
                 """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS game_feedback (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id TEXT,
                 game TEXT,
                 message TEXT,
                 sentiment TEXT,
                 confidence REAL,
                 created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
                 """)
    conn.commit()
    return conn

@app.middleware("http")
async def add_ngrok_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

app.mount("/roms",      StaticFiles(directory="roms"),      name="roms")
app.mount("/emulator",  StaticFiles(directory="emulator"),  name="emulator")

templates = Jinja2Templates(directory="templates")

games = {
    "pokemon-emerald": {
        "core": "mgba",
        "rom":  "/roms/gba/Pokemon-Emerald.gba"
    },
    "kingdom-hearts": {
        "core": "mgba",
        "rom":  "/roms/gba/Kingdom-Hearts.gba"
    },
    "street-fighter": {
        "core": "mgba",
        "rom":  "/roms/gba/Street-Fighter.gba"
    },
    "heartgold": {
        "core": "melonds",
        "rom":  "/roms/ds/Pokemon-HeartGold.nds"
    },
    "Mega-Man": {
        "core": "mgba",
        "rom":  "/roms/gba/MegaMan-Zero.gba"
    },
     "Kirby": {
        "core": "mgba",
        "rom":  "/roms/gba/Kirby - Nightmare in Dream Land.gba"
    },
    "Sonic": {
        "core": "mgba",
        "rom":  "/roms/gba/Sonic-Advance.gba"
    },
    "super-mario": {
        "core": "mgba",
        "rom":  "/roms/gba/Super Mario - Advance2.gba"
    },
    "The-Legend-Of-Zelda": {
    "core": "mgba",
    "rom":  "/roms/gba/Legend of Zelda-TheMinishCap.gba"
},
    
}

@app.get("/play/{game}", response_class=HTMLResponse)
async def play_game(request: Request, game: str, uid: str = "anonymous"):
    selected_game = games.get(game)
    if not selected_game:
        return HTMLResponse("Jogo não encontrado", status_code=404)
    
    db = get_db()

    db.execute(
        """
        INSERT INTO game_sessions (user_id, game)
        VALUES (?, ?)
        """,
        (uid, game)
    )

    db.commit()
    db.close()

    return templates.TemplateResponse(request, "player.html", {
        "core":    selected_game["core"],
        "rom":     selected_game["rom"],
        "user_id": uid,
        "game":    game
    })

@app.post("/save/{game}")
async def save_game(game: str, request: Request):
    body    = await request.json()
    user_id = body.get("user_id", "anonymous")
    type_   = body.get("type", "srm")
    data    = body.get("data")

    if not data:
        return {"ok": False, "error": "no data"}

    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO saves (user_id, game, type, data) VALUES (?, ?, ?, ?)",
        (user_id, game, type_, data)
    )
    db.commit()
    db.close()
    return {"ok": True}

@app.get("/load/{game}")
async def load_game(game: str, uid: str = "anonymous"):
    db   = get_db()
    rows = db.execute(
        "SELECT type, data FROM saves WHERE user_id=? AND game=?",
        (uid, game)
    ).fetchall()
    db.close()

    result = {"srm": None, "state": None}
    for row in rows:
        result[row[0]] = row[1]

    return result