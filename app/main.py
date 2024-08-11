from fastapi import FastAPI
from app.utils.authorize_jwt import authorize_jwt
from functools import partial
from app.routes import endpoint
from app.routes import rooms
# from apscheduler.schedulers.background import BackgroundScheduler
# from app.utils.waitroom_expiry import close_expired_waitrooms
from fastapi.middleware.cors import CORSMiddleware

# Initialize app
app = FastAPI()
# scheduler = BackgroundScheduler()
# scheduler.add_job(close_expired_waitrooms, 'interval', minutes=10)
# scheduler.start()


# App Middlewares
authorize_jwt_middleware: partial= partial(authorize_jwt)
app.middleware('http')(authorize_jwt_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# App Router
app.include_router(endpoint.router)
app.include_router(rooms.router)