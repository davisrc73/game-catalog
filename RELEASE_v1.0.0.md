# 🎮 Notas de Lançamento: Catálogo de Jogos `v1.0.0`

**Data de Lançamento:** 10 de Setembro de 2026  
**Repositório:** [davisrc73/game-catalog](https://github.com/davisrc73/game-catalog)  
**Tag Oficial:** `v1.0.0`

---

## 📖 Visão Geral

A versão **`v1.0.0`** marca o primeiro lançamento oficial e estável do **Catálogo de Jogos para Synology NAS**. Trata-se de uma aplicação web autónoma e de baixo consumo de recursos, desenhada especificamente para organizar e navegar em bibliotecas de jogos guardadas em discos e pens USB no NAS (otimizada para o modelo **DS220+** e modelos ARM como o **DS220j**).

---

## 🌟 Principais Funcionalidades da v1.0.0

### 1. Indexação Inteligente e Suporte Multi-Volume
* **Estrutura por Consola:** Deteção automática das pastas de primeiro nível como consolas e o seu conteúdo como jogos.
* **Resiliência a Discos Externos:** Sobrevive a trocas de montagens USB (`/volumeUSBx`) através de hashes estáveis de identificação (`consola + caminho relativo`).
* **Proteção Offline:** Se um disco USB for temporariamente desligado, o scan ignora o volume sem apagar os jogos já catalogados.
* **Filtro CUE/BIN:** Deduplicação inteligente de faixas `.bin` quando existe um ficheiro `.cue` associado, evitando jogos duplicados na listagem.
* **Suporte a Pastas e Ficheiros:** Pastas com ficheiros internos de jogo (ex: Xbox 360 com `default.xex`) contam automaticamente como um único jogo.

---

### 2. Pesquisa Global em Tempo Real (Live Search)
* **Pesquisa Instantânea:** Dropdown reativo ao digitar na barra de pesquisa superior (com *debounce* de 150ms).
* **Insensibilidade a Acentos e Maiúsculas:** Função SQL customizada `norm()` que normaliza caracteres (ex: pesquisar "pokemon", "POKÉMON" ou "pokémon" devolve os mesmos resultados).
* **Pesquisa Multi-Termo:** Permite encontrar jogos cruzando palavras da consola e do título (ex: "switch mario").
* **Submissão HTML Nativa:** Fallback universal com tecla `Enter` para o ecrã inicial com resultados completos.

---

### 3. Sistema de Favoritos ⭐
* **Marcação Rápida:** Botão de estrela interativo com brilho âmbar retro no canto superior direito de cada capa.
* **Alternância AJAX:** Adiciona e remove dos favoritos com feedback por notificação *toast*, sem abrir a ligação do jogo.
* **Separadores de Filtro (*Tabs*):** Alternância com 1 clique entre "Todos os jogos" e "⭐ Favoritos" no ecrã inicial e em cada consola.
* **Estatísticas Clicáveis:** Contador de favoritos no cabeçalho que filtra diretamente a biblioteca.

---

### 4. Sorteador de Jogo Aleatório 🎲
* **Sorteio Global:** Botão `🎲 Aleatório` na barra superior para descobrir um jogo ao acaso de toda a biblioteca.
* **Sorteio por Consola:** Botão `🎲 Aleatório` dentro da página de cada consola.
* **Filtro com Favoritos:** Se acionado a partir do separador de favoritos, o sorteio incide exclusivamente sobre os jogos favoritos.

---

### 5. Gestão de Capas e Metadados
* **Upload Direto de Ficheiro Local:** Suporte a carregamento de imagens (`.png`, `.jpg`, `.jpeg`, `.webp`) diretamente do computador ou telemóvel no ecrã de edição.
* **Integração SteamGridDB:** Download automático de capas verticais oficiais no formato de grelha.
* **Integração Twitch / IGDB:** Obtenção automática de ano de lançamento, género e sinopse oficial.
* **Proteção Anti-Sobrecarga (`cover_locked`):** Capas alteradas manualmente ficam protegidas e nunca são substituídas por scans automáticos.
* **Segurança Anti-SSRF:** Validação rigorosa de URLs para prevenir ataques de falsificação de pedidos em rede interna.

---

### 6. Área de Definições Web (`/settings`) ⚙️
* **Prioridade em Cascata:** Chaves de API configuradas na interface web têm prioridade e são guardadas em SQLite na tabela `settings`. Se vazias, a aplicação usa automaticamente o valor do `.env`.
* **Testes de Ligação em Tempo Real:** Botões dedicados para validar chaves SteamGridDB e credenciais Twitch/IGDB com feedback imediato de erro ou sucesso.
* **Diagnóstico de Volumes:** Tabela que lista cada pasta montada no Docker, caminho no NAS, total de jogos e estado (`🟢 Acessível` / `🔴 Offline`).
* **Diagnóstico de Armazenamento:** Informação em tempo real do tamanho da base de dados e miniaturas em cache.
* **Ferramenta de Manutenção:** Botão para procurar capas em falta em segundo plano sem re-escanear ficheiros.

---

## 🏗️ Especificações Técnicas

| Componente | Tecnologia | Detalhes |
|---|---|---|
| **Linguagem** | Python 3.11 | Imagem base `python:3.11-slim` multi-arquitetura (ARM64 e x86_64) |
| **Servidor Web** | Waitress 3.0 | Puro Python, *thread-based*, sem fork, consumo mínimo de RAM |
| **Framework Web** | Flask 3.0 | Rotas REST, templates Jinja2 e API JSON |
| **Base de Dados** | SQLite 3 | Modo WAL (`Write-Ahead Logging`), migrações automáticas não-destrutivas |
| **Frontend** | HTML5 / CSS3 / Vanilla JS | Zero dependências externas (sem frameworks pesadas, funciona offline na LAN) |
| **Design** | Dark Arcade Theme | Tipografia Bricolage Grotesque, acentos âmbar neon e efeitos glassmorphism |

---

## 🧪 Cobertura de Testes Automatizados

A versão `v1.0.0` foi validada com uma suite de **15 testes unitários** automatizados:

1. `test_advanced_search`: pesquisa multi-palavra, cruzada e insensível a acentos.
2. `test_crud_games`: criação, leitura, atualização e eliminação de jogos.
3. `test_database_migration`: migração transparente de bases de dados legadas sem perda de dados.
4. `test_favorites_and_random`: alternância de favoritos, filtros combinados e sorteio aleatório.
5. `test_missing_covers_count`: contagem precisa de jogos sem capa.
6. `test_settings_and_cascade_config`: persistência em SQLite, resolução em cascata e reversão para `.env`.
7. `test_settings_route`: validação do endpoint web `/settings` com retorno `200 OK`.
8. `test_steamgriddb_validation`: validação de chaves ativas e rejeição de chaves inválidas.
9. `test_igdb_validation`: validação de credenciais Twitch/IGDB.
10. `test_is_safe_url`: prevenção de SSRF e bloqueio de IPs internos/privados.
11. `test_clean_title`: normalização e limpeza de nomes de ficheiros ROM.
12. `test_cue_bin_deduplication`: remoção de faixas redundantes BIN/CUE.
13. `test_initials_for`: geração de iniciais de consolas sem logótipo.
14. `test_safe_name`: sanitização de nomes de consolas para logótipos.
15. `test_accent_for_deterministic`: cores de destaque consistentes por consola.

---

## 🚀 Como Instalar ou Atualizar no Synology NAS

### Atualização para quem já tem o contentor a correr:

```bash
cd /volume1/docker/game-catalog
git pull origin main
sudo docker compose build --no-cache
sudo docker compose up -d
```

No browser, recarregue com **`Cmd + Shift + R`** (Mac) ou **`Ctrl + F5`** (Windows).

### Nova Instalação:

1. Clone o repositório no NAS:
   ```bash
   cd /volume1/docker
   git clone https://github.com/davisrc73/game-catalog.git
   cd game-catalog
   mkdir -p data
   ```
2. Ajuste as pastas de jogos no [docker-compose.yml](file:///Users/daviscorreia/Antigravity%20/game-catalog/docker-compose.yml).
3. Inicie o contentor:
   ```bash
   sudo docker compose up -d --build
   ```
4. Aceda via browser a `http://IP-DO-NAS:8088`.
