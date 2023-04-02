from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/lib", StaticFiles(directory="www/lib"))
app.mount("/videos", StaticFiles(directory="www/vid"))
app.mount("/", StaticFiles(directory="www", html=True))
