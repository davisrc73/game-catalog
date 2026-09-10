# Imagem leve e compatível com a CPU ARM64 (Realtek RTD1296) do DS220+
FROM python:3.11-slim

# Não gerar .pyc e não fazer buffer do stdout (logs imediatos)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependências primeiro (melhor cache de camadas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código
COPY app/ ./app/
COPY server.py scan.py ./

# Pasta de dados persistente (BD + capas). Será montada do NAS.
ENV DATA_DIR=/data
VOLUME ["/data"]

# A pasta dos jogos é montada como só-leitura em /games
ENV GAMES_ROOT=/games \
    DB_PATH=/data/catalog.db \
    THUMBS_DIR=/data/thumbnails \
    PORT=8088

EXPOSE 8088

CMD ["python3", "server.py"]
