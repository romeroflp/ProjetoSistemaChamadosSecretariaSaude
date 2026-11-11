import json

import config
from crud.usuarios_crud import criar_usuario
from database.connection import conectar

SQL_TABELAS = """
CREATE TABLE IF NOT EXISTS perfis_acesso (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT NOT NULL UNIQUE,
    menus     TEXT NOT NULL DEFAULT '[]',
    submenus  TEXT NOT NULL DEFAULT '[]',
    status    TEXT NOT NULL DEFAULT 'ativo'
);

CREATE TABLE IF NOT EXISTS usuarios (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_completo  TEXT NOT NULL,
    usuario        TEXT NOT NULL UNIQUE,
    senha          TEXT NOT NULL,
    setor          TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo')),
    tipo           INTEGER NOT NULL REFERENCES perfis_acesso(id)
);

CREATE TABLE IF NOT EXISTS chamados (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitante_id  INTEGER NOT NULL REFERENCES usuarios(id),
    assunto         TEXT NOT NULL,
    descricao       TEXT NOT NULL,
    prioridade      TEXT NOT NULL DEFAULT 'normal',
    status          TEXT NOT NULL DEFAULT 'aberto'
                    CHECK (status IN ('aberto', 'em_andamento', 'pausado', 'concluido', 'cancelado')),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_chamados_solicitante ON chamados(solicitante_id);
CREATE INDEX IF NOT EXISTS idx_chamados_status ON chamados(status);

-- O SQLite não tem ON UPDATE CURRENT_TIMESTAMP como o MySQL; o trigger faz esse papel
CREATE TRIGGER IF NOT EXISTS trg_chamados_updated_at
AFTER UPDATE ON chamados
BEGIN
    UPDATE chamados SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TABLE IF NOT EXISTS chamados_respostas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    chamado_id  INTEGER NOT NULL REFERENCES chamados(id) ON DELETE CASCADE,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id),
    resposta    TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_respostas_chamado ON chamados_respostas(chamado_id);

CREATE TRIGGER IF NOT EXISTS trg_respostas_updated_at
AFTER UPDATE ON chamados_respostas
BEGIN
    UPDATE chamados_respostas SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
"""


def criar_tabelas():
    conn = conectar()
    try:
        conn.execute("PRAGMA journal_mode = WAL")  # leitura e escrita ao mesmo tempo, sem travar
        conn.executescript(SQL_TABELAS)
        conn.commit()
    finally:
        conn.close()


def semear():
    """Dados iniciais: perfis padrão e o primeiro administrador.
    Se você já tem perfis_acesso reais, cadastre-os e este bloco deixa de agir."""
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) AS total FROM perfis_acesso")

        if cursor.fetchone()["total"] == 0:
            cursor.executemany(
                "INSERT INTO perfis_acesso (nome, menus, submenus) VALUES (?, ?, ?)",
                [
                    ("Administrador", json.dumps(["chamados", "usuarios"]), "[]"),
                    ("Técnico", json.dumps(["chamados"]), "[]"),
                    ("Usuário", json.dumps(["chamados"]), "[]"),
                ],
            )
            conn.commit()

        cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
        total_usuarios = cursor.fetchone()["total"]

        cursor.execute("SELECT id FROM perfis_acesso WHERE nome = ?", (config.PERFIL_ADMIN,))
        perfil_admin = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if config.ADMIN_USUARIO and config.ADMIN_SENHA and total_usuarios == 0 and perfil_admin:
        criar_usuario({
            "nome_completo": "Administrador",
            "usuario": config.ADMIN_USUARIO,
            "senha": config.ADMIN_SENHA,
            "setor": "TI",
            "status": "ativo",
            "tipo": perfil_admin["id"],
        })
