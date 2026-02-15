# Voronoi Simulator V2 🌪️

![Voronoi Simulator Header](HeaderReadMe.png)

## Description

**Voronoi Simulator V2** is an advanced Voronoi diagram simulator that accounts for wind influence, developed in Python using PyQt6. The project allows for modeling the spread of sensor influence zones under external environmental conditions.

### Key Features:
*   🌌 **Voronoi Diagram Generation:** Classical and weighted diagrams.
*   💨 **Wind Simulation:** Accounts for wind speed and direction when calculating cell boundaries.
*   📊 **Metrics and Analysis:** Calculation of Accuracy (Ec), Coverage (Ea), and Stability (Es).
*   🧪 **Testing:** Built-in tools for manual and automated hypothesis testing.
*   📈 **Visualization:** Interactive display of graphs and grids in real-time.

## Installation and Usage 🚀

To run the project, you need Python 3.9+.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Ar1Mi/voronoiSymulator.git
    cd voronoiSymulator
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # For macOS/Linux
    # or
    .venv\Scripts\activate     # For Windows
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python main.py
    ```

## Project Structure 📂

*   `main.py` — Application entry point.
*   `simulation.py` — Simulation logic and calculations.
*   `ui/` — User Interface (PyQt6).
*   `tests/` — Unit and integration tests.
*   `savedSymulations/` — Saved simulation configurations.

## Author

Developed as part of a thesis project.
