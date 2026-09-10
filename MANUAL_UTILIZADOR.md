# 📖 Manual do Utilizador: Catálogo de Jogos para Synology NAS

Bem-vindo ao **Manual do Utilizador** do Catálogo de Jogos. Este guia foi elaborado para te ajudar a tirar o máximo partido de todas as funcionalidades da aplicação no teu dia a dia, desde a organização e pesquisa de jogos até à gestão de capas e definições avançadas.

---

## 📑 Índice
1. [Acesso à Aplicação](#1-acesso-à-aplicação)
2. [Ecrã Inicial e Navegação](#2-ecrã-inicial-e-navegação)
3. [Pesquisa de Jogos](#3-pesquisa-de-jogos)
4. [Sistema de Favoritos ⭐](#4-sistema-de-favoritos-)
5. [Sorteador de Jogos Aleatórios 🎲](#5-sorteador-de-jogos-aleatórios-)
6. [Ficha de Detalhe e Edição de Jogos](#6-ficha-de-detalhe-e-edição-de-jogos)
7. [Gestão de Capas e Logótipos](#7-gestão-de-capas-e-logótipos)
8. [Sincronização e Scan de Pastas](#8-sincronização-e-scan-de-pastas)
9. [Painel de Definições do Sistema ⚙️](#9-painel-de-definições-do-sistema-️)
10. [Dicas e Boas Práticas](#10-dicas-e-boas-práticas)

---

## 1. Acesso à Aplicação

O Catálogo de Jogos funciona diretamente através do teu navegador de internet (no computador, portátil, tablet, telemóvel ou até na Smart TV), desde que o dispositivo esteja ligado à mesma rede local do teu Synology NAS.

* **Endereço no navegador:**
  ```text
  http://IP-DO-TEU-NAS:8088
  ```
  *(Substitui `IP-DO-TEU-NAS` pelo endereço IP local do Synology, por exemplo: `http://192.168.1.100:8088`)*

---

## 2. Ecrã Inicial e Navegação

Ao entrares no catálogo, encontras:

* **Barra Superior Fixa:**
  * **Logótipo/Home:** Clicar em `▚ Catálogo/NAS` regressa imediatamente ao ecrã inicial.
  * **Barra de Pesquisa:** Caixa de texto central para procurar jogos em toda a biblioteca.
  * **Botão `🎲 Aleatório`:** Sorteia e abre de imediato um jogo ao acaso.
  * **Botão `Fazer scan`:** Sincroniza o catálogo com as pastas e discos do NAS.
  * **Ícone `⚙️`:** Acesso rápido à área de Definições do Sistema e diagnósticos.
* **Resumo de Estatísticas:**
  * Apresenta o número total de jogos, consolas registadas, jogos com capa e o total de favoritos.
  * **Dica:** Clicar no bloco **`⭐ X favoritos`** filtra imediatamente a biblioteca para mostrar apenas os teus jogos favoritos.
* **Grelha de Consolas:**
  * Cada cartão representa uma plataforma (ex: *Nintendo Switch*, *Xbox 360*, *PlayStation 2*).
  * Mostra o logótipo da consola, a cor de destaque e a contagem de jogos armazenados.

---

## 3. Pesquisa de Jogos

A pesquisa foi desenvolvida para ser instantânea e inteligente:

### A. Pesquisa Instantânea (Live Search Dropdown)
* Basta começares a digitar na caixa de pesquisa no topo.
* Abre-se imediatamente um menu suspenso abaixo da barra com os jogos encontrados, as respetivas capas e a consola a que pertencem.
* Clicar em qualquer jogo desse menu abre a sua página de detalhe instantaneamente.
* Premir a tecla **`Escape`** ou clicar fora fecha o menu.

### B. Pesquisa Completa no Ecrã Inicial
* Podes escrever a tua pesquisa e carregar na tecla **`Enter`**.
* O ecrã inicial substitui a grelha de consolas pela grelha de jogos encontrados em todas as plataformas.
* **Sem preocupações com acentos:** Escrever `pokemon`, `pokémon` ou `POKEMON` devolve exatamente os mesmos resultados.
* **Pesquisa multi-palavra:** Podes combinar palavras soltas da consola e do título (ex: `switch mario` encontra os jogos de Mario na consola Switch).
* Para limpar a pesquisa e voltar às consolas, clica no botão **`✕`** dentro da caixa ou em **"Ver todas as consolas"**.

---

## 4. Sistema de Favoritos ⭐

Podes marcar os teus jogos de eleição para acesso rápido:

* **Como marcar nos cartões:** No canto superior direito da capa de qualquer jogo, existe uma estrela. Clicar nela ativa/desativa o favorito no mesmo segundo com um brilho âmbar retro e uma notificação de confirmação (*toast*).
* **Como marcar na página do jogo:** No ecrã de detalhe do jogo, existe um botão dedicado **`★ Favorito`** ao lado de "Editar metadados".
* **Separadores de Filtro:** Tanto no ecrã inicial como dentro de qualquer consola, existem botões de separador:
  * **`Todos os jogos`** — Mostra o catálogo completo.
  * **`⭐ Favoritos`** — Mostra apenas os jogos que marcaste com estrela.

---

## 5. Sorteador de Jogos Aleatórios 🎲

Se não sabes o que jogar a seguir, o catálogo escolhe por ti:

* **Sorteio em toda a biblioteca:** Clica no botão **`🎲 Aleatório`** na barra superior.
* **Sorteio dentro de uma consola:** Entra na consola desejada e clica no botão **`🎲 Aleatório`** no cabeçalho dessa consola.
* **Sorteio entre favoritos:** Se estiveres no separador **⭐ Favoritos**, o botão de sorteio escolhe exclusivamente de entre os jogos que marcaste como favoritos!

---

## 6. Ficha de Detalhe e Edição de Jogos

Ao clicares num jogo, acedes à sua ficha individual:

* **Informações apresentadas:** Capa em alta resolução, título, consola, ano de lançamento, género, descrição/sinopse, tamanho do ficheiro e o caminho real do ficheiro no NAS.
* **Editar Metadados:**
  * Clica no botão **"Editar metadados"**.
  * Podes corrigir o título, consola, ano, género ou sinopse.
  * Podes substituir a capa (ver secção seguinte).
  * Clica em **"Guardar alterações"**.
* **Remover do Catálogo:**
  * No fundo da página de edição, existe o botão vermelho **"Remover do catálogo"**.
  * **Importante:** Esta ação apenas remove o registo e a capa da base de dados do portal. **NUNCA apaga o ficheiro físico no teu NAS**.

---

## 7. Gestão de Capas e Logótipos

### A. Substituir a Capa de um Jogo
No ecrã de edição de um jogo, tens duas formas práticas:
1. **Ficheiro Local (Recomendado):** Clica em **"Escolher ficheiro"** e seleciona qualquer imagem guardada no teu telemóvel ou computador (`.png`, `.jpg`, `.jpeg`, `.webp`).
2. **Endereço Web (URL):** Cola o link direto de uma imagem da internet no campo de URL.
* **Nota de Proteção:** Sempre que defines uma capa manualmente, ela fica automaticamente **bloqueada/protegida** (`cover_locked`), o que garante que scans automáticos futuros nunca a irão substituir.

### B. Personalizar o Logótipo de uma Consola
* Entra na página da consola (ex: *PlayStation 2*).
* No topo direito, clica em **"Logótipo…"**.
* Seleciona uma imagem (PNG com fundo transparente é o ideal, SVG, WebP ou JPG). O logótipo é atualizado de imediato no cartão da consola.

---

## 8. Sincronização e Scan de Pastas

Sempre que adicionares ou removeres jogos do NAS ou das pens USB:

1. Clica no botão **`Fazer scan`** no canto superior direito.
2. O botão passa para o estado pulsante *"A analisar…"*.
3. Podes continuar a navegar normalmente enquanto o scan corre em segundo plano.
4. Quando terminar, surge uma mensagem de notificação com o resumo (novos jogos adicionados, atualizados ou removidos).

> **Segurança de Discos USB:** Se um dos teus discos externos USB for temporariamente desligado do NAS, o catálogo deteta que a origem está ausente e **não apaga** os jogos desse disco do catálogo! Só remove ficheiros de consolas cujo disco esteja efetivamente ligado e acessível.

---

## 9. Painel de Definições do Sistema ⚙️

Ao clicares no ícone **⚙️** no topo direito, acedes à central de controlo da aplicação:

### A. Integrações com APIs de Metadados
* **SteamGridDB (Capas Verticais):**
  * Insere a tua chave de API gratuita da SteamGridDB.
  * Clica em **"Testar ligação"** para verificar na hora se a chave está válida.
* **Twitch / IGDB (Sinopses, Anos e Géneros):**
  * Insere o *Client ID* e *Client Secret* da tua aplicação Twitch.
  * Clica em **"Testar ligação IGDB"** para validar a autenticação.
* **Etiquetas de Origem:** Os campos mostram se o valor está guardado na base de dados (`Definido na UI`) ou se veio do ficheiro de configuração (`Herdado do .env`).

### B. Comportamento do Scan
* **Descarregar capas automaticamente:** Ativa ou desativa a procura online de capas durante o scan.
* **Descarregar metadados do IGDB:** Ativa ou desativa a procura online de descrições e géneros.
* **Extensões de ficheiro reconhecidas:** Lista de formatos considerados jogos (`.nsp, .xci, .iso, .chd, .zip, etc.`). Podes adicionar formatos novos separando-os por vírgula.

### C. Diagnóstico de Volumes Montados
* Tabela que lista todos os discos e pastas de consolas configurados no Docker.
* **Indicador de estado:**
  * `🟢 Acessível` — A pasta está montada e pronta a ler jogos.
  * `🔴 Indisponível` — A pasta ou partição USB não está acessível no momento.
* Mostra a contagem em tempo real de jogos indexados por cada consola.

### D. Ferramenta de Manutenção de Capas
* Apresenta o tamanho da base de dados e o número de jogos que ainda não têm capa.
* Se existirem jogos sem capa, podes clicar no botão **"🎨 Procurar capas em falta"**: o sistema vai à internet procurar capas apenas para os jogos que precisam, sem teres de re-escanear todos os ficheiros do disco.

---

## 10. Dicas e Boas Práticas

1. **Adicionar ao Ecrã Principal do Telemóvel/Tablet:**
   * No Safari (iOS) ou Chrome (Android), clica em **Partilhar / Mais opções** e seleciona **"Adicionar ao Ecrã Principal"**. O catálogo passa a abrir como se fosse uma aplicação nativa de ecrã inteiro!
2. **Atualização de Estilos no Navegador:**
   * Se após uma atualização do sistema notares algo visualmente desalinhado, força a limpeza de cache da página premindo **`Cmd + Shift + R`** (no Mac) ou **`Ctrl + F5`** (no Windows).
3. **Ficheiros de Múltiplos Discos (CUE / BIN):**
   * Em jogos de PlayStation ou Saturn com ficheiros `.cue` e vários `.bin` (faixas de áudio), mantém os nomes base iguais. O catálogo agrupa tudo automaticamente e mostra apenas um único jogo limpo.
