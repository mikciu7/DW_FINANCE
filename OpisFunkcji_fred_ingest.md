🏗️ Modular FRED Data Pipeline (OOP)
Ten projekt to modułowy system ETL do pobierania danych makroekonomicznych z FRED API i składowania ich w Data Lake na AWS S3 (warstwa Bronze).

Projekt został przepisany na architekturę obiektową (OOP), aby umożliwić łatwą orkiestrację (np. przez Apache Airflow lub AWS Glue) i separację logiki pobierania (Extract) od logiki zapisywania (Load).

🧩 Architektura Systemu
System składa się z dwóch niezależnych klas ("klocków") oraz skryptu orkiestrującego:

FredIngestor (The Worker):

Odpowiedzialny wyłącznie za komunikację z FRED API.

Nie łączy się z S3. Działa "w pamięci".

Pobiera dane i magazynuje je w wewnętrznych buforach (daily, monthly, quarterly).

Obsługuje pobieranie konkretnych serii oraz masowe pobieranie całych kategorii (Bulk).

S3DataHandler (The Courier):

Odpowiedzialny wyłącznie za bezpieczny transport danych na S3.

Nie wie, skąd pochodzą dane (FRED, Yahoo, Edgar) - musimy mu to podać jako source.

Zapisuje dane w ustandaryzowanej strukturze: bronze/{source}/{frequency}/{id}.csv.

Posiada mechanizm fallback – w razie awarii S3 zapisuje dane lokalnie.

⚙️ Wymagania i Konfiguracja
1. Instalacja Zależności
Uruchom w terminalu (lokalnie lub AWS CloudShell):

Bash

pip install --user pandas fredapi boto3 python-dotenv
2. Plik .env (Sekrety)
Utwórz plik .env w głównym katalogu projektu i dodaj swój klucz API:

Ini, TOML
FRED_API_KEY="twoj_klucz_api_fred"
Lub po prostu tworząc istancje klasy FredIngestor podaj mu wprot swój klucz API

🚀 Jak używać? 
Potem w dalszej czesci projektu bedziemy mieli jakis zautomatyzowany skrypt albo kilka skryptow ktore beda tworzyc sobie po prostu instancje obiektu i pobierac wszystkie dane dla obecnych dat itd. i w nim bedzie wszystko ulozone

📂 Struktura Danych na S3
Po uruchomieniu pipeline'u, dane zostaną automatycznie posortowane w wiadrze S3 według następującego schematu:

Plaintext

s3://neo-eye/
|-- bronze/
|   |-- fred/
|       |-- daily/
|       |   |-- DGS10.csv
|       |   |-- T10Y2Y.csv
|       |
|       |-- monthly/
|       |   |-- UNRATE.csv
|       |   |-- CPIAUCSL.csv
|       |
|       |-- quarterly/
|           |-- GDP.csv
📘 Dokumentacja Klas
Klasa FredIngestor
Główne metody do użycia w orkiestratorze:

ingest_daily_data(series_list, start, end) - pobiera listę serii dziennych.

ingest_monthly_data(series_list, start, end) - pobiera listę serii miesięcznych.

ingest_quarterly_data(series_list, start, end) - pobiera listę serii kwartalnych.

ingest_category_bulk(category_id, freq, start, end, limit) - automatycznie znajduje i pobiera najpopularniejsze serie z danej kategorii.

Gettery (do wyciągania danych):

get_daily_data()

get_monthly_data()

get_quarterly_data()

Klasa S3DataHandler
Główna metoda:

save_data(data, source_name, frequency, file_name) - uniwersalna metoda zapisu. Automatycznie konwertuje dane do CSV i wysyła na S3. Jeśli S3 jest niedostępne, tworzy lokalny backup.

💡 Wskazówki 
Aktualizacja danych: System działa w trybie nadpisywania. Jeśli pobierzesz dane z nowszą datą dla tej samej serii (np. UNRATE), stary plik na S3 zostanie zastąpiony nowym, zaktualizowanym plikiem CSV.

Nowe źródła: Aby dodać np. Yahoo Finance, wystarczy stworzyć nową klasę YahooIngestor działającą na podobnej zasadzie co FredIngestor i wykorzystać istniejący S3DataHandler do zapisu.

Kategorie FRED: Przydatne ID kategorii do metody BULK:

22 - Stopy procentowe (Interest Rates)

9 - Inflacja CPI (Consumer Price Indexes)

32447 - Bezrobocie (Unemployment)

18 - PKB (National Accounts)

# TODO 
Z racji, ze nie mozemy pobrac wszystkich danych naraz i ich spakowac bo to blokuje nasze konto z darmowym API, trzeba do bronze pobierac dane w pojedynczych plikach dla danej zmiennej makroekonomicznej. I po prostu z taka sama czestotliwoscia jak bedziemy aktualizowac sobie dane, albo bedziemy mieli wszystkie dane ktore nas interesuja. Ustawimy sobie na bronze/fred trigger. I on z kazda aktualizacja ktoregokolwiek z plikow bedzie przechodzic po wszystkich plikach i bedzie robic join tych danych po dacie i tworzyc kolumny w jednym pliku oczyszczonym wstepnie w silver, taki plik bedzie sie nazywac. np. fred_daily_data_base.csv i zawierac zlaczone dane z folderu daily freda. - Trzeba bedzie zrobic skrypt i klase do czyszczenia takich plikow ze zlaczymi danymi przed wrzuceniem ich na silver i zaharmonogramowac taki skrypt.