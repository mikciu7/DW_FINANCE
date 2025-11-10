# 📈 FRED Data Ingest - Początek Pipeline

Pythonowy skrypt służący do pobierania danych makroekonomicznych z [FRED API](https://fred.stlouisfed.org/docs/api/fred/) i ładowania ich bezpośrednio do warstwy `bronze` w Data Lake na AWS S3.

Skrypt jest parametryzowany i pozwala na pobieranie dowolnych serii danych w zadanym zakresie dat. Posiada również mechanizm *fallback* – jeśli zapis na S3 się nie powiedzie (np. z powodu braku uprawnień), zapisze pliki lokalnie w folderze `fred_local_data`.

## 1. Wymagania Wstępne

Zanim uruchomisz skrypt, upewnij się, że masz:

* **Klucz FRED API:** Musisz wygenerować swój własny, darmowy klucz API na stronie [FRED API](https://fred.stlouisfed.org/docs/api/api_key.html).
* **Konto AWS IAM:** Musisz posiadać konto użytkownika IAM na naszym głównym koncie AWS (z dostępem do konsoli).
* **Uprawnienia:** Twoja rola (lub użytkownik) musi mieć uprawnienia `s3:PutObject` do naszego wiadra S3 (`neo-eye`).

## 2. Konfiguracja Środowiska (AWS CloudShell)

Aby uniknąć problemów z kluczami AWS i zależnościami, **zawsze** uruchamiamy ten skrypt z **AWS CloudShell**.

1.  **Zaloguj się do AWS:** Zaloguj się na swoje konto IAM w konsoli AWS.
2.  **Uruchom CloudShell:** W prawym górnym rogu kliknij ikonę CloudShell (`>_`).
3.  **Pobierz kod:** Sklonuj to repozytorium do swojego CloudShell:
    ```bash
    git clone [https://github.com/TWOJA-ORGANIZACJA/NAZWA-REPO.git](https://github.com/TWOJA-ORGANIZACJA/NAZWA-REPO.git)
    cd NAZWA-REPO/
    ```
    ... Lub po prostu zrób ręczny update jednego pliku (ikonka z plusikiem po prawej stronie shella )...
4.  **Zainstaluj zależności:** Wymagane biblioteki Pythona instalujemy w folderze domowym użytkownika CloudShell (robisz to tylko raz):
    ```bash
    pip install --user boto3 pandas fredapi python-dotenv
    ```
5.  **Stwórz plik .env:** To najważniejszy krok. Skrypt szuka klucza API w pliku `.env`. Stwórz go:
    ```bash
    # Będąc w głównym folderze projektu
    nano/vim .env
    ```
    Do otwartego edytora wklej swój klucz API w następującym formacie:
    ```ini
    API_KEY="abcdef1234567890abcdef1234567890"
    ```
    Zapisz plik (w `nano`: **Ctrl+O**, Enter, **Ctrl+X**).

> **WAŻNE:** Plik `.env` jest ignorowany przez `.gitignore`. **Nigdy nie wrzucaj go na GitHuba ani nie kopiuj ręcznie na S3!** Jest bezpieczny tylko w Twoim prywatnym folderze domowym na CloudShell.

## 3. Użycie Skryptu

Skrypt uruchamiasz poleceniem `python`, podając trzy argumenty:

* `--series`: (Wymagane) Lista jednej lub więcej serii FRED oddzielonych spacją.
* `--start`: (Wymagane) Data początkowa w formacie `YYYY-MM-DD`.
* `--end`: (Wymagane) Data końcowa w formacie `YYYY-MM-DD`.

### Przykładowe wywołanie

Pobranie PKB, dochodu narodowego, CPI, aktywów Fed oraz długu publicznego z lat 2000-2025:

```bash

python fred_ingest.py --series GDP GNP CPIAUCSL WALCL GFDEBTN --start 2000-01-01 --end 2025-12-31