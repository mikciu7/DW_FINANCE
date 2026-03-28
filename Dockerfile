# Używamy oficjalnego, lekkiego obrazu Pythona
FROM python:3.10-slim

# Ustawiamy katalog roboczy wewnątrz kontenera
WORKDIR /app

# Kopiujemy plik z listą paczek i instalujemy je
# (Robimy to najpierw, żeby Docker mógł skeszować ten krok i budować się szybciej w przyszłości)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy całą resztę kodu do kontenera
COPY . .

# Otwieramy port, na którym działa Uvicorn
EXPOSE 8000

# Komenda startowa
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]