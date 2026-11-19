# Documentação da API de Chamados

*Referência dos endpoints do backend-python (FastAPI + SQLite).*

## 1. Visão geral

| Item | Valor |
| --- | --- |
| URL base (local) | `http://localhost:8000` |
| Formato | JSON (o login usa formulário) |
| Autenticação | Token JWT no header `Authorization: Bearer <token>` |
| Validade do token | 5 horas ||
| Documentação interativa | `/docs` (Swagger UI) e `/redoc` |


Se você chamar a API pelo ngrok e receber uma página HTML de aviso em vez de JSON, envie o header `ngrok-skip-browser-warning: 1`.

## 2. Autenticação

1. Faça login em `POST /auth/token` com `username` e `password` (formulário). A resposta traz o `access_token`.
2. Envie o token em todas as chamadas protegidas:

```
Authorization: Bearer eyJhbGciOi...
```

3. Depois de 5 horas o token expira e a API responde 401. Faça login de novo.

Um usuário marcado como `inativo` não consegue logar, e os tokens que ele já tinha deixam de valer imediatamente.

## 3. Convenções

### 3.1 Formato de erro

Erros comuns vêm como `{"detail": "mensagem"}`. Erros de validação (422) trazem uma lista indicando o campo:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "assunto"], 
      "msg": "Field required"
    }
  ]
}
```

### 3.2 Códigos de status

| Código | Significado | Quando ocorre |
| --- | --- | --- |
| 200 | OK | consultas e atualizações |
| 201 | Criado | POST que cria registro |
| 204 | Sem conteúdo | exclusão de usuário |
| 400 | Pedido inválido | nenhum campo para atualizar, senha atual errada, excluir a própria conta |
| 401 | Não autenticado | sem token, token inválido ou expirado, usuário inativo, login errado |
| 403 | Sem permissão | perfil sem acesso à rota |
| 404 | Não encontrado | recurso inexistente, ou chamado de outra pessoa |
| 409 | Conflito | usuário duplicado, cancelar chamado concluído ou já cancelado, excluir usuário com vínculos |
| 422 | Dados inválidos | campo faltando, fora do formato ou valor fora da lista |
| 500 | Erro interno | falha ao gravar no banco (veja o terminal da API) |

### 3.3 Limites dos campos

| Campo | Regra |
| --- | --- |
| `senha`, `nova_senha` | de 8 caracteres até 72 bytes |
| `usuario` | de 3 a 50 caracteres, único |
| `nome_completo` | de 1 a 120 caracteres |
| `setor` | até 80 caracteres |
| `assunto` | de 1 a 150 caracteres |
| `descricao`, `resposta` | mínimo de 1 caractere |

## 4. Perfis e permissões

A API vem com três perfis: **Administrador**, **Técnico** e **Usuário**. São chamados de **atendentes** o Administrador e o Técnico (definido em `PERFIS_ATENDENTES`, no `config.py`).

| Ação | Usuário comum | Técnico | Administrador |
| --- | --- | --- | --- |
| Login, `/auth/me`, alterar a própria senha | sim | sim | sim |
| Abrir chamado | sim | sim | sim |
| Listar e ver chamados | só os seus | todos | todos |
| Ver e enviar respostas | só nos seus chamados | todos | todos |
| Editar chamado, mudar status, cancelar | não | sim | sim |
| Ver o próprio usuário (`GET /usuarios/{id}`) | sim | sim | sim |
| Gerenciar usuários e listar perfis | não | não | sim |   **(ALGUMAS ROTAS COMENTADAS)**



Um chamado que o usuário não pode ver responde **404**, e não 403, para não revelar que ele existe.

## 5. Endpoints

### 5.1 Saúde

#### GET /health

**Acesso:** público.

Verifica se a API está de pé.

```json
{ "status": "ok" }
```

### 5.2 Autenticação

#### POST /auth/token

**Acesso:** público.

Faz o login. O corpo é um **formulário** (`application/x-www-form-urlencoded`), não JSON.

| Campo | Descrição |
| --- | --- |
| `username` | nome de usuário |
| `password` | senha |

**Resposta 200:**

```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

**Erros:** 401 `Usuário ou senha incorretos` (inclui usuário inativo), 422 campos ausentes.

#### GET /auth/me

**Acesso:** logado.

Devolve os dados do usuário logado e os menus do perfil, para o front montar a tela.

```json
{
  "id": 1,
  "nome_completo": "Administrador",
  "usuario": "admin",
  "setor": "TI",
  "status": "ativo",
  "tipo": 1,
  "perfil": "Administrador",
  "menus": ["chamados", "usuarios"],
  "submenus": []
}
```

#### POST /auth/alterar-senha **(ROTA COMENTADA!)**

**Acesso:** logado.

```json
{
  "senha_atual": "senha12345",
  "nova_senha": "novasenha123"
}
```

**Resposta 200:** `{"mensagem": "Senha alterada com sucesso!"}`

