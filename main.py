from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_db():
    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS predictions (
                    user_id INTEGER,
                    country_order TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS admin_settings (
                    id INTEGER PRIMARY KEY,
                    editing_enabled INTEGER
                )""")
    c.execute("INSERT OR IGNORE INTO admin_settings (id, editing_enabled) VALUES (1, 1)")
    conn.commit()
    conn.close()

init_db()

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class PredictionRequest(BaseModel):
    username: str
    country_order: list

@app.post("/register")
def register(data: RegisterRequest):
    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (data.username, data.password))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="User already exists")
    finally:
        conn.close()
    return {"status": "registered"}

@app.post("/login")
def login(data: LoginRequest):
    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (data.username, data.password))
    user = c.fetchone()
    conn.close()
    if user:
        return {"status": "success"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/save_prediction")
def save_prediction(data: PredictionRequest):
    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (data.username,))
    user = c.fetchone()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    user_id = user[0]
    c.execute("REPLACE INTO predictions (user_id, country_order) VALUES (?, ?)", (user_id, ",".join(data.country_order)))
    conn.commit()
    conn.close()
    return {"status": "saved"}

@app.get("/can_edit")
def can_edit():
    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()
    c.execute("SELECT editing_enabled FROM admin_settings WHERE id=1")
    value = c.fetchone()[0]
    conn.close()
    return {"editing_enabled": bool(value)}

@app.post("/admin/toggle_editing")
def toggle_editing(status: bool):
    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()
    c.execute("UPDATE admin_settings SET editing_enabled=? WHERE id=1", (int(status),))
    conn.commit()
    conn.close()
    return {"status": "updated"}
