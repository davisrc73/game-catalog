# 🎮 Catálogo de Jogos — Manual de Operação e Guia de Deploy (Synology NAS)

Este documento reúne todas as informações práticas para instalar, gerir, atualizar e agendar o **Catálogo de Jogos** alojado no seu **Synology DS220+** (ou qualquer modelo com DSM 7+ e Container Manager / Docker).

---

## 🌐 1. Acesso à Aplicação e Serviços

- **Portal Web (Catálogo)**: `http://<IP_DO_SEU_NAS>:8088`
- **API de Estado**: `http://<IP_DO_SEU_NAS>:8088/api/status`
- **Base de Dados**: SQLite em modo WAL localizada internamente em `/data/catalog.db` (sem servidor externo)
- **Armazenamento de Capas e Logótipos**: Guardados localmente em `/data/thumbnails` e `/data/logos`

---

## 📁 2. Estrutura de Pastas e Volumes no Synology

Para manter o catálogo persistente e seguro, a estrutura recomendada no NAS é:

```text
/volume1/docker/game-catalog/
├── data/                       # Dados persistentes (base de dados SQLite, capas e logos)
│   ├── catalog.db
│   ├── thumbnails/
│   └── logos/
├── .env                        # Chaves de API e configurações locais
├── docker-compose.yml
└── ... (código da aplicação clonado via Git)
```

### Origem dos Jogos
Os ficheiros de jogos podem residir na pasta partilhada principal ou em discos externos USB:
- **Pasta interna partilhada:** `/volume1/jogos` montada em `/games:ro`
- **Discos externos USB:** Montados diretamente sob `/games/<NomeDaConsola>:ro` (ex: `/volumeUSB6/usbshare/SWITCH GAMES:/games/Nintendo Switch:ro`)

> 🔒 **Segurança Garantida:** Todos os volumes de jogos são montados como **apenas-leitura** (`:ro`). A aplicação nunca apaga nem modifica os ficheiros das suas ROMs/ISOs no NAS.

---

## 🚀 3. Instalação Inicial Passo a Passo (via Terminal SSH)

### Passo 1: Aceder ao NAS por SSH
Abra o Terminal no Mac e ligue-se ao Synology:
```bash
ssh utilizador_admin@<IP_DO_SEU_NAS>
```

### Passo 2: Criar a pasta base e clonar o repositório
```bash
# Entrar na pasta do Docker
cd /volume1/docker

# Clonar o repositório do GitHub
git clone https://github.com/davisrc73/game-catalog.git

# Entrar na pasta do projeto
cd /volume1/docker/game-catalog

# Criar a pasta de dados persistentes
mkdir -p data
```

### Passo 3: Configurar o ficheiro `.env`
Copie o modelo de configuração e edite com as suas chaves (opcionais):
```bash
cp .env.example .env
nano .env
```

*(Preencha a `STEAMGRIDDB_API_KEY` para capas automáticas e `TWITCH_CLIENT_ID`/`TWITCH_CLIENT_SECRET` para metadados via IGDB).*

### Passo 4: Ajustar os caminhos no `docker-compose.yml`
Verifique se os volumes correspondem à sua organização no NAS:
```bash
nano docker-compose.yml
```
*(Confirme se os pontos de montagem dos jogos apontam para os caminhos reais do seu NAS).*

### Passo 5: Compilar e Iniciar os Contentores
```bash
sudo docker compose up -d --build
```

Aceda de seguida no seu navegador a: `http://<IP_DO_SEU_NAS>:8088`.

---

## 🔄 4. Ciclo de Atualização e Desenvolvimento

Sempre que forem feitas alterações, correções ou novas funcionalidades:

### No Mac:
```bash
# 1. Adicionar e comitar as alterações
git add .
git commit -m "feat: nova melhoria"

# 2. Enviar para o GitHub
git push origin main
```

### No Synology NAS (via Terminal SSH):
```bash
# 1. Entrar na pasta do projeto
cd /volume1/docker/game-catalog

# 2. Puxar as atualizações do GitHub
git pull origin main

# 3. Reconstruir e reiniciar o contentor (sem cache para garantir atualização)
sudo docker compose build --no-cache
sudo docker compose up -d
```

---

## ⏰ 5. Agendamento de Scans Automáticos no DSM

