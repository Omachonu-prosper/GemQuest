from fastapi import FastAPI

from app.middleware.authorize_jwt import authorize_jwt
from functools import partial
from app.routes import endpoint
from app.routes import rooms

# Initialize app
app = FastAPI()

# App Middlewares
authorize_jwt_middleware: partial= partial(authorize_jwt)
app.middleware('http')(authorize_jwt_middleware)

# App Router
app.include_router(endpoint.router)
app.include_router(rooms.router)
