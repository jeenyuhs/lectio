from datetime import timedelta
from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm
import auth
from lectio.user import User
import cache

app = FastAPI()


@app.on_event("shutdown")
async def shutdown():
    for u in cache.lectio_users:
        await cache.lectio_users[u].close()


@app.get("/")
async def read_root():
    return {"Hello": "Worldasasa"}


@app.post("/token", response_model=auth.Token)
async def authenticate(data: OAuth2PasswordRequestForm = Depends()):
    user = await auth.authenticate(data.username, data.password)

    if not user:
        raise auth.CREDENTIAL_ERROR

    expiration = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRATION)
    access_token = auth.create_access_token(user, expiration)

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me")
async def get_user(u: User = Depends(auth.get_user)):
    return u


@app.get("/schedule")
async def get_schedule(u: User = Depends(auth.get_user), day: str = ""):
    schedule = await u.schedule()

    if day:
        return schedule.get(day)

    return schedule


@app.get("/messages")
async def get_messages(u: User = Depends(auth.get_user)):
    return await u.messages()


@app.get("/absence")
async def get_absence(u: User = Depends(auth.get_user)):
    return await u.absence()
