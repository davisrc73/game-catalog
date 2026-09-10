# 🎮 Catálogo de Jogos para Synology NAS

Web portal leve para gerir um catálogo de jogos guardados no NAS, organizado por
consola, com scan automático das pastas, deteção de novos/removidos e procura de
capas online. Pensado para correr com poucos recursos no **DS220+** (Intel Celeron x86_64, 2 GB de RAM)
ou modelos ARM como o **DS220j** (Realtek RTD1296). A imagem Docker Python slim é
multi-arquitetura e suporta ambos nativamente.

- **Backend:** Python + Flask, servido por **waitress** (leve, sem fork — ideal para sistemas com pouca RAM)
- **Base de dados:** SQLite (modo WAL, sem servidor extra)
- **Frontend:** HTML + CSS/JS próprio, **sem dependências externas** (funciona offline na LAN) com pesquisa global
- **Capas:** SteamGridDB · **Metadados:** IGDB (ambos opcionais), guardados localmente com validação de segurança anti-SSRF

---

## 1. Estrutura do projeto

```
game-catalog/
├── app/
│   ├── __init__.py
│   ├── app.py            # Aplicação Flask (rotas + pesquisa global + API)
│   ├── config.py         # Configuração via variáveis de ambiente
│   ├── database.py       # SQLite (esquema + ligação)
│   ├── models.py         # Acesso a dados (queries)
│   ├── scanner.py        # Lógica de scan/sincronização com o NAS e filtro CUE/BIN
│   ├── metadata.py       # Capas (SteamGridDB) + metadados (IGDB) + validação de URLs
│   ├── templates/        # index, console, game, edit, search, base
│   └── static/           # css/style.css, js/main.js
├── tests/                # Suite de testes unitários com unittest nativo
├── scan.py               # Scan via linha de comandos (para o cron)
├── server.py             # Servidor de produção (waitress)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── MANUAL_SYNOLOGY.md    # Manual detalhado de deploy e operação no Synology
└── README.md
```

### Como o NAS é interpretado

Cada **subpasta de primeiro nível** dentro de `GAMES_ROOT` é uma **consola**.
Cada **item imediato** dentro dela (um ficheiro com extensão válida **ou** uma
pasta) é um **jogo**:

```
/volume1/jogos/
├── Nintendo Switch/
│   ├── Super Mario Odyssey.nsp        ← jogo
│   └── Zelda BOTW.xci                 ← jogo
├── PS2/
│   └── Shadow of the Colossus.iso     ← jogo
└── Xbox 360/
    └── Halo 3/                        ← jogo (pasta)
        └── default.xex
```

O **ID** de cada jogo é um hash estável de `consola + nome do ficheiro` (não do
caminho físico), por isso o catálogo sobrevive a mudanças de `volumeUSBx` quando
voltas a ligar um USB.

### Consolas em volumes/caminhos diferentes (ex: USB shares)

Se as consolas não estão sob uma raiz comum (ex: `/volumeUSB6/usbshare/SWITCH GAMES`
e `/volumeUSB3/usbshare/XBOX 360 (GAMES)`), há duas formas:

**Opção A (recomendada, só `docker-compose.yml`):** monta cada origem como
`/games/<NomeDaConsola>`. O último segmento define o nome no portal, o que também
permite limpar nomes feios:

```yaml
volumes:
  - "/volumeUSB6/usbshare/SWITCH GAMES:/games/Nintendo Switch:ro"
  - "/volumeUSB3/usbshare/XBOX 360 (GAMES):/games/Xbox 360:ro"
  - /volume1/docker/game-catalog/data:/data
```

Não é preciso código adicional: `GAMES_ROOT` continua a ser `/games`.

**Opção B (mapeamento explícito, serve Docker e nativo):** define `GAME_SOURCES`
com pares `Consola=Caminho` (um por linha, ou separados por `;`). Tem prioridade
sobre `GAMES_ROOT`:

```yaml
environment:
  GAME_SOURCES: |
    Nintendo Switch=/games/switch
    Xbox 360=/games/xbox360
```

No modo nativo, no `.env`:
```
GAME_SOURCES="Nintendo Switch=/volumeUSB6/usbshare/SWITCH GAMES;Xbox 360=/volumeUSB3/usbshare/XBOX 360 (GAMES)"
```

> **Volumes offline:** se uma origem não existir no momento do scan (ex: USB
> desligado), é ignorada com um aviso e os seus jogos **não** são removidos do
> catálogo. Só se removem jogos de consolas que foram efetivamente analisadas.