**Erros:** 400 `A senha atual está incorreta.`, 422 nova senha fora das regras.

#### POST /auth/registro (opcional) **(ROTA COMENTADA!)**

**Acesso:** público, **só existe se você aplicou o auto-cadastro**, e só funciona com `REGISTRO_ABERTO=true`.

A pessoa se cadastra sempre com o perfil `Usuário`. Ela não escolhe o perfil nem o status. Com `REGISTRO_STATUS=inativo`, a conta espera um administrador liberar.

```json
{
  "nome_completo": "Carla Dias",
  "usuario": "carla",
  "senha": "senha12345",
  "setor": "RH"
}
```

**Respostas:** 201 com uma `mensagem`, 403 auto-cadastro desativado, 409 usuário já existe, 422 dados inválidos.

### 5.3 Usuários

#### POST /usuarios

**Acesso:** administrador.

Cria um usuário.

```json
{
  "nome_completo": "Ana Souza",
  "usuario": "ana",
  "senha": "senha12345",
  "setor": "Financeiro",
  "status": "ativo",
  "tipo": 3
}
```

`status` é opcional (padrão `ativo`). `tipo` é o id do perfil (consulte `GET /usuarios/perfis`).

**Respostas:** 201 com o usuário criado, 409 `Nome de usuário já está em uso.`, 422 `Perfil (tipo) inexistente.` ou dados inválidos, 403 sem permissão.

#### GET /usuarios

**Acesso:** administrador.

Lista os usuários, ordenados por nome. Parâmetro opcional: `apenas_ativos=true` (padrão `false`).

#### GET /usuarios/perfis

**Acesso:** administrador.

Lista os perfis ativos, para preencher o campo `tipo`.

```json
[
  { "id": 1, "nome": "Administrador" },
  { "id": 2, "nome": "Técnico" },
  { "id": 3, "nome": "Usuário" }
]
```

#### GET /usuarios/{usuario\_id}

**Acesso:** administrador, ou o próprio usuário.

**Erros:** 403 `Sem permissão.`, 404 `Usuário não encontrado.`

#### PATCH /usuarios/{usuario\_id} **(ROTA COMENTADA!)**

**Acesso:** administrador.

Atualiza só os campos enviados: `nome_completo`, `usuario`, `setor`, `status`, `tipo`.

```json
{ "status": "inativo" }
```

**Erros:** 400 `Nenhum campo para atualizar.`, 404, 409 `Nome de usuário já está em uso.`, 422 perfil inexistente.

#### DELETE /usuarios/{usuario\_id} **(ROTA COMENTADA!)**

**Acesso:** administrador.

**Resposta 204** sem corpo.

**Erros:** 400 `Você não pode excluir a própria conta.`, 404, 409 quando o usuário já tem chamados ou respostas. Nesse caso, marque-o como `inativo` com o `PATCH`.

### 5.4 Chamados

#### POST /chamados

**Acesso:** logado.

Abre um chamado. O solicitante é o usuário logado e o status inicial é `aberto`.

```json
{
  "assunto": "PC lento",
  "descricao": "Demora para ligar",
  "prioridade": "alta"
}
```

`prioridade` é opcional (padrão `normal`).

**Resposta 201:**

```json
{
  "id": 12,
  "solicitante_id": 3,
  "solicitante": "Ana Souza",
  "usuario": "ana",
  "setor": "Financeiro",
  "perfil": "Usuário",
  "assunto": "PC lento",
  "descricao": "Demora para ligar",
  "prioridade": "alta",
  "status": "aberto",
  "created_at": "2026-11-13T14:20:05Z",
  "updated_at": "2026-11-13T14:20:05Z"
}
```

#### GET /chamados

**Acesso:** logado.

Lista os chamados, do mais novo para o mais antigo. Atendentes veem todos; os demais, só os seus. Parâmetro opcional: `status` (um dos valores da seção 6.2), por exemplo `GET /chamados?status=aberto`.

#### GET /chamados/{chamado\_id}

**Acesso:** dono do chamado ou atendente.

**Erro:** 404 `Chamado não encontrado.`

#### PATCH /chamados/{chamado\_id}

**Acesso:** atendente (Administrador ou Técnico).

Edita só os campos enviados: `assunto`, `descricao`, `prioridade`.

```json
{ "prioridade": "urgente" }
```

**Erros:** 400 `Nenhum campo para atualizar.`, 403, 404, 422.

#### PATCH /chamados/{chamado\_id}/status

**Acesso:** atendente.

```json
{ "status": "em_andamento" }
```

**Erros:** 403, 404, 422 (status fora da lista).

#### POST /chamados/{chamado\_id}/cancelar

**Acesso:** atendente.

Muda o status para `cancelado`, sem corpo.

**Erros:** 403, 404, 409 `Chamados concluídos ou já cancelados não podem ser cancelados.`

### 5.5 Respostas

As respostas formam a conversa dentro de um chamado. Não é possível editar nem apagar uma resposta, e responder **não** muda o status do chamado.

