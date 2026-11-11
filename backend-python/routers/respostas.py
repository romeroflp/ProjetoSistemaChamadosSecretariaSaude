from fastapi import APIRouter, HTTPException

from crud.chamados_respostas_crud import buscar_resposta, criar_resposta, listar_respostas_chamado
from routers.chamados import carregar_chamado
from schemas import RespostaCriar, RespostaOut
from security import UsuarioLogado

router = APIRouter(prefix="/chamados/{chamado_id}/respostas", tags=["Respostas"])


@router.get("", response_model=list[RespostaOut])
def listar(chamado_id: int, usuario: UsuarioLogado):
    carregar_chamado(chamado_id, usuario)  # garante que o usuário pode ver o chamado
    return listar_respostas_chamado(chamado_id)


@router.post("", response_model=RespostaOut, status_code=201)
def criar(chamado_id: int, dados: RespostaCriar, usuario: UsuarioLogado):
    carregar_chamado(chamado_id, usuario)
    nova_id = criar_resposta({"chamado_id": chamado_id, "usuario_id": usuario["id"], "resposta": dados.resposta})
    if nova_id is None:
        raise HTTPException(status_code=500, detail="Erro ao cadastrar resposta.")
    return buscar_resposta(nova_id)


@router.get("/{resposta_id}", response_model=RespostaOut)
def buscar(chamado_id: int, resposta_id: int, usuario: UsuarioLogado):
    carregar_chamado(chamado_id, usuario)
    resposta = buscar_resposta(resposta_id)
    if resposta is None or resposta["chamado_id"] != chamado_id:
        raise HTTPException(status_code=404, detail="Resposta não encontrada.")
    return resposta
