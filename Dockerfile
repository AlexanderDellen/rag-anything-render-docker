FROM python:3.11-slim

# Systempakete: LibreOffice für Office-Dokumente, poppler-utils/ghostscript für PDF-Hilfsfunktionen
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    poppler-utils \
    ghostscript \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# App-Verzeichnis
WORKDIR /app

# Python-Abhängigkeiten
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Code
COPY app.py /app/app.py

# Standard-Umgebungsvariablen
ENV WORKDIR=/data/rag_storage
ENV PYTHONUNBUFFERED=1

# Wichtig: $PORT von Render benutzen (Fallback 8080)
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]
