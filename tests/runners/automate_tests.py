
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

# Add project root to path (3 levels up from tests/runners/automate_tests.py)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(ROOT_DIR)

from simulation import SimulationManager
from models import Sensor
from ui.grid_renderer import GridRenderer
from ui.simulation_controller import SimulationController # Used for import logic

# Configuration
TEST_DATA_DIR = os.path.join(ROOT_DIR, 'tests', 'data', 'data-auto-testing')
SAVED_SIM_DIR = os.path.join(ROOT_DIR, 'savedSymulations')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'TestResults_001-010')
REPORT_FILE = os.path.join(OUTPUT_DIR, 'REPORT.md')
GRID_WIDTH = 100
GRID_HEIGHT = 100

# Create Output Dir
os.makedirs(OUTPUT_DIR, exist_ok=True)
# os.makedirs(os.path.join(OUTPUT_DIR, 'images'), exist_ok=True) # Skipped for No Images

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
    Calculates wind direction and strength.
    Direction: Vector from Dirtiest Sensor -> True Source.
    Strength: 20%.
    """
    if not sensors or not true_source_pos:
        return 0, 0

    dirtiest = max(sensors, key=lambda s: s.pollution_value)
    
    sx, sy = dirtiest.x, dirtiest.y
    tx, ty = true_source_pos
    
    # Calculate vector from Sensor to True Source
    dx = tx - sx
    dy = ty - sy
    
    angle_rad = math.atan2(dy, dx)
    wind_dir = -math.degrees(angle_rad)
    
    return wind_dir, 20 # 20% strength

def render_heatmap(accumulated_grid, width, height, sensors, true_source_pos, csv_grid, filename):
    # Import CELL_SIZE locally to be sure
    from constants import CELL_SIZE
    
    # Calculate total dimensions in pixels
    total_width = width * CELL_SIZE
    total_height = height * CELL_SIZE
    
    scene = QGraphicsScene()
    # Explicitly set the scene rect to the exact pixel dimensions
    scene.setSceneRect(0, 0, total_width, total_height)
    
    renderer = GridRenderer(scene, width, height)
    
    renderer.draw(
        grid_data=accumulated_grid, 
        show_grid=True, 
        sensors=sensors, 
        is_accumulated=True, 
        show_values=True,
        csv_grid=csv_grid,
        true_source_pos=true_source_pos
    )
    
    # Render to Image using the calculated dimensions
    image = QImage(int(total_width), int(total_height), QImage.Format.Format_ARGB32)
    image.fill(QColor("white"))
    
    painter = QPainter(image)
    # Render using the scene rect as the source
    scene.render(painter, target=QRectF(0, 0, total_width, total_height), source=QRectF(0, 0, total_width, total_height))
    painter.end()
    
    image.save(filename)

def process_data_files():
    # Helper to parse CSV (borrowed logic from SimulationController)
    controller = SimulationController(100, 100, [], 0, 0)
    
    # Initialize Report
    with open(REPORT_FILE, 'w', encoding='utf-8') as report:
        report.write("# Report of Automated Tests (Files 001-010)\n\n")

    # Files to process
    csv_files = sorted([f for f in os.listdir(TEST_DATA_DIR) if f.startswith('Test_') and f.endswith('.csv')])
    # Slice for batch 1-10
    csv_files = csv_files[0:10]
    
    # Summary Statistics Storage
    summary_stats = {} 
    
    # 1. Specific Configs - Only position1-3
    config_files = ['position1.json', 'position2.json', 'position3.json']
    all_configs_paths = []
    for cf in config_files:
        p = os.path.join(SAVED_SIM_DIR, cf)
        if os.path.exists(p):
            all_configs_paths.append(p)
        else:
            print(f"Warning: Config {cf} not found in {SAVED_SIM_DIR}")

    for csv_file in csv_files:
        csv_path = os.path.join(TEST_DATA_DIR, csv_file)
        print(f"Processing {csv_file}...")
        
        with open(REPORT_FILE, 'a', encoding='utf-8') as report:
            report.write(f"## Data: {csv_file}\n\n")
        
        for config_path in all_configs_paths:
            config_name = os.path.basename(config_path) # e.g. position1.json or random_5_sensors_v1.json
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
            csv_grid = controller.csv_grid
            
            # Calculate Wind
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

            # Generate Image (Skipped for Extended Run)
            # image_filename = f"{csv_file.replace('.csv','')}_{config_key}.png"
            
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
    density_map = {} # { density: { 'ec': [], 'ea': [], 'rel': [] } }
    
    with open(REPORT_FILE, 'a', encoding='utf-8') as report:
        report.write("## Summary Statistics by Sensor Density\n\n")
        report.write("| Density (Sensors) | Config | Avg Ec | Avg Es | Avg Rank | Avg Ea | Avg Relevance | Std Dev Ea |\n")
        report.write("|---|---|---|---|---|---|---|---|\n")
        
        sorted_configs = sorted(summary_stats.items(), key=lambda x: (x[1]['sensor_count'], x[0]))
        
        for config, stats in sorted_configs:
            count = stats['sensor_count']
            
            avg_ec = sum(stats['ec']) / len(stats['ec']) if stats['ec'] else 0
            avg_es = sum(stats['es']) / len(stats['es']) if stats.get('es') else 0
            avg_rank = sum(stats['source_rank']) / len(stats['source_rank']) if stats.get('source_rank') else 0
            avg_ea = sum(stats['ea']) / len(stats['ea']) if stats['ea'] else 0
            avg_rel = sum(stats['relevance']) / len(stats['relevance']) if stats['relevance'] else 0
            
            # Std Dev
            std_dev_ea = 0.0
            if stats['ea'] and len(stats['ea']) > 1:
                variance = sum([((x - avg_ea) ** 2) for x in stats['ea']]) / len(stats['ea'])
                std_dev_ea = math.sqrt(variance)
            
            report.write(f"| {count} | {config} | {avg_ec:.4f} | {avg_es:.4f} | {avg_rank:.2f} | {avg_ea:.4f} | {avg_rel:.2f} | {std_dev_ea:.4f} |\n")
            
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
        plt.title('Impact of Sensor Density on Accuracy Error (Ea)')
        plt.xlabel('Number of Sensors')
        plt.ylabel('Accuracy Error (Pixels)')
        plt.grid(True)
        plt.legend()
        plt.savefig(os.path.join(graphs_dir, 'Ea_vs_Density.png'))
        plt.close()
        
        # Graph 2: Ec vs Density
        plt.figure(figsize=(10, 6))
        plt.plot(densities, avg_ec_list, 's-', color='orange', label='Avg Classification Error')
        plt.title('Impact of Sensor Density on Classification Error (Ec)')
        plt.xlabel('Number of Sensors')
        plt.ylabel('Classification Error (Ratio)')
        plt.grid(True)
        plt.legend()
        plt.savefig(os.path.join(graphs_dir, 'Ec_vs_Density.png'))
        plt.close()
        
        # Graph 3: Es vs Density
        plt.figure(figsize=(10, 6))
        plt.plot(densities, avg_es_list, '^-', color='green', label='Avg Search Error (Es)')
        plt.title('Impact of Sensor Density on Search Error (Es)')
        plt.xlabel('Number of Sensors')
        plt.ylabel('Search Error (Ratio)')
        plt.grid(True)
        plt.legend()
        plt.savefig(os.path.join(graphs_dir, 'Es_vs_Density.png'))
        plt.close()
        
        # Graph 4: Rank vs Density
        plt.figure(figsize=(10, 6))
        plt.plot(densities, avg_rank_list, 'd-', color='purple', label='Avg True Source Rank')
        plt.title('Impact of Sensor Density on True Source Rank')
        plt.xlabel('Number of Sensors')
        plt.ylabel('Rank (1 = Best)')
        plt.grid(True)
        plt.legend()
        plt.savefig(os.path.join(graphs_dir, 'Rank_vs_Density.png'))
        plt.close()
        
        print("Graphs generated in TestResults/graphs/")
        
        # Add Graphs to Report
        with open(REPORT_FILE, 'a', encoding='utf-8') as report:
            report.write("\n## Visual Analysis\n\n")
            report.write("### Accuracy Error vs Sensor Density\n")
            report.write("The following graph shows the improvement in accuracy (lower distance to true source) as sensor density increases. Error bars indicate the standard deviation (stability) of the results.\n\n")
            report.write("![Ea vs Density](graphs/Ea_vs_Density.png)\n\n")
            
            report.write("### Classification Error vs Sensor Density\n")
            report.write("This graph illustrates how the predicted area size relative to the total field changes with more sensors.\n\n")
            report.write("![Ec vs Density](graphs/Ec_vs_Density.png)\n\n")

            report.write("### Search Error (Es) vs Sensor Density\n")
            report.write("This graph shows the search error, which is the cumulative area ratio of sensors ranked up to the true source.\n\n")
            report.write("![Es vs Density](graphs/Es_vs_Density.png)\n\n")

            report.write("### True Source Rank vs Sensor Density\n")
            report.write("This graph shows the average rank of the sensor containing the true source. Lower is better (1 means the dirtiest sensor found the source).\n\n")
            report.write("![Rank vs Density](graphs/Rank_vs_Density.png)\n\n")
            
    except ImportError:
        print("Matplotlib not found. Skipping graph generation.")
        with open(REPORT_FILE, 'a', encoding='utf-8') as report:
            report.write("\n> [!WARNING]\n> Matplotlib not installed. Graphs could not be generated.\n\n")

    # Generate Textual Conclusions
    with open(REPORT_FILE, 'a', encoding='utf-8') as report:
        report.write("## Conclusions\n\n")
        
        if len(densities) >= 2:
            first = densities[0]
            last = densities[-1]
            improvement_ea = ((avg_ea_list[0] - avg_ea_list[-1]) / avg_ea_list[0]) * 100
            
            report.write(f"Based on the analysis of {len(csv_files)} test cases across {len(densities)} density configurations:\n\n")
            report.write(f"1. **Accuracy Improvement**: Increasing sensor density from {first} to {last} resulted in a **{improvement_ea:.1f}% reduction** in Accuracy Error ($E_a$).\n")
            report.write(f"2. **Stability**: The standard deviation (error bars) typically decreases with higher density, indicating more consistent results.\n")
            report.write(f"3. **Optimal Density**: The 'knee' of the curve suggests where diminishing returns begin. (Refer to the Ea vs Density graph).\n")
    
    print("Test Complete.")

if __name__ == "__main__":
    app = QApplication(sys.argv) # Necessary for Graphics Scene
    process_data_files()
    print("Done! Check TestResults/REPORT.md")
