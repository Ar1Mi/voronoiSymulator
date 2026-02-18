import matplotlib.pyplot as plt
import os
import re

# Paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
DOCS_DIR = os.path.join(ROOT_DIR, 'tests', 'docs', 'TestResultsMain_1-100_auto')
INPUT_FILE = os.path.join(DOCS_DIR, 'Density_Analysis.md')
OUTPUT_DIR = os.path.join(DOCS_DIR, 'density_graphs')

# Create Output Directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_markdown_table(file_path):
    data = {
        'density': [],
        'ec': [],
        'es': [],
        'rank': [],
        'ea': [],
        'relevance': []
    }
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # Find the table start
    table_start = False
    for line in lines:
        if '| Gęstość |' in line:
            table_start = True
            continue
        if table_start and '|---|' in line:
            continue
        if table_start and line.strip() == '':
            break # End of table
        
        if table_start and '|' in line:
            parts = [p.strip() for p in line.strip().split('|') if p.strip()]
            if len(parts) >= 6:
                try:
                    data['density'].append(int(parts[0]))
                    data['ec'].append(float(parts[1]))
                    data['es'].append(float(parts[2]))
                    data['rank'].append(float(parts[3]))
                    data['ea'].append(float(parts[4]))
                    data['relevance'].append(float(parts[5]))
                except ValueError as e:
                    print(f"Skipping line: {line.strip()} - Error: {e}")
                    
    return data

def plot_graph(x, y, title, ylabel, filename, color='blue', marker='o'):
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, marker=marker, linestyle='-', color=color, label=ylabel)
    plt.title(title)
    plt.xlabel('Liczba czujników') # Polish label for Density
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.legend()
    
    # Save path
    save_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(save_path)
    plt.close()
    print(f"Graph saved: {save_path}")

if __name__ == "__main__":
    print(f"Reading data from: {INPUT_FILE}")
    if not os.path.exists(INPUT_FILE):
        print(f"Error: File not found: {INPUT_FILE}")
        exit(1)
        
    data = parse_markdown_table(INPUT_FILE)
    
    if not data['density']:
        print("No data found in the file.")
        exit(1)
        
    print(f"Found {len(data['density'])} data points.")

    # 1. Avg Ec
    plot_graph(data['density'], data['ec'], 'Średni błąd klasyfikacji ($E_c$) vs Gęstość', 'Średni $E_c$', 'Ec_vs_Density.png', color='orange', marker='s')
    
    # 2. Avg Es
    plot_graph(data['density'], data['es'], 'Średni błąd przeszukiwania ($E_s$) vs Gęstość', 'Średni $E_s$', 'Es_vs_Density.png', color='green', marker='^')
    
    # 3. Avg Rank
    plot_graph(data['density'], data['rank'], 'Średnia pozycja źródła (Rank) vs Gęstość', 'Średni Rank', 'Rank_vs_Density.png', color='purple', marker='d')
    
    # 4. Avg Ea
    plot_graph(data['density'], data['ea'], 'Średni błąd dokładności ($E_a$) vs Gęstość', 'Średni $E_a$ (px)', 'Ea_vs_Density.png', color='blue', marker='o')
    
    # 5. Avg Relevance
    plot_graph(data['density'], data['relevance'], 'Średnia relewancja vs Gęstość', 'Średnia Relewancja', 'Relevance_vs_Density.png', color='red', marker='x')
    
    print("All graphs generated successfully.")