#### GET /chamados/{chamado\_id}/respostas

**Acesso:** dono do chamado ou atendente.

Lista as respostas, da mais antiga para a mais nova.

#### POST /chamados/{chamado\_id}/respostas

**Acesso:** dono do chamado ou atendente.

```json
{ "resposta": "Vou verificar o disco." }
```

**Resposta 201:**

```json
{
  "id": 7,
  "chamado_id": 12,
  "usuario_id": 2,
  "usuario": "Carlos Lima",
  "login": "tec",
  "setor": "TI",
  "perfil": "Técnico",
  "resposta": "Vou verificar o disco.",
  "created_at": "2026-11-13T14:35:10Z",
  "updated_at": "2026-11-13T14:35:10Z"
}
```

**Erros:** 404 se o chamado não existe ou não é seu, 422 resposta vazia.

#### GET /chamados/{chamado\_id}/respostas/{resposta\_id}

**Acesso:** dono do chamado ou atendente.

**Erro:** 404 `Resposta não encontrada.` (inclui o caso de a resposta ser de outro chamado).

## 6. Modelos de dados

### 6.1 Objetos

**Usuário**

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `id` | inteiro | identificador |
| `nome_completo` | texto | nome |
| `usuario` | texto | nome de login, único |
| `setor` | texto | setor da pessoa |
| `status` | texto | `ativo` ou `inativo` |
| `tipo` | inteiro | id do perfil |
| `perfil` | texto | nome do perfil |

A senha nunca é devolvida. Ela fica guardada como hash bcrypt.

**Chamado**

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `id` | inteiro | identificador |
| `solicitante_id` | inteiro | id de quem abriu |
| `solicitante` | texto | nome completo de quem abriu |
| `usuario` | texto | login de quem abriu |
| `setor` | texto | setor de quem abriu |
| `perfil` | texto | perfil de quem abriu |
| `assunto` | texto | título do chamado |
| `descricao` | texto | detalhes |
| `prioridade` | texto | veja 6.2 |
| `status` | texto | veja 6.2 |
| `created_at` | data e hora | criação, em UTC |
| `updated_at` | data e hora | última alteração, em UTC |

**Resposta**

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `id` | inteiro | identificador |
| `chamado_id` | inteiro | chamado a que pertence |
| `usuario_id` | inteiro | id de quem escreveu |
| `usuario` | texto | nome completo de quem escreveu |
| `login` | texto | login de quem escreveu |
| `setor` | texto | setor de quem escreveu |
| `perfil` | texto | perfil de quem escreveu |
| `resposta` | texto | conteúdo |
| `created_at` | data e hora | criação, em UTC |
| `updated_at` | data e hora | última alteração, em UTC |

### 6.2 Valores aceitos

| Campo | Valores |
| --- | --- |
| `prioridade` | `baixa`, `normal`, `alta`, `urgente` |
| `status` do chamado | `aberto`, `em_andamento`, `pausado`, `concluido`, `cancelado` |
| `status` do usuário | `ativo`, `inativo` |

Para aceitar outras prioridades, edite a lista `Prioridade` em `schemas.py`.

## 7. Regras de negócio

- O solicitante de um chamado é sempre o usuário logado; o cliente não escolhe.
- Todo chamado nasce com o status `aberto`.
- Só chamados que não estão `concluido` nem `cancelado` podem ser cancelados.
- Um usuário com chamados ou respostas não pode ser excluído. Use o status `inativo`.
- Um administrador não pode excluir a própria conta.
- Trocar o login de um usuário para um já existente devolve 409.
- Ao se cadastrar (se o auto-cadastro estiver ligado), a pessoa recebe sempre o perfil `Usuário`.



## 8. Configuração

Variáveis do arquivo `.env`:

| Variável | Obrigatória | Descrição |
| --- | --- | --- |
| `SECRET_KEY` | sim | chave que assina os tokens |
| `ALLOWED_ORIGINS` | não | origens liberadas no CORS, separadas por vírgula (padrão: todas) |
| `ADMIN_USUARIO`, `ADMIN_SENHA` | não | primeiro administrador, criado só se não houver usuários |
| `DATABASE_PATH` | não | arquivo do banco (padrão `chamados.db`) |
| `REGISTRO_ABERTO`, `REGISTRO_STATUS` | não | só no auto-cadastro opcional |

Constantes no `config.py`: `TOKEN_EXPIRA_HORAS` (5), `PERFIL_ADMIN` e `PERFIS_ATENDENTES`.

## 9. Observações

- Sem o limitador de requisições, as rotas de login e cadastro não têm limite de tentativas. Com o limitador aplicado, elas respondem **429** com o header `Retry-After` quando o IP excede o limite.
- O token é assinado, mas não criptografado: ele carrega o id do usuário e a validade, e nada sensível.
- Não há refresh token: ao expirar, faça login de novo.
- O banco é um arquivo SQLite. Os dados ficam em cada máquina onde a API roda.
