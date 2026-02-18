
import sys
import os
import json
import csv
import math
import copy
import time
from multiprocessing import Pool, cpu_count, current_process

# Add project root to path (3 levels up from tests/runners/automate_tests.py)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(ROOT_DIR)

from models import Sensor
from ui.simulation_controller import SimulationController

# Configuration
TEST_DATA_DIR = os.path.join(ROOT_DIR, 'tests', 'data', 'data-auto-testing')
SAVED_SIM_DIR = os.path.join(ROOT_DIR, 'savedSymulations')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'tests', 'docs')
REPORT_FILE = os.path.join(OUTPUT_DIR, 'REPORT_FULL.md')
GRID_WIDTH = 100
GRID_HEIGHT = 100

def load_sim_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

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

def process_single_file(args):
    """
    Worker function to process a single CSV file with all provided configurations.
    Returns a dict with filename and results.
    """
    csv_file, config_paths = args
    csv_path = os.path.join(TEST_DATA_DIR, csv_file)
    
    results = {
        'file': csv_file,
        'configs': {}
    }
    
    # print(f"[{current_process().name}] Processing {csv_file}...")
    
    # Create Controller (Reusable if we clear it)
    controller = SimulationController(100, 100, [], 0, 0)
    
    for config_path in config_paths:
        config_name = os.path.basename(config_path)
        config_key = config_name.replace('.json', '')
        
        # Load Config
        try:
            sim_data = load_sim_config(config_path)
        except Exception as e:
            results['configs'][config_key] = {'error': str(e)}
            continue
            
        grid_w = sim_data['grid']['width']
        grid_h = sim_data['grid']['height']
        
        # Setup Sensors
        sensors = []
        for s_data in sim_data['sensors']:
             sensors.append(Sensor(s_data['x'], s_data['y'], s_data['pollution_value']))
        
        # Configure Controller
        controller.set_grid_size(grid_w, grid_h)
        controller.sensors = sensors # This works because controller doesn't copy on assign, but uses ref.
        # However, set_grid_size clears sensors. So assign after.
        
        # Import Data
        try:
            controller.import_csv_data(csv_path)
        except Exception as e:
            results['configs'][config_key] = {'error': f"Import Error: {e}"}
            continue
        
        true_source_pos = controller.true_source_pos
        
        # Calculate Wind
        wind_dir, wind_str = calculate_wind_parameters(controller.sensors, true_source_pos)
        
        # Note: Previous script ran 'run_synchronous_weighted_sum' here but IGNORED the result.
        # We are omitting it for optimization as it was dead code affecting performance.
        
        # Run Standard Simulation for Metrics
        controller.update_wind(wind_dir, wind_str)
        controller.run() 
        metrics = controller.calculate_accuracy_metrics()
        
        if metrics:
            metrics['sensor_count'] = len(sensors)
            results['configs'][config_key] = metrics
            
    return results

