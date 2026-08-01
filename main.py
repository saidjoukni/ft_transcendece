from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 1. GET عادي
@app.get("/")
def hello():
    return {"Hello": "World"}

# 2. Path Parameter
@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id, "message": "هادا هو اللعاب لي طلبتي"}

# 3. POST & Request Body
class Player(BaseModel):
    username: str
    level: int

@app.post("/players/")
def create_player(player: Player):
    return {
        "message": "تم تسجيل اللعاب بنجاح",
        "username": player.username,
        "level": player.level
    }