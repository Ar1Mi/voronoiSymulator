
import sys
import os
import json
import csv
import math
import copy
import time
from PyQt6.QtWidgets import QApplication, QGraphicsScene
from PyQt6.QtCore import QSize, QRectF
from PyQt6.QtGui import QImage, QPainter, QColor

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(ROOT_DIR)

from simulation import SimulationManager
from models import Sensor
from ui.grid_renderer import GridRenderer
from ui.simulation_controller import SimulationController 

# Configuration - MODIFIED FOR DANE TESTS
TEST_DATA_DIR = os.path.join(ROOT_DIR, 'tests', 'data', 'data-manual-testing')
SAVED_SIM_DIR = os.path.join(ROOT_DIR, 'savedSymulations')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'TestResults_Dane')
REPORT_FILE = os.path.join(OUTPUT_DIR, 'REPORT.md')
GRID_WIDTH = 100
GRID_HEIGHT = 100

# Create Output Dir
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_sim_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_synchronous_weighted_sum(grid_width, grid_height, sensors, wind_dir, wind_str):
    """
    Replicates the logic of SimulationWorker for 'Suma Ważona' (Weighted Sum) mode.
    Returns: accumulated_grid (2D array of floats)
    """
    n_sensors = len(sensors)
    if n_sensors < 2:
        return []

    # Deep copy sensors to avoid modifying original
    sim_sensors = copy.deepcopy(sensors)
    
    # Sort sensors by pollution value (Cleanest to Dirtiest)
    clean_order = sorted(range(n_sensors), key=lambda k: sim_sensors[k].pollution_value)
    
    accumulated_grid = [[0.0 for _ in range(grid_width)] for _ in range(grid_height)]
    
    # Iterate cycles: i = number of clean sensors
    # Format: 1 clean, 2 clean ... n-1 clean
    for i in range(1, n_sensors):
        # Configure sensors
        num_clean = i
        clean_indices = set(clean_order[:num_clean])
        
        for idx, s in enumerate(sim_sensors):
            s.polluted = idx not in clean_indices
            s.radius = 0 # Reset radius
        
        # Create and Run Simulation
        sim = SimulationManager(grid_width, grid_height, sim_sensors, wind_dir, wind_str)
        # Run until stable
        # Max steps safety
        max_steps = grid_width + grid_height + 100
        
        for _ in range(max_steps):
            prev_grid = sim.steps[-1]
            sim.next_step()
            curr_grid = sim.steps[-1]
            
            # Check for changes
            has_changes = False
            for y in range(grid_height):
                for x in range(grid_width):
                    if prev_grid[y][x].status is None and curr_grid[y][x].status is not None:
                        has_changes = True
                        break
                if has_changes:
                    break
            
            if not has_changes:
                sim.steps.pop()
                break
        
        final_grid = sim.steps[-1]
        
        # Accumulate
        for y in range(grid_height):
            for x in range(grid_width):
                cell = final_grid[y][x]
                if cell.status == "polluted" and cell.polluted_by:
                    accumulated_grid[y][x] += cell.polluted_by.pollution_value

    return accumulated_grid

def calculate_wind_parameters(sensors, true_source_pos):
    """
    OVERRIDE: Hardcoded Wind Compensation.
    Returns: 220 degrees, 20% strength.
    """
    return 220, 20 

