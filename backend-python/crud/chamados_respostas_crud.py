from database.connection import conectar


# ==========================================================
# 💬 CADASTRAR RESPOSTA
# ==========================================================

def criar_resposta(dados):
    conn = conectar()
    cursor = conn.cursor()

    try:

        sql = """
            INSERT INTO chamados_respostas (
                chamado_id,
                usuario_id,
                resposta
            )
            VALUES (?, ?, ?)
        """

        valores = (
            dados["chamado_id"],
            dados["usuario_id"],
            dados["resposta"]
        )

        cursor.execute(
            sql,
            valores
        )

        conn.commit()

        return cursor.lastrowid

    except Exception as e:

        conn.rollback()

        print(
            "❌ Erro ao cadastrar resposta:",
            e
        )

        return None

    finally:

        cursor.close()
        conn.close()


# ==========================================================
# 📋 LISTAR RESPOSTAS DE UM CHAMADO
# ==========================================================

def listar_respostas_chamado(chamado_id):
    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                r.id,
                r.chamado_id,
                r.usuario_id,
                u.nome_completo AS usuario,
                u.usuario AS login,
                u.setor,
                p.nome AS perfil,
                r.resposta,
                r.created_at,
                r.updated_at

            FROM chamados_respostas r

            INNER JOIN usuarios u
                ON u.id = r.usuario_id

            LEFT JOIN perfis_acesso p
                ON p.id = u.tipo

            WHERE r.chamado_id = ?

            ORDER BY r.created_at ASC, r.id ASC
        """, (chamado_id,))

        return cursor.fetchall()

    except Exception as e:

        print(
            "❌ Erro ao listar respostas do chamado:",
            e
        )

        return []

    finally:

        cursor.close()
        conn.close()


# ==========================================================
# 👁 BUSCAR UMA RESPOSTA
# ==========================================================

def buscar_resposta(resposta_id):
    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                r.id,
                r.chamado_id,
                r.usuario_id,
                u.nome_completo AS usuario,
                u.usuario AS login,
                u.setor,
                p.nome AS perfil,
                r.resposta,
                r.created_at,
                r.updated_at

            FROM chamados_respostas r

            INNER JOIN usuarios u
                ON u.id = r.usuario_id

            LEFT JOIN perfis_acesso p
                ON p.id = u.tipo

            WHERE r.id = ?
        """, (resposta_id,))

        return cursor.fetchone()

    except Exception as e:

        print(
            "❌ Erro ao buscar resposta:",
            e
        )

        return None

    finally:

        cursor.close()
        conn.close()
