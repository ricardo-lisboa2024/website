# Website — Gerenciador de Atividades e Produções

## Resumo do Projeto

Aplicação web responsiva (Flask + SQLite) para gerenciar atividades e produções, com vinculação entre elas. Operacional 24/7 via systemd service no seu computador.

---

## Funcionalidades Implementadas

### ✓ Gerenciamento de Atividades
- **Criar**: formulário simples (Nome, Data, Descrição)
- **Listar**: cards com ícones (Ver, Editar, Excluir)
- **Visualizar**: página dedicada mostrando detalhes + produções relacionadas
- **Editar**: atualizar dados
- **Excluir**: com confirmação

### ✓ Gerenciamento de Produções
- **Criar**: formulário com dropdown pesquisável de atividades (Tom Select)
- **Listar**: cards mostrando título, quantidade, descrição e atividade relacionada
- **Editar**: com dropdown para trocar atividade relacionada
- **Excluir**: com confirmação
- **Vincular**: produções podem ser associadas a atividades (activity_id)

### ✓ Interface & UX
- **Menu lateral** com opções principais (Início, Atividades, Produções)
- **Hamburger menu** para mobile (automático em telas ≤900px)
- **Cards** com animações hover (transform + shadow)
- **Botões** com ícones (Font Awesome 6.4.0)
- **Dropdown pesquisável** (Tom Select, agora local — sem CDN)
- **Mensagens de sucesso** com fundo verde e ícone ✓
- **Imagem de fundo** suave (mesa de estudo) com overlay
- **Responsividade** completa (funciona bem em desktop e mobile)

### ✓ API & Exportação
- **JSON API**:
  - `GET /api/activities` — lista de atividades
  - `GET /api/productions` — lista de produções (com activity_name)
- **CSV Export**:
  - `GET /export/activities.csv` — dowload em CSV
  - `GET /export/productions.csv` — download em CSV (inclui activity_name)

### ✓ Banco de Dados
- SQLite3 com tabelas:
  - `activities` (id, name, date, description, created_at)
  - `productions` (id, title, quantity, description, activity_id, created_at)
- Vinculação via `activity_id` (foreign key lógica)
- Auto-migração: `init_db()` adiciona coluna `activity_id` em BD pré-existentes

### ✓ Inicialização Automática
- Serviço systemd (`website.service`) inicia ao boot
- Rodas em `0.0.0.0:5000` (acessível pela rede local)
- Logs em `journalctl -u website.service -f`

---

## Estrutura de Arquivos

```
/home/ricardo/website/
├── app.py                         # Aplicação Flask (rotas, lógica BD)
├── schema.sql                     # Schema SQL (inicialização)
├── requirements.txt               # Dependências (Flask>=2.0)
├── data.db                        # Banco SQLite3 (criado automaticamente)
├── static/
│   └── lib/
│       ├── tom-select.min.css     # Tom Select CSS (local)
│       └── tom-select.complete.min.js  # Tom Select JS (local)
├── templates/
│   ├── base.html                  # Template base (header, menu, estilos)
│   ├── index.html                 # Página inicial (visão geral)
│   ├── activities_list.html       # Listagem de atividades
│   ├── activities_add.html        # Formulário adicionar atividade
│   ├── activities_edit.html       # Formulário editar atividade
│   ├── activities_show.html       # Página de detalhes + produções
│   ├── productions_list.html      # Listagem de produções
│   ├── productions_add.html       # Formulário adicionar produção (com dropdown)
│   └── productions_edit.html      # Formulário editar produção (com dropdown)
├── .venv/                         # Python virtual environment
├── server.log                     # Log do servidor (se rodado com nohup)
└── server.pid                     # PID do servidor em background (se aplicável)
```

---

## Como Acessar

### No seu computador
```
http://127.0.0.1:5000/
ou
http://localhost:5000/
```

### De outro dispositivo na mesma rede Wi‑Fi
```
http://192.168.100.71:5000/
```
(Substitua o IP pela saída de `hostname -I` se diferente)

