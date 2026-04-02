# Środowisko dopasowane do Twojego lokalnego Pythona 3.11
FROM python:3.11-slim

# Ustawiamy katalog roboczy dla backendu
WORKDIR /app

# Instalujemy narzędzia systemowe niezbędne do skompilowania paczek ML i PostgreSQL
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Kopiujemy plik z listą paczek
COPY requirements.txt .

# Instalujemy paczki Pythona (--no-cache-dir zmniejsza wagę obrazu)
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy całą resztę kodu backendu
COPY . .

# Wystawiamy port, na którym nasłuchuje FastAPI
EXPOSE 8000

# Uruchamiamy serwer
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]