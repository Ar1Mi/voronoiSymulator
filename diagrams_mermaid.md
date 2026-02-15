# Schema Struktury i Algorytmu Symulatora Voronoi

Poniżej znajdują się diagrama blokowa struktury projektu oraz schemat blokowy (FlowChart) algorytmu symulacji.

## 1. Diagram Blokowy Struktury Projektu (Block Diagram)

Przedstawia główne komponenty aplikacji i ich relacje.

```mermaid
flowchart TD
    subgraph EntryPoint ["Entry Point"]
        Main[main.py]
    end

    subgraph UI ["User Interface (UI)"]
        MW[MainWindow]
        CB[ControlsBuilder]
        GR[GridRenderer]
        GV[GridViewport]
        GIH[GridInputHandler]
        DD[DetailsDialog]
        Styles[styles.py]
    end

    subgraph LogicControl ["Logic & Control"]
        SC[SimulationController]
        Worker[SimulationWorker]
    end

    subgraph SimulationEngine ["Core Simulation Engine"]
        SM[SimulationManager]
    end

    subgraph DataModels ["Data Models"]
        Sensor[Sensor]
        Cell[Cell]
    end

    %% Relations
    Main -->|Initializes| MW
    MW -->|Uses| CB
    MW -->|Uses| GR
    MW -->|Uses| GV
    MW -->|Uses| GIH
    MW -->|Uses| SC
    MW -->|Uses| Styles
    MW -.->|Opens| DD

    GV -->|Renders using| GR
    GIH -->|Handles input for| MW

    SC -->|Manages| SM
    SC -->|Runs async tasks via| Worker
    Worker -->|Uses| SM

    SM -->|Manipulates| Cell
    SM -->|Tracks| Sensor
    
    Sensor -.->|Used in| Models[models.py]
    Cell -.->|Used in| Models
```

## 2. Schemat Blokowy Algorytmu (FlowChart)

Przedstawia logikę pojedynczego kroku symulacji (`next_step`), w tym mechanizm wzrostu i wpływu wiatru.

```mermaid
flowchart TD
    Start([Start Step]) --> InitGrid[Inicjalizacja nowej siatki - new_grid]
    InitGrid --> CalcWind[Oblicz wektor wiatru - Wind Offset]
    CalcWind --> SensorsLoop{Dla każdego sensora S}
    
    SensorsLoop -->|Koniec sensorów| ApplyCandidates[Zastosuj najlepszych kandydatów do new_grid]
    ApplyCandidates --> SaveStep[Zapisz krok w historii steps]
    SaveStep --> End([Koniec Kroku])

    SensorsLoop -->|Dla sensora S| IncRadius[Zwiększ promień: R = R + 1]
    IncRadius --> CalcEffCenter["Oblicz Efektywne Centrum (EffX, EffY)<br>(Pozycja + Wiatr)"]
    CalcEffCenter --> RangeLoop{Pętla po zasięgu -R, +R}
    
    RangeLoop -->|Koniec pętli zasięgu| SensorsLoop
    RangeLoop -->|Dla dx, dy| CheckCircle{Wewnątrz koła R?}
    
    CheckCircle -- Nie --> RangeLoop
    CheckCircle -- Tak --> CalcCoords[Oblicz współrzędne w siatce: nx, ny]
    
    CalcCoords --> CheckBounds{Czy nx, ny w granicach siatki?}
    CheckBounds -- Nie --> RangeLoop
    CheckBounds -- Tak --> CheckEmpty{Czy komórka była pusta<br>w poprzednim kroku?}
    
    CheckEmpty -- Nie (Zajęta) --> RangeLoop
    CheckEmpty -- Tak (Pusta) --> CalcDist["Oblicz odległość (D^2) od EffCenter"]
    
    CalcDist --> CompareCand{"Czy już jest kandydat<br>dla tej komórki?"}
    
    CompareCand -- Nie --> StoreCand[Zapisz kandydata: S, D^2]
    CompareCand -- Tak --> CheckBetter{"Czy nowy D^2 < Stary D^2?"}
    
    CheckBetter -- Tak (Lepszy) --> UpdateCand[Nadpisz kandydata: S, D^2]
    CheckBetter -- Nie (Gorszy) --> RangeLoop
    
    StoreCand --> RangeLoop
    UpdateCand --> RangeLoop

    subgraph ConflictResolution ["Resolving Conflicts (Voronoi Logic)"]
        CompareCand
        CheckBetter
        UpdateCand
    end
```