Para que o catálogo detete novos jogos automaticamente (por exemplo, todas as noites às 04:00), configure uma tarefa no DSM:

1. No DSM, aceda a: **Painel de Controlo > Tarefas Agendadas**.
2. Clique em: **Criar > Tarefa Agendada > Script definido pelo utilizador**.
3. No separador **Geral**:
   - Nome da Tarefa: `Game Catalog - Scan Diário`
   - Utilizador: `root`
4. No separador **Agendamento**:
   - Configure a frequência desejada (ex: Diariamente às `04:00`).
5. No separador **Definições da Tarefa**, insira o comando:
   ```bash
   docker exec game-catalog python3 scan.py
   ```
   *(Caso pretenda saltar o download de capas e apenas sincronizar novos ficheiros, utilize `docker exec game-catalog python3 scan.py --no-cover`)*.

---

## 🛠️ 6. Comandos Úteis de Gestão no Synology

Todos os comandos devem ser executados em `/volume1/docker/game-catalog`:

### Estado e Logs
```bash
# Ver estado do contentor
sudo docker compose ps

# Ver logs em tempo real
sudo docker compose logs -f

# Ver as últimas 50 linhas de log
sudo docker compose logs --tail=50
```

### Parar / Reiniciar o Serviço
```bash
# Reiniciar o catálogo
sudo docker compose restart

# Parar o serviço
sudo docker compose down

# Iniciar em segundo plano
sudo docker compose up -d
```

### Disparar um Scan Manual via Terminal
```bash
# Scan completo com procura de capas
sudo docker compose exec game-catalog python3 scan.py

# Scan rápido sem consulta de capas
sudo docker compose exec game-catalog python3 scan.py --no-cover
```

---

## 💾 7. Cópias de Segurança (Backup & Restauro)

Toda a informação do catálogo reside na pasta `data/`:
* Base de dados: `data/catalog.db`
* Capas: `data/thumbnails/`
* Logótipos: `data/logos/`

### Criar um Backup Rápido
```bash
cd /volume1/docker/game-catalog
tar -czvf backup_catalogo_$(date +%Y%m%d_%H%M%S).tar.gz data/
```

### No Hyper Backup do DSM:
Inclua a pasta `/volume1/docker/game-catalog/data` na sua rotina habitual de backups para proteção total contra falhas de disco.

---

## 🔒 8. Acesso Externo Seguro (HTTPS via Synology Reverse Proxy)

Se quiser aceder à sua biblioteca fora de casa de forma segura:

1. No DSM: **Painel de Controlo > Portal de Início de Sessão > Avançadas > Proxy Inverso**.
2. Clique em **Criar**:
   - **Nome da Regra**: `Game Catalog`
   - **Origem**:
     - Protocolo: `HTTPS`
     - Nome do Host: `jogos.oseudominio.synology.me`
     - Porta: `443`
     - Ativar HSTS: Marcado
   - **Destino**:
     - Protocolo: `HTTP`
     - Nome do Host: `localhost`
     - Porta: `8088`
3. Em **Painel de Controlo > Segurança > Certificado**, associe o seu certificado Let's Encrypt a esta regra.

---

## ⚡ 9. Resolução de Problemas Frequentes

| Situação | Causa Provável | Solução |
| :--- | :--- | :--- |
| **Jogos de um disco USB não aparecem** | O disco foi ligado com um nome de partilha diferente (ex: `volumeUSB2` vs `volumeUSB3`). | Ajuste o caminho em `volumes:` no `docker-compose.yml` e execute `sudo docker compose up -d`. O catálogo não perde os dados anteriores. |
| **Erro de permissão a gravar capa/BD** | A pasta `data` no NAS não tem permissões de escrita para o utilizador do Docker. | Execute no NAS: `sudo chmod -R 775 /volume1/docker/game-catalog/data`. |
| **Capas não são descarregadas** | `STEAMGRIDDB_API_KEY` ausente ou inválida no `.env`. | Obtenha uma chave gratuita em [steamgriddb.com](https://www.steamgriddb.com) e adicione ao `.env`. Reinicie com `sudo docker compose restart`. |
| **Dois scans em simultâneo** | O utilizador carregou no botão enquanto corria o scan agendado. | O sistema possui bloqueio atómico (`_scan_lock`), ignorando automaticamente o segundo pedido sem corromper dados. |
