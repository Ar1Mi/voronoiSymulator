import matplotlib.pyplot as plt
import os
import sys

# Define Output Directory
# Navigate 2 levels up from runners to project root, then to tests/docs/density_graphs
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
OUTPUT_DIR = os.path.join(ROOT_DIR, 'tests', 'docs', 'density_graphs')

# Create Output Directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_report_data(report_path):
    densities = []
    avg_ec = []
    avg_es = []
    avg_rank = []
    avg_ea = []
    avg_relevance = []
    
    with open(report_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    in_table = False
    for line in lines:
        if "## Summary Statistics" in line:
            in_table = True
            continue
        
        if in_table and line.strip().startswith('|') and "Config" not in line and "---" not in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 7:
                # | uniform_X_sensors | Sensors | Ec | Es | Rank | Ea | Rel | Count |
                # Index: 0=Name, 1=Sensors, 2=Ec, 3=Es, 4=Rank, 5=Ea, 6=Rel
                try:
                    s_count = int(parts[1])
                    ec = float(parts[2])
                    es = float(parts[3])
                    rank = float(parts[4])
                    ea = float(parts[5])
                    rel = float(parts[6])
                    
                    densities.append(s_count)
                    avg_ec.append(ec)
                    avg_es.append(es)
                    avg_rank.append(rank)
                    avg_ea.append(ea)
                    avg_relevance.append(rel)
                except ValueError:
                    continue
                    
    # Sort by density just in case
    data = sorted(zip(densities, avg_ec, avg_es, avg_rank, avg_ea, avg_relevance))
    if not data:
        return [], [], [], [], [], []
        
    return zip(*data)

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

def main():
    report_path = os.path.join(ROOT_DIR, 'tests', 'docs', 'REPORT_FULL.md')
    if not os.path.exists(report_path):
        print(f"Error: Report file not found at {report_path}")
        return

    densities, avg_ec, avg_es, avg_rank, avg_ea, avg_relevance = parse_report_data(report_path)
    
    if not densities:
        print("Error: No data found in report.")
        return

    print("Generating Density Analysis Graphs...")
    
    # 1. Avg Ec
    plot_graph(densities, avg_ec, 'Średni błąd klasyfikacji ($E_c$) vs Gęstość', 'Średni $E_c$', 'Ec_vs_Density.png', color='orange', marker='s')
    
    # 2. Avg Es
    plot_graph(densities, avg_es, 'Średni błąd przeszukiwania ($E_s$) vs Gęstość', 'Średni $E_s$', 'Es_vs_Density.png', color='green', marker='^')
    
    # 3. Avg Rank
    plot_graph(densities, avg_rank, 'Średnia pozycja źródła (Rank) vs Gęstość', 'Średni Rank', 'Rank_vs_Density.png', color='purple', marker='d')
    
    # 4. Avg Ea
    plot_graph(densities, avg_ea, 'Średni błąd dokładności ($E_a$) vs Gęstość', 'Średni $E_a$ (px)', 'Ea_vs_Density.png', color='blue', marker='o')
    
    # 5. Avg Relevance
    plot_graph(densities, avg_relevance, 'Średnia relewancja vs Gęstość', 'Średnia Relewancja', 'Relevance_vs_Density.png', color='red', marker='x')
    
    print("All graphs generated successfully.")

if __name__ == "__main__":
    main()
