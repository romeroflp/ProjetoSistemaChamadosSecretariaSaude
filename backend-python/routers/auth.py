from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from crud.usuarios_crud import alterar_senha_usuario, autenticar_usuario, buscar_permissoes_usuario
from schemas import AlterarSenha, MeOut, Token
from security import UsuarioLogado, criar_token

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/token", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    usuario_id = autenticar_usuario(form.username, form.password)
    if usuario_id is None:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
    return Token(access_token=criar_token(usuario_id), token_type="bearer")


@router.get("/me", response_model=MeOut)
def me(usuario: UsuarioLogado):
    """Dados do usuário logado e os menus do perfil (para o front montar a tela)."""
    permissoes = buscar_permissoes_usuario(usuario["id"])
    return MeOut(**usuario, menus=permissoes["menus"], submenus=permissoes["submenus"])


@router.post("/alterar-senha")
def trocar_senha(dados: AlterarSenha, usuario: UsuarioLogado):
    ok, mensagem = alterar_senha_usuario(usuario["id"], dados.senha_atual, dados.nova_senha)
    if not ok:
        raise HTTPException(status_code=400, detail=mensagem)
    return {"mensagem": mensagem}
