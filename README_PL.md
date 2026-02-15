# Voronoi Simulator V2 🌪️

[🇺🇸 English](README.md) | [🇵🇱 Polski](README_PL.md) | [🇷🇺 Русский](README_RU.md)

---

![Zrzut ekranu symulatora Voronoi](screenshot.png)

*> Zastąp ten tekst i plik `screenshot.png` rzeczywistym zrzutem ekranu aplikacji, aby użytkownicy mogli od razu zobaczyć, jak ona wygląda.*

## Opis

**Voronoi Simulator V2** to zaawansowany symulator diagramów Woronoja uwzględniający wpływ wiatru, opracowany w języku Python przy użyciu PyQt6. Projekt umożliwia modelowanie rozprzestrzeniania się stref wpływu czujników w warunkach oddziaływania czynników zewnętrznych.

### Główne funkcje:
*   🌌 **Generowanie diagramów Woronoja:** Klasyczne i ważone diagramy.
*   💨 **Symulacja wiatru:** Uwzględnianie prędkości i kierunku wiatru przy obliczaniu granic komórek.
*   📊 **Metryki i analiza:** Obliczanie Dokładności (Ec), Pokrycia (Ea) i Stabilności (Es).
*   🧪 **Testowanie:** Wbudowane narzędzia do ręcznego i automatycznego testowania hipotez.
*   📈 **Wizualizacja:** Interaktywne wyświetlanie wykresów i siatek w czasie rzeczywistym.

## Instalacja i uruchomienie 🚀

Do uruchomienia projektu wymagany jest Python 3.9+.

1.  **Sklonuj repozytorium:**
    ```bash
    git clone https://github.com/Ar1Mi/voronoiSymulator.git
    cd voronoiSymulator
    ```

2.  **Utwórz i aktywuj środowisko wirtualne (zalecane):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Dla macOS/Linux
    # lub
    .venv\Scripts\activate     # Dla Windows
    ```

3.  **Zainstaluj zależności:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Uruchom aplikację:**
    ```bash
    python main.py
    ```

## Struktura projektu 📂

*   `main.py` — Główny plik uruchomieniowy aplikacji.
*   `simulation.py` — Logika symulacji i obliczeń.
*   `ui/` — Interfejs użytkownika (PyQt6).
*   `tests/` — Testy jednostkowe i integracyjne.
*   `savedSymulations/` — Zapisane konfiguracje symulacji.

## Autor

Opracowano w ramach pracy dyplomowej.
