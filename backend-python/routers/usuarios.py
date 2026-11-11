from fastapi import APIRouter, HTTPException

from crud.usuarios_crud import (
    atualizar_usuario,
    buscar_nome_perfil,
    buscar_usuario,
    buscar_usuario_por_login,
    criar_usuario,
    deletar_usuario,
    listar_perfis_ativos,
    listar_usuarios,
    listar_usuarios_ativos,
)
from schemas import PerfilOut, UsuarioAtualizar, UsuarioCriar, UsuarioOut
from security import Admin, UsuarioLogado, eh_admin

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


def _carregar(usuario_id: int) -> dict:
    usuario = buscar_usuario(usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return usuario


@router.post("", response_model=UsuarioOut, status_code=201)
def criar(dados: UsuarioCriar, _: Admin):
    if buscar_usuario_por_login(dados.usuario):
        raise HTTPException(status_code=409, detail="Nome de usuário já está em uso.")
    if buscar_nome_perfil(dados.tipo) is None:
        raise HTTPException(status_code=422, detail="Perfil (tipo) inexistente.")
    novo_id = criar_usuario(dados.model_dump())
    if novo_id is None:
        raise HTTPException(status_code=500, detail="Erro ao criar usuário.")
    return buscar_usuario(novo_id)


@router.get("", response_model=list[UsuarioOut])
def listar(_: Admin, apenas_ativos: bool = False):
    return listar_usuarios_ativos() if apenas_ativos else listar_usuarios()


@router.get("/perfis", response_model=list[PerfilOut])  # fica antes de /{usuario_id}
def listar_perfis(_: Admin):
    return listar_perfis_ativos()


@router.get("/{usuario_id}", response_model=UsuarioOut)
def buscar(usuario_id: int, logado: UsuarioLogado):
    if usuario_id != logado["id"] and not eh_admin(logado):
        raise HTTPException(status_code=403, detail="Sem permissão.")
    return _carregar(usuario_id)


@router.patch("/{usuario_id}", response_model=UsuarioOut)
def atualizar(usuario_id: int, dados: UsuarioAtualizar, _: Admin):
    usuario = _carregar(usuario_id)
    campos = dados.model_dump(exclude_unset=True, exclude_none=True)
    if not campos:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar.")
    if "usuario" in campos and campos["usuario"] != usuario["usuario"] and buscar_usuario_por_login(campos["usuario"]):
        raise HTTPException(status_code=409, detail="Nome de usuário já está em uso.")
    if "tipo" in campos and buscar_nome_perfil(campos["tipo"]) is None:
        raise HTTPException(status_code=422, detail="Perfil (tipo) inexistente.")
    if atualizar_usuario(usuario_id, campos) == 0:
        raise HTTPException(status_code=400, detail="Não foi possível atualizar o usuário.")
    return buscar_usuario(usuario_id)


@router.delete("/{usuario_id}", status_code=204)
def deletar(usuario_id: int, admin: Admin):
    _carregar(usuario_id)
    if usuario_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Você não pode excluir a própria conta.")
    if deletar_usuario(usuario_id) == 0:
        raise HTTPException(
            status_code=409,
            detail="Usuário possui chamados ou respostas. Altere o status para 'inativo' em vez de excluir.",
        )
