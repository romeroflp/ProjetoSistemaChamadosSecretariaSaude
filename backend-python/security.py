from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

import config
from crud.usuarios_crud import buscar_usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def criar_token(usuario_id: int) -> str:
    expira = datetime.now(timezone.utc) + timedelta(hours=config.TOKEN_EXPIRA_HORAS)
    return jwt.encode({"sub": str(usuario_id), "exp": expira}, config.SECRET_KEY, algorithm=config.ALGORITHM)


def usuario_atual(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """Lê o token e devolve o usuário logado (dict, como vem do buscar_usuario)."""
    invalido = HTTPException(
        status_code=401,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        dados = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        usuario = buscar_usuario(int(dados["sub"]))
    except (InvalidTokenError, KeyError, ValueError):
        raise invalido
    if usuario is None or usuario["status"] != "ativo":
        raise invalido
    return usuario


UsuarioLogado = Annotated[dict, Depends(usuario_atual)]


def eh_admin(usuario: dict) -> bool:
    return usuario["perfil"] == config.PERFIL_ADMIN


def eh_atendente(usuario: dict) -> bool:
    return usuario["perfil"] in config.PERFIS_ATENDENTES


def exigir_admin(usuario: UsuarioLogado) -> dict:
    if not eh_admin(usuario):
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return usuario


Admin = Annotated[dict, Depends(exigir_admin)]

def exigir_atendente(usuario: UsuarioLogado) -> dict:
    if not eh_atendente(usuario):
        raise HTTPException(403, "Apenas administradores e técnicos podem realizar essa operação.")
    return usuario

Atendente = Annotated[dict, Depends(exigir_atendente)]
