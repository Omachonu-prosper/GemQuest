from fastapi import FastAPI
from app.middleware.authorize_jwt import authorize_jwt
from functools import partial
from app.routes import endpoint
from app.routes import rooms
from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.waitroom_expiry import close_expired_waitrooms

# Initialize app
app = FastAPI()
scheduler = BackgroundScheduler()
scheduler.add_job(close_expired_waitrooms, 'interval', minutes=10)
scheduler.start()


# App Middlewares
authorize_jwt_middleware: partial= partial(authorize_jwt)
app.middleware('http')(authorize_jwt_middleware)

# App Router
app.include_router(endpoint.router)
app.include_router(rooms.router)