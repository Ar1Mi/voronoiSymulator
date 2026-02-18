# Algorytm Generowania "Idealnych" Pozycji Sensorów (Centroidal Voronoi Tessellation)

W celu uzyskania maksymalnie równomiernego rozmieszczenia sensorów na ograniczonym obszarze symulacji (siatka 100x100), zastosowano algorytm relaksacji **Lloyda** (Lloyd's Algorithm). Metoda ta pozwala na wyznaczenie tzw. **Teselacji Voronoja z Centroidem** (Centroidal Voronoi Tessellation - CVT).

Jest to standardowa metoda służąca do optymalizacji rozmieszczenia punktów w przestrzeni, dążąca do minimalizacji wariancji odległości wewnątrz komórek Voronoja. W przestrzeni dwuwymiarowej prowadzi to do ułożenia zbliżonego do sieci heksagonalnej, która jest najgęstszym sposobem pakowania okręgów na płaszczyźnie.

## Opis Algorytmu

Algorytm działa w sposób iteracyjny:

1.  **Inicjalizacja**: Na początku $N$ sensorów jest rozmieszczanych w losowych punktach na płaszczyźnie siatki.
2.  **Wyznaczenie Obszarów Voronoja**: W każdym kroku iteracji, dla każdego punktu siatki (piksela) $(x, y)$ znajdowany jest najbliższy sensor. Zbiór wszystkich punktów przypisanych do danego sensora tworzy jego komórkę Voronoja $V_i$.
3.  **Obliczenie Centroidów**: Dla każdej komórki Voronoja obliczany jest jej środek ciężkości (centroid) $(C_x, C_y)$. W przestrzeni dyskretnej (siatka pikseli), centroid jest średnią arytmetyczną współrzędnych wszystkich punktów należących do danego obszaru:
    $$ C_x = \frac{\sum_{p \in V_i} x_p}{|V_i|}, \quad C_y = \frac{\sum_{p \in V_i} y_p}{|V_i|} $$
    Gdzie $|V_i|$ to liczba punktów (pole powierzchni) w komórce sensora $i$.
4.  **Aktualizacja Pozycji**: Każdy sensor jest przesuwany do nowo obliczonego centroidu swojego obszaru: $(S_x, S_y) \leftarrow (C_x, C_y)$.
5.  **Relaksacja**: Kroki 2-4 są powtarzane wielokrotnie (w zaimplementowanym skrypcie do 50 razy) lub do momentu konwergencji, gdy przesunięcia sensorów w kolejnych krokach spadną poniżej założonego progu (np. 0.1 jednostki).

## Uzasadnienie Wyboru

Zastosowanie CVT gwarantuje, że sensory rozkładają się w sposób "naturalnie" równomierny, unikając sztucznych artefaktów wynikających z prostego podziału siatki (np. sztywne rzędy i kolumny). Dzięki temu każdemu sensorowi przypada obszar o zbliżonej powierzchni i kształcie, co maksymalizuje pokrycie terenu przy zadanej liczbie czujników.
