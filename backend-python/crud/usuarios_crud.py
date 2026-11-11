import bcrypt
import json
from database.connection import conectar


# Hash usado quando o usuário não existe, para o tempo de resposta do login não revelar isso
_HASH_FALSO = bcrypt.hashpw(b"senha-falsa", bcrypt.gensalt()).decode("utf-8")


# ==========================================================
# ➕ CRIAR
# ==========================================================

def criar_usuario(dados):

    conn = conectar()
    cursor = conn.cursor()

    try:

        # ======================================================
        # VERIFICA SE USUÁRIO JÁ EXISTE
        # ======================================================

        cursor.execute("""
            SELECT id
            FROM usuarios
            WHERE usuario = ?
            LIMIT 1
        """, (dados["usuario"],))

        if cursor.fetchone():
            print("⚠️ Nome de usuário já está em uso.")
            return None

        # ======================================================
        # SENHA
        # ======================================================

        senha_hash = bcrypt.hashpw(
            dados["senha"].encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        # ======================================================
        # INSERT
        # ======================================================

        sql = """
            INSERT INTO usuarios (
                nome_completo,
                usuario,
                senha,
                setor,
                status,
                tipo
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """

        valores = (
            dados["nome_completo"],
            dados["usuario"],
            senha_hash,
            dados["setor"],
            dados["status"],
            dados["tipo"]
        )

        cursor.execute(sql, valores)
        conn.commit()

        return cursor.lastrowid

    except Exception as e:

        conn.rollback()

        print("❌ Erro ao criar usuário:", e)

        return None

    finally:

        cursor.close()
        conn.close()


# ==========================================================
# 🔑 AUTENTICAR (LOGIN)
# ==========================================================

def autenticar_usuario(usuario, senha):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, senha, status
            FROM usuarios
            WHERE usuario = ?
        """, (usuario,))

        resultado = cursor.fetchone()

        hash_salvo = resultado["senha"] if resultado else _HASH_FALSO

        try:
            senha_ok = bcrypt.checkpw(
                senha.encode("utf-8"),
                hash_salvo.encode("utf-8")
            )
        except ValueError:  # senha acima de 72 bytes
            senha_ok = False

        if not resultado or not senha_ok or resultado["status"] != "ativo":
            return None

        return resultado["id"]

    except Exception as e:
        print("❌ Erro ao autenticar usuário:", e)
        return None

    finally:
        cursor.close()
        conn.close()


# ==========================================================
# 📋 LISTAR TODOS
# ==========================================================

def listar_usuarios():
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                u.id,
                u.nome_completo,
                u.usuario,
                u.setor,
                u.tipo,
                u.status,
                p.nome AS perfil
            FROM usuarios u
            LEFT JOIN perfis_acesso p
                ON p.id = u.tipo
            ORDER BY u.nome_completo
        """)

        return cursor.fetchall()

    except Exception as e:
        print("❌ Erro ao listar usuários:", e)
        return []

    finally:
        cursor.close()
        conn.close()


# ==========================================================
# 📋 LISTAR USUÁRIOS ATIVOS
# ==========================================================

def listar_usuarios_ativos():
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                u.id,
                u.nome_completo,
                u.usuario,
                u.setor,
                u.status,
                u.tipo,
                p.nome AS perfil
            FROM usuarios u
            LEFT JOIN perfis_acesso p
                ON p.id = u.tipo
            WHERE u.status = 'ativo'
            ORDER BY u.nome_completo ASC
        """)

        return cursor.fetchall()

    except Exception as e:
        print("❌ Erro ao listar usuários ativos:", e)
        return []

    finally:
        cursor.close()
        conn.close()


# ==========================================================
# 🔎 BUSCAR POR ID
# ==========================================================

def buscar_usuario(id):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                u.id,
                u.nome_completo,
                u.usuario,
                u.setor,
                u.status,
                u.tipo,
                p.nome AS perfil
            FROM usuarios u
            LEFT JOIN perfis_acesso p
                ON p.id = u.tipo
            WHERE u.id = ?
        """, (id,))

        return cursor.fetchone()

    except Exception as e:
        print("❌ Erro ao buscar usuário:", e)
        return None

    finally:
        cursor.close()
        conn.close()


# ==========================================================
# 🔎 BUSCAR POR NOME DE USUÁRIO (LOGIN)
# ==========================================================

