import json
import os
import psycopg2
from fastapi import FastAPI
import redis
import requests


app = FastAPI(title="backend")


PG_HOST = os.environ["PG_HOST"]
PG_PORT = int(os.environ["PG_PORT"])
PG_DATABASE = os.environ["PG_DATABASE"]
PG_USER = os.environ["PG_USER"]
PG_PASSWORD = os.environ["PG_PASSWORD"]
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ["REDIS_PORT"])
AI_URL = os.environ["AI_URL"]


cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

def get_db_connection():
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )
    return conn 


@app.get("/")
def read_root():
    return {"message": "Hello from the backend!"}

@app.get("/health")
def read_health():
    return {"status": "healthy"}


@app.get("/data")
def read_data():
    cached = cache.get("users")
    if cached:
        return {"users": json.loads(cached.decode("utf-8")), "source": "cache"}

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users ORDER BY id;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    users = [{"id": r[0], "username": r[1], "email": r[2]} for r in rows]
    cache.set("users", json.dumps(users), ex=60)
    return {"users": users, "source": "database"}


@app.get("/posts")
def read_posts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT p.id, p.title, p.content, u.username "
        "FROM posts p JOIN users u ON u.id = p.user_id ORDER BY p.id;"
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {
        "posts": [
            {"id": r[0], "title": r[1], "content": r[2], "author": r[3]}
            for r in rows
        ]
    }


@app.get("/ai")
def call_ai():
    response = requests.get(f"{AI_URL}/predict")
    if response.status_code == 200:
        return {"ai_response": response.json()}
    else:
        return {"error": "Failed to call AI service", "status_code": response.status_code}