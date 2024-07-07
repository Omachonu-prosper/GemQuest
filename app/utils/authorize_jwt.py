import os
from dotenv import load_dotenv

from fastapi import Request, status
from fastapi.responses import JSONResponse


load_dotenv(override=True)

async def authorize_jwt(request: Request, call_next):
    if request.headers.get('X_API_Token') != os.getenv('X_API_Token'):
        return JSONResponse(content={'message': 'Unauthorized'}, status_code=status.HTTP_401_UNAUTHORIZED)
    response = await call_next(request)
    return response