---

## 2. Instalação — Opção A: Docker (recomendada)

O **Container Manager** (antigo Docker) está disponível no Package Center do DSM.

### Passos

1. Copia a pasta `game-catalog/` para o NAS, por exemplo para
   `/volume1/docker/game-catalog/`.
2. Cria a pasta de dados persistentes:
   ```bash
   mkdir -p /volume1/docker/game-catalog/data
   ```
3. (Opcional) Define a chave do SteamGridDB. Cria um ficheiro `.env` ao lado do
   `docker-compose.yml`:
   ```
   STEAMGRIDDB_API_KEY=a_tua_chave
   ```
4. Confirma no `docker-compose.yml` que os volumes apontam para as tuas pastas
   reais. Por omissão:
   - `/volume1/jogos` → `/games` (só-leitura)
   - `/volume1/docker/game-catalog/data` → `/data` (BD + capas)
5. Constrói e arranca:
   ```bash
   cd /volume1/docker/game-catalog
   sudo docker compose up -d --build
   ```
   > Em DSM mais antigos pode ser `docker-compose` (com hífen).

6. Abre no browser, dentro da rede local:
   ```
   http://IP-DO-NAS:8088
   ```

7. Carrega em **Fazer scan** para popular o catálogo.

### Atualizar

```bash
cd /volume1/docker/game-catalog
sudo docker compose up -d --build
```

---

## 3. Instalação — Opção B: Nativa (sem Docker)

Útil se preferires não usar contentores. Requer Python 3 (o DSM traz o pacote
**Python 3** no Package Center).

```bash
# 1. Copiar o projeto, p.ex. para /volume1/web/game-catalog
cd /volume1/web/game-catalog

# 2. Criar ambiente virtual e instalar dependências
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt

# 3. Configurar (copiar e editar o exemplo)
cp .env.example .env
#   edita GAMES_ROOT, DATA_DIR e STEAMGRIDDB_API_KEY

# 4. Exportar as variáveis e arrancar
export $(grep -v '^#' .env | xargs)
python3 server.py
```

Fica acessível em `http://IP-DO-NAS:8088`.

### Arrancar automaticamente no boot (nativo)

No DSM: **Painel de Controlo → Tarefas Agendadas → Criar → Tarefa Acionada →
Arranque**, com utilizador `root` e o comando:

```bash
cd /volume1/web/game-catalog && . venv/bin/activate && \
export $(grep -v '^#' .env | xargs) && \
nohup python3 server.py >> /volume1/web/game-catalog/server.log 2>&1 &
```

---

## 4. Configuração (variáveis de ambiente)

| Variável               | Por omissão           | Descrição                                            |
|------------------------|-----------------------|------------------------------------------------------|
| `GAMES_ROOT`           | `/volume1/jogos`      | Pasta-raiz das consolas (`/games` em Docker)         |
| `GAME_SOURCES`         | (vazio)               | Pares `Consola=Caminho` p/ volumes diferentes; tem prioridade sobre `GAMES_ROOT` |
| `DATA_DIR`             | `./data`              | Pasta da BD e das capas (`/data` em Docker)          |
| `DB_PATH`              | `DATA_DIR/catalog.db` | Caminho do ficheiro SQLite                           |
| `THUMBS_DIR`           | `DATA_DIR/thumbnails` | Pasta onde se guardam as capas                       |
| `GAME_EXTENSIONS`      | (lista de ROMs/ISOs)  | Extensões consideradas jogo, separadas por vírgula   |
| `STEAMGRIDDB_API_KEY`  | (vazio)               | Chave para descarregar capas. Sem ela, não há capas. |
| `TWITCH_CLIENT_ID`     | (vazio)               | Client ID da app Twitch, para metadados via IGDB     |
| `TWITCH_CLIENT_SECRET` | (vazio)               | Client Secret da app Twitch (IGDB)                   |
| `PORT`                 | `8088`                | Porta do servidor web                                |

**Capas (SteamGridDB):** chave gratuita em
<https://www.steamgriddb.com/profile/preferences/api>.

**Metadados — ano, género e descrição (IGDB):** cria uma aplicação em
<https://dev.twitch.tv/console/apps> (OAuth Redirect URL pode ser
`http://localhost`) e copia o **Client ID** e **Client Secret** para
`TWITCH_CLIENT_ID` / `TWITCH_CLIENT_SECRET`. O IGDB é gratuito para uso
não-comercial.

