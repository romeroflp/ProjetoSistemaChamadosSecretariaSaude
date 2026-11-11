from database.connection import conectar


# ==========================================================
# 📝 CADASTRAR CHAMADO
# ==========================================================

def criar_chamado(dados):
    conn = conectar()
    cursor = conn.cursor()

    try:

        sql = """
            INSERT INTO chamados (
                solicitante_id,
                assunto,
                descricao,
                prioridade,
                status
            )
            VALUES (?, ?, ?, ?, ?)
        """

        valores = (
            dados["solicitante_id"],
            dados["assunto"],
            dados["descricao"],
            dados.get("prioridade", "normal"),
            dados.get("status", "aberto")
        )

        cursor.execute(sql, valores)
        conn.commit()

        return cursor.lastrowid

    except Exception as e:

        conn.rollback()

        print(
            "❌ Erro ao cadastrar chamado:",
            e
        )

        return None

    finally:

        cursor.close()
        conn.close()


# ==========================================================
# 📋 LISTAR CHAMADOS
# ==========================================================

def listar_chamados(solicitante_id=None, status=None):
    conn = conectar()
    cursor = conn.cursor()

    # Filtros opcionais: sem argumentos, lista todos (como antes)
    condicoes = []
    valores = []

    if solicitante_id is not None:
        condicoes.append("c.solicitante_id = ?")
        valores.append(solicitante_id)

    if status:
        condicoes.append("c.status = ?")
        valores.append(status)

    where = ("WHERE " + " AND ".join(condicoes)) if condicoes else ""

    try:
        cursor.execute(f"""
            SELECT
                c.id,
                c.solicitante_id,

                u.nome_completo AS solicitante,
                u.usuario,
                u.setor,

                p.nome AS perfil,

                c.assunto,
                c.descricao,
                c.prioridade,
                c.status,
                c.created_at,
                c.updated_at

            FROM chamados c

            INNER JOIN usuarios u
                ON u.id = c.solicitante_id

            LEFT JOIN perfis_acesso p
                ON p.id = u.tipo

            {where}

            ORDER BY c.created_at DESC, c.id DESC
        """, tuple(valores))

        return cursor.fetchall()

    except Exception as e:
        print("❌ Erro ao listar chamados:", e)
        return []

    finally:
        cursor.close()
        conn.close()


# ==========================================================
# 👁 BUSCAR CHAMADO
# ==========================================================

def buscar_chamado(chamado_id):
    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                c.id,
                c.solicitante_id,
                u.nome_completo AS solicitante,
                u.usuario,
                c.assunto,
                u.setor,
                p.nome AS perfil,
                c.descricao,
                c.prioridade,
                c.status,
                c.created_at,
                c.updated_at
            FROM chamados c

            INNER JOIN usuarios u
                ON u.id = c.solicitante_id

            LEFT JOIN perfis_acesso p
                ON p.id = u.tipo

            WHERE c.id = ?
        """, (chamado_id,))

        return cursor.fetchone()

    except Exception as e:

        print(
            "❌ Erro ao buscar chamado:",
            e
        )

        return None

    finally:

        cursor.close()
        conn.close()


# ==========================================================
# ✏️ ATUALIZAR CHAMADO
# ==========================================================

def atualizar_chamado(chamado_id, dados):

    if not dados:
        return 0

    campos = []
    valores = []

    # O status tem função própria (alterar_status_chamado), que valida os valores
    campos_permitidos = {
        "assunto",
        "descricao",
        "prioridade"
    }

    for campo, valor in dados.items():

        if campo in campos_permitidos:

            campos.append(
                f"{campo} = ?"
            )

            valores.append(valor)

    if not campos:
        return 0

    conn = conectar()
    cursor = conn.cursor()

    try:

        sql = f"""
            UPDATE chamados
            SET {", ".join(campos)}
            WHERE id = ?
        """

        valores.append(chamado_id)

        cursor.execute(
            sql,
            tuple(valores)
        )

        conn.commit()

        return cursor.rowcount

    except Exception as e:

        conn.rollback()

        print(
            "❌ Erro ao atualizar chamado:",
            e
        )

        return 0

    finally:

        cursor.close()
        conn.close()


# ==========================================================
# 🔄 ALTERAR STATUS
# ==========================================================

def alterar_status_chamado(chamado_id, status):

    status_permitidos = {
        "aberto",
        "em_andamento",
        "pausado",
        "concluido",
        "cancelado"
    }

    if status not in status_permitidos:

        print(
            "❌ Status de chamado inválido:",
            status
        )

        return False

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE chamados
            SET status = ?
            WHERE id = ?
        """, (
            status,
            chamado_id
        ))

        conn.commit()

        return cursor.rowcount > 0

    except Exception as e:

        conn.rollback()

        print(
            "❌ Erro ao alterar status do chamado:",
            e
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==========================================================
# 🚫 CANCELAR CHAMADO
# ==========================================================

def cancelar_chamado(chamado_id):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE chamados
            SET status = 'cancelado'
            WHERE id = ?
            AND status NOT IN ('concluido', 'cancelado')
        """, (chamado_id,))

        conn.commit()

        return cursor.rowcount > 0

    except Exception as e:

        conn.rollback()

        print(
            "❌ Erro ao cancelar chamado:",
            e
        )

        return False

    finally:

        cursor.close()
        conn.close()
