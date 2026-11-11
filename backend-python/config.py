import os

from dotenv import load_dotenv

load_dotenv()  # lê o arquivo .env (se existir)

SECRET_KEY = os.environ["SECRET_KEY"]  # sem ela a API nem sobe
ALGORITHM = "HS256"
TOKEN_EXPIRA_HORAS = 5

DATABASE_PATH = os.getenv("DATABASE_PATH", "chamados.db")
ORIGENS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]

# Primeiro administrador: criado só se a tabela de usuários estiver vazia
ADMIN_USUARIO = os.getenv("ADMIN_USUARIO")
ADMIN_SENHA = os.getenv("ADMIN_SENHA")

# Nomes de perfis (tabela perfis_acesso) com poderes especiais
PERFIL_ADMIN = "Administrador"
PERFIS_ATENDENTES = {"Administrador", "Técnico"}  # veem e tratam todos os chamados