def process_data_files():
    # Create Output Dir
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    graphs_dir = os.path.join(OUTPUT_DIR, 'graphs')
    os.makedirs(graphs_dir, exist_ok=True)

    # Initialize Report
    with open(REPORT_FILE, 'w', encoding='utf-8') as report:
        report.write("# Report of Automated Tests (Files 001-100)\n")
        report.write("Optimized Parallel Execution\n\n")

    # Files to process (Test_001 to Test_100)
    # We want ALL Test_*.csv files in the directory
    all_files = sorted([f for f in os.listdir(TEST_DATA_DIR) if f.startswith('Test_') and f.endswith('.csv')])
    
    # Ensure strict sorting 1-100 manually because string sort puts Test_100 before Test_20
    # Try to extract number
    try:
        all_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    except:
        pass # Fallback to string sort if naming is weird
    
    # Select files (User asked for 1-100)
    # If there are more, we can slice. Assuming folder has correct files.
    csv_files = all_files
    
    print(f"Found {len(csv_files)} test files. Preparing to run on {cpu_count()} cores.")

    # Configurations
    # Configurations (5 to 100 step 5)
    config_files = [f'research/uniform_{i}_sensors.json' for i in range(5, 101, 5)]

    all_configs_paths = []
    for cf in config_files:
        p = os.path.join(SAVED_SIM_DIR, cf)
        if os.path.exists(p):
            all_configs_paths.append(p)
        else:
            print(f"Warning: Config {cf} not found in {SAVED_SIM_DIR}")
            
    # Prepare Args for Pool
    tasks = [(f, all_configs_paths) for f in csv_files]
    
    # Run Parallel
    start_time = time.time()
    results = []
    with Pool(processes=cpu_count()) as pool:
        # Use imap to get results as they complete (approx) or just map
        # map guarantees order of results matches input order
        results = pool.map(process_single_file, tasks)
        
    duration = time.time() - start_time
    print(f"Processing finished in {duration:.2f} seconds.")
    
    # Process Results and Write Report
    summary_stats = {} # { config_key: { ec: [], ... } }
    
    with open(REPORT_FILE, 'a', encoding='utf-8') as report:
        for res in results:
            fname = res['file']
            report.write(f"## Data: {fname}\n\n")
            
            for config_key, metrics in res['configs'].items():
                if 'error' in metrics:
                    report.write(f"### Configuration: {config_key}\n")
                    report.write(f"> Error: {metrics['error']}\n\n")
                    continue
                
                # Add to stats
                if config_key not in summary_stats:
                    summary_stats[config_key] = {
                        'ec': [], 'ea': [], 'es': [], 'relevance': [], 'source_rank': [],
                        'sensor_count': metrics['sensor_count'],
                        'max_vals': []
                    }
                
                stats = summary_stats[config_key]
                stats['ec'].append(metrics['ec'])
                if metrics['ea'] is not None: stats['ea'].append(metrics['ea'])
                if metrics['es'] is not None: stats['es'].append(metrics['es'])
                if metrics['source_rank'] is not None: stats['source_rank'].append(metrics['source_rank'])
                stats['relevance'].append(metrics['relevance'])
                stats['max_vals'].append(metrics['dirtiest_sensor_val'])
                
                # Write to File
                es_str = f"{metrics['es']:.4f}" if metrics['es'] is not None else "N/A"
                rank_str = str(metrics['source_rank']) if metrics['source_rank'] is not None else "N/A"
                ea_str = f"{metrics['ea']:.4f}" if metrics['ea'] is not None else "N/A"
                
                report.write(f"### Configuration: {config_key}\n")
                report.write(f"- **Ec**: {metrics['ec']:.4f}, **Es**: {es_str}, **Rank**: {rank_str}, **Ea**: {ea_str}, **Rel**: {metrics['relevance']}, **Max**: {metrics['dirtiest_sensor_val']:.4e}\n")
            report.write("\n")

        # Write Summary Section
        report.write("## Summary Statistics\n\n")
        report.write("| Config | Sensors | Avg Ec | Avg Es | Avg Rank | Avg Ea | Avg Relevance | Count |\n")
        report.write("|---|---|---|---|---|---|---|---|\n")
        
        for config_key, stats in summary_stats.items():
            count = len(stats['ec'])
            avg_ec = sum(stats['ec']) / count if count else 0
            avg_es = sum(stats['es']) / len(stats['es']) if stats['es'] else 0
            avg_rank = sum(stats['source_rank']) / len(stats['source_rank']) if stats['source_rank'] else 0
            avg_ea = sum(stats['ea']) / len(stats['ea']) if stats['ea'] else 0
            avg_rel = sum(stats['relevance']) / count if count else 0
            
            report.write(f"| {config_key} | {stats['sensor_count']} | {avg_ec:.4f} | {avg_es:.4f} | {avg_rank:.2f} | {avg_ea:.4f} | {avg_rel:.2f} | {count} |\n")
            
    print(f"Report written to {REPORT_FILE}")

if __name__ == "__main__":
    process_data_files()