def buscar_usuario_por_login(login):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, usuario
            FROM usuarios
            WHERE usuario = ?
        """, (login,))

        return cursor.fetchone()

    except Exception as e:
        print("❌ Erro ao buscar usuário por login:", e)
        return None

    finally:
        cursor.close()
        conn.close()


# ==========================================================
# ✏️ ATUALIZAR
# ==========================================================

def atualizar_usuario(id, dados):
    conn = conectar()
    cursor = conn.cursor()

    try:
        campos = []
        valores = []

        # Campos permitidos para atualização
        campos_permitidos = [
            "nome_completo",
            "usuario",
            "setor",
            "status",
            "tipo"
        ]

        for campo in campos_permitidos:

            if campo in dados:
                campos.append(f"{campo}=?")
                valores.append(dados[campo])

        # Nenhum campo para atualizar
        if not campos:
            return 0

        sql = f"""
            UPDATE usuarios
            SET
                {", ".join(campos)}
            WHERE id=?
        """

        valores.append(id)

        cursor.execute(
            sql,
            tuple(valores)
        )

        conn.commit()

        return cursor.rowcount

    except Exception as e:

        print(
            "❌ Erro ao atualizar usuário:",
            e
        )

        conn.rollback()

        return 0

    finally:
        cursor.close()
        conn.close()

# ==========================================================
# 🔐 ALTERAR SENHA
# ==========================================================

def alterar_senha_usuario(usuario_id, senha_atual, nova_senha):
    conn = conectar()
    cursor = conn.cursor()

    try:
        # Busca a senha atual do usuário
        cursor.execute("""
            SELECT senha
            FROM usuarios
            WHERE id = ?
        """, (usuario_id,))

        resultado = cursor.fetchone()

        if not resultado:
            return False, "Usuário não encontrado."

        senha_hash_atual = resultado["senha"]

        # Verifica a senha atual
        try:
            senha_confere = bcrypt.checkpw(
                senha_atual.encode(),
                senha_hash_atual.encode()
            )
        except ValueError:  # senha acima de 72 bytes
            senha_confere = False

        if not senha_confere:
            return False, "A senha atual está incorreta."

        # Gera novo hash
        novo_hash = bcrypt.hashpw(
            nova_senha.encode(),
            bcrypt.gensalt()
        ).decode()

        # Atualiza a senha
        cursor.execute("""
            UPDATE usuarios
            SET senha = ?
            WHERE id = ?
        """, (
            novo_hash,
            usuario_id
        ))

        conn.commit()

        return True, "Senha alterada com sucesso!"

    except Exception as e:

        conn.rollback()

        print(
            "❌ Erro ao alterar senha:",
            e
        )

        return False, "Erro ao alterar senha."

    finally:
        cursor.close()
        conn.close()


# ==========================================================
# ❌ DELETAR
# ==========================================================

def deletar_usuario(id):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM usuarios WHERE id=?",
            (id,)
        )

        conn.commit()

        return cursor.rowcount

    except Exception as e:
        conn.rollback()
        print("❌ Erro ao deletar usuário:", e)
        return 0

    finally:
        cursor.close()
        conn.close()


# ==========================================================
# 🔐 BUSCAR PERFIL E PERMISSÕES DO USUÁRIO
# ==========================================================

def buscar_permissoes_usuario(usuario_id):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                u.id,
                u.nome_completo,
                u.tipo,
                p.nome AS perfil,
                p.menus,
                p.submenus
            FROM usuarios u
            INNER JOIN perfis_acesso p
                ON p.id = u.tipo
            WHERE u.id = ?
        """, (usuario_id,))

        resultado = cursor.fetchone()

        if not resultado:
            return None

        # Converte JSON do banco para listas Python
        if isinstance(resultado["menus"], str):
            resultado["menus"] = json.loads(
                resultado["menus"]
            )

        if isinstance(resultado["submenus"], str):
            resultado["submenus"] = json.loads(
                resultado["submenus"]
            )

        return resultado

    except Exception as e:
        print("❌ Erro ao buscar permissões do usuário:", e)
        return None

    finally:
        cursor.close()
        conn.close()


# ==========================================================
# 📋 LISTAR PERFIS ATIVOS DE USUÁRIO
# ==========================================================

def listar_perfis_ativos():
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                nome
            FROM perfis_acesso
            WHERE status = 'ativo'
            ORDER BY nome
        """)

        return cursor.fetchall()

    except Exception as e:
        print("❌ Erro ao listar perfis:", e)
        return []

    finally:
        cursor.close()
        conn.close()


# ==========================================================
# 📋 BUSCAR NOME DOS PERFIS
# ==========================================================

def buscar_nome_perfil(perfil_id):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT nome
            FROM perfis_acesso
            WHERE id = ?
        """, (perfil_id,))

        resultado = cursor.fetchone()

        if resultado:
            return resultado["nome"]

        return None

    except Exception as e:
        print("❌ Erro ao buscar perfil:", e)
        return None

    finally:
        cursor.close()
        conn.close()
