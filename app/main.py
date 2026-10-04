from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api import game_route, user_routes, vote_route
from app.core.chess_engine import start_game
from app.db.db_config import Base, engine, get_session
from app.scripts.process_votes import process_daily_votes

Base.metadata.create_all(engine)

# setup apscheduler
scheduler = AsyncIOScheduler()
trigger = CronTrigger(hour=16, minute=0)
scheduler.add_job(process_daily_votes, trigger)
scheduler.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up the CCVS API...")
    print("Starting game initialization...")

    db = get_session()
    start_game(db)
    yield

    scheduler.shutdown()
    print("Shutting down the CCVS API...")


app = FastAPI(title="CCVS", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key="my-super-secret-key",
    session_cookie="ccvs_session",
    max_age=3600,
    same_site="lax",
    https_only=False,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.get("/")
def health_check():
    return {"Success": "API is running"}


app.include_router(user_routes.router, prefix="/api/v1/users", tags=["users"])
app.include_router(game_route.router, prefix="/api/v1/game", tags=["game"])
app.include_router(vote_route.router, prefix="/api/v1/votes", tags=["votes"])
