from fastapi import APIRouter, HTTPException

from crud.chamados_crud import (
    alterar_status_chamado,
    atualizar_chamado,
    buscar_chamado,
    cancelar_chamado,
    criar_chamado,
    listar_chamados,
)
from schemas import ChamadoAtualizar, ChamadoCriar, ChamadoOut, StatusChamado, StatusIn
from security import UsuarioLogado, eh_atendente

router = APIRouter(prefix="/chamados", tags=["Chamados"])


def carregar_chamado(chamado_id: int, usuario: dict) -> dict:
    """Atendentes acessam qualquer chamado; os demais, só os próprios.
    Quem não pode ver recebe 404 (não revela que o chamado existe)."""
    chamado = buscar_chamado(chamado_id)
    if chamado is None or not (eh_atendente(usuario) or chamado["solicitante_id"] == usuario["id"]):
        raise HTTPException(status_code=404, detail="Chamado não encontrado.")
    return chamado


@router.post("", response_model=ChamadoOut, status_code=201)
def criar(dados: ChamadoCriar, usuario: UsuarioLogado):
    novo_id = criar_chamado({"solicitante_id": usuario["id"], **dados.model_dump()})
    if novo_id is None:
        raise HTTPException(status_code=500, detail="Erro ao cadastrar chamado.")
    return buscar_chamado(novo_id)


@router.get("", response_model=list[ChamadoOut])
def listar(usuario: UsuarioLogado, status: StatusChamado | None = None):
    dono = None if eh_atendente(usuario) else usuario["id"]
    return listar_chamados(solicitante_id=dono, status=status)


@router.get("/{chamado_id}", response_model=ChamadoOut)
def buscar(chamado_id: int, usuario: UsuarioLogado):
    return carregar_chamado(chamado_id, usuario)


@router.patch("/{chamado_id}", response_model=ChamadoOut)
def atualizar(chamado_id: int, dados: ChamadoAtualizar, usuario: UsuarioLogado):
    carregar_chamado(chamado_id, usuario)
    campos = dados.model_dump(exclude_unset=True, exclude_none=True)
    if not campos:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar.")
    if atualizar_chamado(chamado_id, campos) == 0:
        raise HTTPException(status_code=400, detail="Não foi possível atualizar o chamado.")
    return buscar_chamado(chamado_id)


@router.patch("/{chamado_id}/status", response_model=ChamadoOut)
def alterar_status(chamado_id: int, dados: StatusIn, usuario: UsuarioLogado):
    if not eh_atendente(usuario):
        raise HTTPException(status_code=403, detail="Apenas atendentes alteram o status.")
    carregar_chamado(chamado_id, usuario)
    alterar_status_chamado(chamado_id, dados.status)
    return buscar_chamado(chamado_id)


@router.post("/{chamado_id}/cancelar", response_model=ChamadoOut)
def cancelar(chamado_id: int, usuario: UsuarioLogado):
    carregar_chamado(chamado_id, usuario)
    if not cancelar_chamado(chamado_id):
        raise HTTPException(status_code=409, detail="Chamados concluídos ou já cancelados não podem ser cancelados.")
    return buscar_chamado(chamado_id)
