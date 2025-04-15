from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Change from absolute to relative imports
from .routes import digits, emoji, health, speech

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(digits.router)
app.include_router(emoji.router)
app.include_router(speech.router, prefix="/speech")
