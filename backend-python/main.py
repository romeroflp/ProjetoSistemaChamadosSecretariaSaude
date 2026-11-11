from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from database.schema import criar_tabelas, semear
from routers import auth, chamados, respostas, usuarios


@asynccontextmanager
async def lifespan(app: FastAPI):
    criar_tabelas()  # cria as tabelas que ainda não existem
    semear()         # perfis padrão e primeiro administrador
    yield


app = FastAPI(title="API de Chamados", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ORIGENS,
    allow_methods=["*"],
    allow_headers=["*"],  # inclui Authorization e ngrok-skip-browser-warning
)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(chamados.router)
app.include_router(respostas.router)


@app.get("/health", tags=["Saúde"])
def health():
    return {"status": "ok"}
