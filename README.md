# Website simples com Flask + SQLite

Projeto mínimo que permite inserir informações através de um formulário e armazená-las em um banco SQLite.

Requisitos
- Python 3.8+

Instalação rápida

```bash
cd /home/user/website
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Inicializar o banco de dados (opcional — o app cria automaticamente se não existir):

```bash
python3 -c "from app import init_db; init_db()"
```

Executar o servidor

```bash
python3 app.py
```

Acesse em `http://127.0.0.1:5000/` e use o menu para registrar atividades e produções.

Novas rotas úteis:

- Lista de atividades (HTML): `GET /activities`
- Formulário de adicionar atividade: `GET /activities/add` / `POST /activities/add`
- Editar atividade: `GET /activities/<id>/edit` / `POST /activities/<id>/edit`
- Excluir atividade: `POST /activities/<id>/delete`
- Export CSV de atividades: `GET /export/activities.csv`
- API JSON de atividades: `GET /api/activities`

- Lista de produções (HTML): `GET /productions`
- Formulário de adicionar produção: `GET /productions/add` / `POST /productions/add`
- Editar produção: `GET /productions/<id>/edit` / `POST /productions/<id>/edit`
- Excluir produção: `POST /productions/<id>/delete`
- Export CSV de produções: `GET /export/productions.csv`
- API JSON de produções: `GET /api/productions`

Notas
- Em produção, defina `SECRET_KEY` de forma segura.
- O arquivo do banco é `data.db` no diretório do projeto.
