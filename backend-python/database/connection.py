import sqlite3

import config


def _linha_como_dict(cursor, linha):
    # Faz fetchone()/fetchall() devolverem dicionários, como o dictionary=True do MySQL
    return {coluna[0]: linha[i] for i, coluna in enumerate(cursor.description)}


def conectar():
    conn = sqlite3.connect(config.DATABASE_PATH, timeout=10)
    conn.row_factory = _linha_como_dict
    conn.execute("PRAGMA foreign_keys = ON")  # o SQLite NÃO valida chaves estrangeiras por padrão
    return conn
