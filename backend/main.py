from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import trading

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trading.router)

@app.get("/")
def read_root():
    return {"status": "Trading Bot Backend Running"}
