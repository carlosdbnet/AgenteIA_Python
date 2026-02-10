FROM python:3.10-slim

# Instala dependências de sistema (libmagic, ffmpeg e sqlite)
RUN apt-get update && apt-get install -y \
    libmagic1 \
    ffmpeg \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . .

# Garante que o Python não faça buffer dos logs
ENV PYTHONUNBUFFERED=1

# Comando para iniciar o bot
CMD ["python", "app/main.py"]