Ambos são opcionais e independentes: sem credenciais, o portal funciona na mesma
e podes preencher tudo à mão na página de edição. **Importante:** os metadados do
IGDB só preenchem campos que estejam *vazios* — as tuas correções manuais nunca
são sobrepostas por um scan seguinte. O matching é por nome (vindo do nome do
ficheiro), por isso nomes limpos dão melhores resultados.

---

## 5. Agendar scans automáticos

### Em Docker — via Tarefas Agendadas do DSM (recomendado)

**Painel de Controlo → Tarefas Agendadas → Criar → Tarefa Agendada → Script
definido pelo utilizador.** Utilizador `root`, agenda (p.ex. diária às 04:00),
e no separador *Tarefa* o comando:

```bash
docker exec game-catalog python3 scan.py
```

(Usa `--no-cover` se quiseres saltar a procura de capas: `... scan.py --no-cover`.)

### Nativo — via cron / Tarefas Agendadas do DSM

Mesmo procedimento, mas o comando é:

```bash
cd /volume1/web/game-catalog && . venv/bin/activate && \
export $(grep -v '^#' .env | xargs) && python3 scan.py
```

### Cron clássico (alternativa por SSH)

```bash
# editar o crontab do root
sudo crontab -e

# scan diário às 04:00 (Docker)
0 4 * * * docker exec game-catalog python3 /app/scan.py >> /volume1/docker/game-catalog/scan.log 2>&1
```

> No Synology, prefere as **Tarefas Agendadas** do DSM em vez de editar o crontab
> à mão: o DSM reescreve o crontab e pode apagar entradas manuais.

O scan também pode ser disparado a qualquer momento pelo botão **Fazer scan** no
portal (corre em segundo plano, com bloqueio para evitar dois scans simultâneos).

---

## 6. Gerir o catálogo: eliminar entradas e logótipos

### Eliminar um jogo ou uma consola

A eliminação remove do **catálogo** (entrada na base de dados + capa gerada).
**Nunca apaga os ficheiros no NAS.**

- **Um jogo:** abre o jogo → *Editar metadados* → *Remover do catálogo*.
- **Uma consola inteira:** entra na consola → *Eliminar consola* (no canto
  superior). Remove todos os jogos dessa consola e o respetivo logótipo.

**Caso típico — caminho escaneado por engano:** como o scanner só remove jogos
de consolas que voltou a analisar, retirar o caminho errado da configuração
*não* limpa sozinho os jogos que ele criou. O procedimento correto é:

1. Corrige/retira o caminho errado do `docker-compose.yml` ou de `GAME_SOURCES`.
2. Usa *Eliminar consola* para apagar as entradas órfãs do catálogo.

> Nota: se eliminares um jogo cujo ficheiro ainda existe **e** a origem continua
> a ser analisada, ele volta a aparecer no próximo scan (é o comportamento
> esperado). A eliminação serve sobretudo para órfãos e enganos.

### Logótipos das consolas

No dashboard, cada consola mostra um logótipo. Se não houver, aparece um
monograma com uma cor própria (derivada do nome), por isso fica sempre
apresentável.

Para definir um logótipo: entra na consola → *Logótipo…* e escolhe uma imagem
(`png`, `jpg`, `webp` ou `svg`, até 4 MB). Em alternativa, podes colocar o
ficheiro diretamente em `…/data/logos/` com o nome da consola
(ex: `Nintendo Switch.png`).

> Os logótipos não são fornecidos pela aplicação (são marcas registadas);
> usa imagens que tenhas o direito de utilizar.

## 7. Notas de desempenho (DS220+)

- O **waitress** usa apenas 2 threads e não faz `fork`, mantendo o uso de RAM baixo.
- O SQLite corre em **WAL**, permitindo ler no browser enquanto o scan escreve.
- A procura de capas (rede) corre **fora** da transação principal, para não
  bloquear a base de dados.
- A pasta dos jogos é montada **só-leitura** em Docker — o portal nunca altera
  os teus ficheiros.

## 8. Trocar de fornecedor de capas

Toda a lógica está em `app/metadata.py`. Para usar IGDB ou TheGamesDB, basta
reimplementar `fetch_cover_bytes(title)` para devolver `(bytes_da_imagem, ".jpg")`
— o resto (gravação, associação ao jogo) continua igual.
