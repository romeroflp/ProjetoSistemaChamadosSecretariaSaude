from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field


def _limite_bcrypt(valor: str) -> str:
    if len(valor.encode("utf-8")) > 72:  # limite do algoritmo bcrypt
        raise ValueError("A senha pode ter no máximo 72 bytes")
    return valor


def _como_utc(data: datetime) -> datetime:
    # O SQLite guarda CURRENT_TIMESTAMP em UTC, sem fuso. Marcar como UTC faz o JSON sair com "Z"
    return data.replace(tzinfo=timezone.utc) if data.tzinfo is None else data


Senha = Annotated[str, Field(min_length=8), AfterValidator(_limite_bcrypt)]
DataUtc = Annotated[datetime, AfterValidator(_como_utc)]

# Ajuste as listas abaixo para os valores que o seu sistema realmente usa
Prioridade = Literal["baixa", "normal", "alta", "urgente"]
StatusChamado = Literal["aberto", "em_andamento", "pausado", "concluido", "cancelado"]
StatusUsuario = Literal["ativo", "inativo"]


class Token(BaseModel):
    access_token: str
    token_type: str


# ---------- Usuários ----------
class PerfilOut(BaseModel):
    id: int
    nome: str


class UsuarioCriar(BaseModel):
    nome_completo: str = Field(min_length=1, max_length=120)
    usuario: str = Field(min_length=3, max_length=50)
    senha: Senha
    setor: str = Field(max_length=80)
    status: StatusUsuario = "ativo"
    tipo: int


class UsuarioAtualizar(BaseModel):
    nome_completo: str | None = Field(None, min_length=1, max_length=120)
    usuario: str | None = Field(None, min_length=3, max_length=50)
    setor: str | None = Field(None, max_length=80)
    status: StatusUsuario | None = None
    tipo: int | None = None


class AlterarSenha(BaseModel):
    senha_atual: str
    nova_senha: Senha


class UsuarioOut(BaseModel):
    id: int
    nome_completo: str
    usuario: str
    setor: str
    status: str
    tipo: int
    perfil: str | None = None


class MeOut(UsuarioOut):
    menus: list = []
    submenus: list = []


# ---------- Chamados ----------
class ChamadoCriar(BaseModel):
    assunto: str = Field(min_length=1, max_length=150)
    descricao: str = Field(min_length=1)
    prioridade: Prioridade = "normal"


class ChamadoAtualizar(BaseModel):
    assunto: str | None = Field(None, min_length=1, max_length=150)
    descricao: str | None = Field(None, min_length=1)
    prioridade: Prioridade | None = None


class StatusIn(BaseModel):
    status: StatusChamado


class ChamadoOut(BaseModel):
    id: int
    solicitante_id: int
    solicitante: str
    usuario: str
    setor: str
    perfil: str | None = None
    assunto: str
    descricao: str
    prioridade: str
    status: str
    created_at: DataUtc
    updated_at: DataUtc


# ---------- Respostas ----------
class RespostaCriar(BaseModel):
    resposta: str = Field(min_length=1)


class RespostaOut(BaseModel):
    id: int
    chamado_id: int
    usuario_id: int
    usuario: str
    login: str
    setor: str
    perfil: str | None = None
    resposta: str
    created_at: DataUtc
    updated_at: DataUtc