### Do celular
- Certifique-se de estar na mesma rede Wi‑Fi
- Abra Firefox e acesse `http://<IP-do-PC>:5000/`

---

## Comandos Úteis

### Verificar status do serviço
```bash
sudo systemctl status website.service
```

### Ver logs em tempo real
```bash
sudo journalctl -u website.service -f
```

### Parar o serviço
```bash
sudo systemctl stop website.service
```

### Iniciar novamente
```bash
sudo systemctl start website.service
```

### Reiniciar (útil após editar templates/código)
```bash
sudo systemctl restart website.service
```

### Consultar atividades direto no DB
```bash
sqlite3 /home/ricardo/website/data.db "SELECT * FROM activities ORDER BY created_at DESC;"
```

### Consultar produções com atividades vinculadas
```bash
sqlite3 /home/ricardo/website/data.db "SELECT p.id, p.title, p.quantity, a.name AS activity FROM productions p LEFT JOIN activities a ON p.activity_id = a.id ORDER BY p.created_at DESC;"
```

### Exportar produções em CSV
```bash
curl -sS http://127.0.0.1:5000/export/productions.csv -o productions.csv
```

### Consultar API de produções em JSON
```bash
curl -sS http://127.0.0.1:5000/api/productions | jq .
```

---

## Tecnologias Usadas

| Camada       | Tecnologia         | Versão   |
|--------------|-------------------|----------|
| Backend      | Flask             | ≥ 2.0    |
| BD           | SQLite3           | 3.x      |
| Frontend     | HTML5 + CSS3      | Native   |
| Pesquisa     | Tom Select        | 1.7+     |
| Ícones       | Font Awesome      | 6.4.0    |
| CSS Base     | Water.css         | 2.0      |
| Animações    | CSS Transitions   | Native   |
| Iniciador    | systemd           | Native   |

---

## Próximas Melhorias (Opcionais)

1. **Autenticação**: adicionar login/logout com senhas
2. **Paginação**: limitar a 10 itens por página
3. **Busca/Filtro**: campo de pesquisa nas listagens
4. **Gunicorn + Nginx**: trocar server de desenvolvimento por produção (mais robusto)
5. **Temas**: adicionar tema escuro
6. **Relatórios**: gráficos simples (ex: atividades por mês)
7. **Backup automático**: fazer dump do DB periodicamente
8. **Docker**: containerizar a app para fácil deploy

---

## Notas de Segurança

- ⚠️ **Desenvolvimento**: `SECRET_KEY` é 'dev' por padrão. Defina em produção:
  ```bash
  export SECRET_KEY="minha-chave-super-secreta"
  sudo systemctl restart website.service
  ```

- ⚠️ **Servidor**: atualmente roda com `debug=False` e `host=0.0.0.0`. Para produção recomenda-se Gunicorn + Nginx com certificado SSL.

- ⚠️ **Firewall**: certifique-se de que a porta 5000 está liberada (ou configure ufw):
  ```bash
  sudo ufw allow 5000/tcp
  ```

---

## Troubleshooting

### Porta 5000 já em uso
```bash
# Encontre o processo
sudo lsof -i :5000
# Mate-o (substitua PID)
sudo kill -9 <PID>
```

### Serviço não inicia
```bash
# Veja o erro
sudo journalctl -u website.service --no-pager | tail -50
```

### Templates não atualizam
```bash
# Sempre reinicie após editar templates
sudo systemctl restart website.service
```

### DB corrompido
```bash
# Recrie o BD (apaga dados existentes!)
rm /home/ricardo/website/data.db
python3 /home/ricardo/website/app.py  # run briefly to init
# depois sudo systemctl start website.service
```

---

## Suporte & Contato

Qualquer dúvida sobre uso ou customização:
- Verifique os logs: `sudo journalctl -u website.service -f`
- Teste a API: `curl -sS http://127.0.0.1:5000/api/activities`
- Consulte o BD direto: `sqlite3 data.db`

---

**Última atualização**: 13 de novembro de 2025  
**Versão**: 1.0.0
