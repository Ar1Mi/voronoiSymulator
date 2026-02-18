import matplotlib.pyplot as plt
import os
import sys

# Define Output Directory
# Navigate 2 levels up from runners to project root, then to tests/docs/density_graphs
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
OUTPUT_DIR = os.path.join(ROOT_DIR, 'tests', 'docs', 'density_graphs')

# Create Output Directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Data
# Data
densities = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
avg_ec = [0.3572, 0.2117, 0.1510, 0.1267, 0.0810, 0.0859, 0.0546, 0.0548, 0.0549, 0.0418, 0.0548, 0.0528, 0.0424, 0.0418, 0.0346, 0.0379, 0.0399, 0.0329, 0.0379, 0.0368]
avg_es = [0.6731, 0.5093, 0.5385, 0.5696, 0.4947, 0.5139, 0.4893, 0.5023, 0.4731, 0.5068, 0.4946, 0.5161, 0.4850, 0.4903, 0.4918, 0.5002, 0.4973, 0.5049, 0.4956, 0.4945]
avg_rank = [2.74, 3.58, 5.69, 9.14, 8.34, 9.75, 12.65, 13.83, 13.92, 19.16, 17.14, 21.15, 19.60, 22.11, 24.03, 25.53, 25.77, 29.16, 30.37, 31.52]
avg_ea = [34.7248, 43.3920, 47.9119, 48.1313, 35.2113, 37.4920, 35.4344, 36.4382, 36.4747, 38.2100, 38.6298, 39.3242, 39.4384, 38.2754, 37.2832, 38.6729, 38.4093, 38.6360, 40.6767, 38.9685]
avg_relevance = [0.40, 0.15, 0.09, 0.05, 0.21, 0.12, 0.13, 0.10, 0.10, 0.07, 0.08, 0.07, 0.05, 0.06, 0.06, 0.07, 0.07, 0.06, 0.05, 0.06]

def plot_graph(x, y, title, ylabel, filename, color='blue', marker='o'):
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, marker=marker, linestyle='-', color=color, label=ylabel)
    plt.title(title)
    plt.xlabel('Liczba czujników')
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.legend()
    
    # Save path
    save_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(save_path)
    plt.close()
    print(f"Graph saved: {save_path}")

if __name__ == "__main__":
    print("Generating Density Analysis Graphs...")
    
    # 1. Avg Ec
    plot_graph(densities, avg_ec, 'Średni błąd klasyfikacji ($E_c$) vs Gęstość', 'Średni $E_c$', 'Ev_vs_Density.png', color='orange', marker='s')
    
    # 2. Avg Es
    plot_graph(densities, avg_es, 'Średni błąd przeszukiwania ($E_s$) vs Gęstość', 'Średni $E_s$', 'Es_vs_Density.png', color='green', marker='^')
    
    # 3. Avg Rank
    plot_graph(densities, avg_rank, 'Średnia pozycja źródła (Rank) vs Gęstość', 'Średni Rank', 'Rank_vs_Density.png', color='purple', marker='d')
    
    # 4. Avg Ea
    plot_graph(densities, avg_ea, 'Średni błąd dokładności ($E_a$) vs Gęstość', 'Średni $E_a$ (px)', 'Ea_vs_Density.png', color='blue', marker='o')
    
    # 5. Avg Relevance
    plot_graph(densities, avg_relevance, 'Średnia relewancja vs Gęstość', 'Średnia Relewancja', 'Relevance_vs_Density.png', color='red', marker='x')
    
    print("All graphs generated successfully.")