def process_data_files():
    # Helper to parse CSV (borrowed logic from SimulationController)
    controller = SimulationController(100, 100, [], 0, 0)
    
    # Initialize Report
    with open(REPORT_FILE, 'w', encoding='utf-8') as report:
        report.write("# Report of Automated Tests (Dane1-5, Position1-3)\n\n")
        report.write("> **Configuration**: Wind Compensation 220°, Strength 20% for ALL simulations.\n\n")

    # Files to process: Dane1.csv - Dane5.csv
    csv_files = [f"Dane{i}.csv" for i in range(1, 6)]
    
    # Summary Statistics Storage
    summary_stats = {} 
    
    # Configs to process: position1.json - position3.json
    config_files = ["position1.json", "position2.json", "position3.json"]
    all_configs_paths = [os.path.join(SAVED_SIM_DIR, f) for f in config_files]

    for csv_file in csv_files:
        csv_path = os.path.join(TEST_DATA_DIR, csv_file)
        if not os.path.exists(csv_path):
            print(f"Skipping {csv_file} (not found)")
            continue

        print(f"Processing {csv_file}...")
        
        with open(REPORT_FILE, 'a', encoding='utf-8') as report:
            report.write(f"## Data: {csv_file}\n\n")
        
        for config_path in all_configs_paths:
            if not os.path.exists(config_path):
                print(f"  Skipping config {config_path} (not found)")
                continue

            config_name = os.path.basename(config_path) # e.g. position1.json
            config_key = config_name.replace('.json', '')
            
            print(f"  Configuration: {config_name}")
            
            # Load Config
            sim_data = load_sim_config(config_path)
            grid_w = sim_data['grid']['width']
            grid_h = sim_data['grid']['height']
            
            # Setup Sensors from Config
            sensors = []
            for s_data in sim_data['sensors']:
                 sensors.append(Sensor(s_data['x'], s_data['y'], s_data['pollution_value']))
            
            sensor_count = len(sensors)
            
            # Init summary stats
            if config_key not in summary_stats:
                summary_stats[config_key] = {
                    'ec': [],
                    'ea': [],
                    'es': [],
                    'relevance': [],
                    'source_rank': [],
                    'sensor_count': sensor_count
                }

            # Setup Controller for Data Mapping
            controller.set_grid_size(grid_w, grid_h)
            controller.sensors = sensors
            
            # Import Data (Updates sensors and finds True Source)
            try:
                controller.import_csv_data(csv_path)
            except Exception as e:
                print(f"    Error importing CSV: {e}")
                continue
            
            true_source_pos = controller.true_source_pos
            
            # FORCED WIND CALCULATION
            wind_dir, wind_str = calculate_wind_parameters(controller.sensors, true_source_pos)
            
            # Run Weighted Sum Simulation
            accumulated_grid = run_synchronous_weighted_sum(grid_w, grid_h, controller.sensors, wind_dir, wind_str)
            
            # Calculate Metrics
            controller.update_wind(wind_dir, wind_str)
            controller.run() 
            metrics = controller.calculate_accuracy_metrics()
            
            if metrics:
                # Add to summary
                if metrics['ea'] is not None:
                     summary_stats[config_key]['ea'].append(metrics['ea'])
                summary_stats[config_key]['ec'].append(metrics['ec'])
                if metrics.get('es') is not None:
                     summary_stats[config_key]['es'].append(metrics['es'])
                
                if metrics.get('source_rank') is not None:
                     summary_stats[config_key]['source_rank'].append(metrics['source_rank'])
                     
                summary_stats[config_key]['relevance'].append(metrics['relevance'])

            # Write to Report
            with open(REPORT_FILE, 'a', encoding='utf-8') as report:
                report.write(f"### Configuration: {config_name}\n")
                if metrics:
                    es_val = metrics.get('es')
                    es_str = f"{es_val:.4f}" if es_val is not None else "N/A"
                    
                    rank = metrics.get('source_rank')
                    rank_str = str(rank) if rank is not None else "N/A"
                    
                    report.write(f"- **Ec**: {metrics['ec']:.4f}, **Es**: {es_str}, **Rank**: {rank_str}, **Ea**: {metrics['ea'] if metrics['ea'] is not None else 'N/A'}, **Rel**: {metrics['relevance']}, **Max**: {metrics['dirtiest_sensor_val']:.4e}\n")
                report.write("\n")

    # Make sure output dir for graphs exists
    graphs_dir = os.path.join(OUTPUT_DIR, 'graphs')
    if not os.path.exists(graphs_dir):
        os.makedirs(graphs_dir)

    # Generate Summary Section by Density
    print("Generating Summary & Graphs...")
    
    # Aggregation for Graphs
    # There might be multiple configs with same density? For position1-3 they are likely different.
    # We will map by config name for this specific request, OR density if user prefers.
    # The original script mapped by density. Let's keep it consistent but also list by config.
    
    density_map = {} # { density: { 'ec': [], 'ea': [], 'rel': [] } }
    
    with open(REPORT_FILE, 'a', encoding='utf-8') as report:
        report.write("## Summary Statistics by Config\n\n")
        report.write("| Config | Density | Avg Ec | Avg Es | Avg Rank | Avg Ea | Avg Relevance |\n")
        report.write("|---|---|---|---|---|---|---|\n")
        
        sorted_configs = sorted(summary_stats.items(), key=lambda x: (x[1]['sensor_count'], x[0]))
        
        for config, stats in sorted_configs:
            count = stats['sensor_count']
            
            avg_ec = sum(stats['ec']) / len(stats['ec']) if stats['ec'] else 0
            avg_es = sum(stats['es']) / len(stats['es']) if stats.get('es') else 0
            avg_rank = sum(stats['source_rank']) / len(stats['source_rank']) if stats.get('source_rank') else 0
            avg_ea = sum(stats['ea']) / len(stats['ea']) if stats['ea'] else 0
            avg_rel = sum(stats['relevance']) / len(stats['relevance']) if stats['relevance'] else 0
            
            report.write(f"| {config} | {count} | {avg_ec:.4f} | {avg_es:.4f} | {avg_rank:.2f} | {avg_ea:.4f} | {avg_rel:.2f} |\n")
            
            # Collect for aggregation
            if count not in density_map:
                density_map[count] = {'ec': [], 'es': [], 'ea': [], 'rel': [], 'rank': []}
            density_map[count]['ec'].extend(stats['ec'])
            if stats.get('es'):
                density_map[count]['es'].extend(stats['es'])
            if stats.get('source_rank'):
                 density_map[count]['rank'].extend(stats['source_rank'])
            density_map[count]['ea'].extend(stats['ea'])
            density_map[count]['rel'].extend(stats['relevance'])

        # Aggregate Table
        report.write("\n## Aggregate by Density\n\n")
        report.write("| Density | Avg Ec | Avg Es | Avg Rank | Avg Ea | Avg Relevance |\n")
        report.write("|---|---|---|---|---|---|\n")
        
        densities = sorted(density_map.keys())
        avg_ea_list = []
        avg_ec_list = []
        avg_es_list = []
        avg_rank_list = []
        std_dev_ea_list = []
        
        for count in densities:
            d_stats = density_map[count]
            avg_ec = sum(d_stats['ec']) / len(d_stats['ec']) if d_stats['ec'] else 0
            avg_es = sum(d_stats['es']) / len(d_stats['es']) if d_stats.get('es') else 0
            avg_rank = sum(d_stats['rank']) / len(d_stats['rank']) if d_stats.get('rank') else 0
            avg_ea = sum(d_stats['ea']) / len(d_stats['ea']) if d_stats['ea'] else 0
            avg_rel = sum(d_stats['rel']) / len(d_stats['rel']) if d_stats['rel'] else 0
            
            # Std Dev for Aggregate
            variance = sum([((x - avg_ea) ** 2) for x in d_stats['ea']]) / len(d_stats['ea']) if d_stats['ea'] else 0
            std_dev = math.sqrt(variance)
            std_dev_ea_list.append(std_dev)
            
            avg_ea_list.append(avg_ea)
            avg_ec_list.append(avg_ec)
            avg_es_list.append(avg_es)
            avg_rank_list.append(avg_rank)
            
            report.write(f"| {count} | {avg_ec:.4f} | {avg_es:.4f} | {avg_rank:.2f} | {avg_ea:.4f} | {avg_rel:.2f} |\n")

    # Generate Graphs using Matplotlib
    try:
        import matplotlib.pyplot as plt
        
        # Graph 1: Ea vs Density
        plt.figure(figsize=(10, 6))
        plt.errorbar(densities, avg_ea_list, yerr=std_dev_ea_list, fmt='o-', capsize=5, label='Avg Accuracy Error')
        plt.title('Impact of Sensor Density on Accuracy Error (Ea) [Dane1-5, Wind 220°]')
        plt.xlabel('Number of Sensors')
        plt.ylabel('Accuracy Error (Pixels)')
        plt.grid(True)
        plt.legend()
        plt.savefig(os.path.join(graphs_dir, 'Ea_vs_Density.png'))
        plt.close()
        
        # Graph 2: Ec vs Density
        plt.figure(figsize=(10, 6))
        plt.plot(densities, avg_ec_list, 's-', color='orange', label='Avg Classification Error')
        plt.title('Impact of Sensor Density on Classification Error (Ec) [Dane1-5, Wind 220°]')
        plt.xlabel('Number of Sensors')
        plt.ylabel('Classification Error (Ratio)')
        plt.grid(True)
        plt.legend()
        plt.savefig(os.path.join(graphs_dir, 'Ec_vs_Density.png'))
        plt.close()
        
        # Graph 3: Es vs Density
        plt.figure(figsize=(10, 6))
        plt.plot(densities, avg_es_list, '^-', color='green', label='Avg Search Error (Es)')
        plt.title('Impact of Sensor Density on Search Error (Es) [Dane1-5, Wind 220°]')
        plt.xlabel('Number of Sensors')
        plt.ylabel('Search Error (Ratio)')
        plt.grid(True)
        plt.legend()
        plt.savefig(os.path.join(graphs_dir, 'Es_vs_Density.png'))
        plt.close()
        
        # Graph 4: Rank vs Density
        plt.figure(figsize=(10, 6))
        plt.plot(densities, avg_rank_list, 'd-', color='purple', label='Avg True Source Rank')
        plt.title('Impact of Sensor Density on True Source Rank [Dane1-5, Wind 220°]')
        plt.xlabel('Number of Sensors')
        plt.ylabel('Rank (1 = Best)')
        plt.grid(True)
        plt.legend()
        plt.savefig(os.path.join(graphs_dir, 'Rank_vs_Density.png'))
        plt.close()
        
        print("Graphs generated in TestResults_Dane/graphs/")
        
        # Add Graphs to Report
        with open(REPORT_FILE, 'a', encoding='utf-8') as report:
            report.write("\n## Visual Analysis\n\n")
            report.write("![Ea vs Density](graphs/Ea_vs_Density.png)\n\n")
            report.write("![Ec vs Density](graphs/Ec_vs_Density.png)\n\n")
            report.write("![Es vs Density](graphs/Es_vs_Density.png)\n\n")
            report.write("![Rank vs Density](graphs/Rank_vs_Density.png)\n\n")
            
    except ImportError:
        print("Matplotlib not found. Skipping graph generation.")
        with open(REPORT_FILE, 'a', encoding='utf-8') as report:
            report.write("\n> [!WARNING]\n> Matplotlib not installed. Graphs could not be generated.\n\n")

    print("Test Complete.")
if __name__ == "__main__":
    app = QApplication(sys.argv) # Necessary for Graphics Scene
    process_data_files()
    print("Done! Check TestResults_Dane/REPORT.md")
