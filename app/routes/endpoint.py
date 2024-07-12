from fastapi import APIRouter

router = APIRouter()

@router.get('/route')
async def protected():
    return {'message': 'protected route'}