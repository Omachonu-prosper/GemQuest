from fastapi import FastAPI

from app.routes import endpoint
from app.middleware.authorize_jwt import authorize_jwt
from functools import partial

app = FastAPI()

app.include_router(endpoint.router)
authorize_jwt_middleware: partial= partial(authorize_jwt)
app.middleware('http')(authorize_jwt_middleware)