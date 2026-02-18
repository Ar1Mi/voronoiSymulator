import matplotlib.pyplot as plt
import os

# Define Output Directory
# Navigate 2 levels up from runners to project root, then to tests/docs/TestResults_Manual/graphs
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
OUTPUT_DIR = os.path.join(ROOT_DIR, 'tests', 'docs', 'TestResults_Manual', 'graphs')

# Create Output Directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Data from REPORT.md
# Densities correspond to position1 (15), position2 (21), position3 (30)
densities = [15, 21, 30]

# Metrics
avg_ec = [0.0902, 0.0792, 0.0468]
avg_es = [0.2058, 0.1482, 0.2254]
avg_rank = [2.20, 2.00, 4.80]
avg_ea = [24.1048, 24.3290, 27.1945]
avg_relevance = [0.40, 0.40, 0.00]

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
    print("Generating Manual Test Analysis Graphs (Polish)...")
    
    # 1. Avg Ec
    plot_graph(densities, avg_ec, 'Średni błąd klasyfikacji ($E_c$) vs Gęstość', 'Średni $E_c$', 'Ec_vs_Density.png', color='orange', marker='s')
    
    # 2. Avg Es
    plot_graph(densities, avg_es, 'Średni błąd przeszukiwania ($E_s$) vs Gęstość', 'Średni $E_s$', 'Es_vs_Density.png', color='green', marker='^')
    
    # 3. Avg Rank
    plot_graph(densities, avg_rank, 'Średnia pozycja źródła (Rank) vs Gęstość', 'Średni Rank', 'Rank_vs_Density.png', color='purple', marker='d')
    
    # 4. Avg Ea
    plot_graph(densities, avg_ea, 'Średni błąd dokładności ($E_a$) vs Gęstość', 'Średni $E_a$ (px)', 'Ea_vs_Density.png', color='blue', marker='o')
    
    # 5. Avg Relevance (Optional, but included in data)
    plot_graph(densities, avg_relevance, 'Średnia relewancja vs Gęstość', 'Średnia Relewancja', 'Relevance_vs_Density.png', color='red', marker='x')
    
    print("All graphs generated successfully.")
