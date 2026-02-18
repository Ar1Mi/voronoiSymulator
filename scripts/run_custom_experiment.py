
import sys
import os
import json
import csv
import copy
import math

from PyQt6.QtWidgets import QApplication, QGraphicsScene
from PyQt6.QtCore import QSize, QRectF
from PyQt6.QtGui import QImage, QPainter, QColor

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(ROOT_DIR)

from simulation import SimulationManager
from models import Sensor
from ui.grid_renderer import GridRenderer
from ui.simulation_controller import SimulationController 

# Configuration
TEST_DATA_DIR = os.path.join(ROOT_DIR, 'tests', 'data', 'data-manual-testing')
SAVED_SIM_DIR = os.path.join(ROOT_DIR, 'savedSymulations', 'research')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'CustomExperiment_Output')
PHASE1_CONFIG = 'uniform_25_sensors.json'
PHASE2_CONFIG = 'uniform_100_sensors.json'
INPUT_CSV = 'Dane1.csv'

# Ensure output dir
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_sim_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_standard_simulation(grid_width, grid_height, sensors, wind_dir, wind_str):
    """
    Run a standard simulation (Voronoi/Propagation) where all sensors compete.
    Each cell will end up with the value of the sensor that claims it.
    Returns: accumulated_grid (2D array of floats) containing the pollution selection.
    """
    # Create Simulation
    sim = SimulationManager(grid_width, grid_height, sensors, wind_dir, wind_str)
    
    # Run until stable
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
    
    # Extract values
    result_grid = [[0.0 for _ in range(grid_width)] for _ in range(grid_height)]
    for y in range(grid_height):
        for x in range(grid_width):
            cell = final_grid[y][x]
            if cell.status == "polluted" and cell.polluted_by:
                result_grid[y][x] = cell.polluted_by.pollution_value
            elif cell.status == "clean" and cell.polluted_by:
                 # Even if "clean" (shouldn't happen if all are polluted=True), 
                 # it has a source.
                 result_grid[y][x] = cell.polluted_by.pollution_value
    
    return result_grid

def capture_screenshot(scene, width, height, output_path):
    # Create QImage
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor("white"))
    
    painter = QPainter(image)
    scene.render(painter)
    painter.end()
    
    image.save(output_path)
    print(f"Screenshot saved to: {output_path}")

def sample_at_sensor_positions(accumulated_grid, target_w=10, target_h=10, grid_w=100, grid_h=100):
    """
    Sample the accumulated grid at the specific positions where the 100 sensors will be placed.
    The 100 sensors are placed at 5, 15, 25... 95 in both X and Y.
    """
    sampled_data = []
    
    # Calculate step size
    step_x = grid_w // target_w # 10
    step_y = grid_h // target_h # 10
    
    # Offset to center (5)
    offset_x = step_x // 2
    offset_y = step_y // 2
    
    for r in range(target_h): # 0 to 9
        row_values = []
        for c in range(target_w): # 0 to 9
            # Simulation coordinates
            sim_x = c * step_x + offset_x # 5, 15, ...
            sim_y = r * step_y + offset_y # 5, 15, ...
            
            # Ensure within bounds
            sim_x = min(sim_x, grid_w - 1)
            sim_y = min(sim_y, grid_h - 1)
            
            # Read exact value at this position
            val = accumulated_grid[sim_y][sim_x]
            row_values.append(val)
        sampled_data.append(row_values)
        
    return sampled_data

def write_csv_output(original_csv_path, sampled_data, output_csv_path):
    # Read header from original CSV to preserve True Source info
    with open(original_csv_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
        
    header = lines[0] # Header contains True Source format
    
    with open(output_csv_path, 'w', encoding='utf-8') as f:
        f.write(header)
        # Write X-coords header (Line 2)
        # Assuming 10 columns 1000-10000
        x_coords = ";".join([str((i+1)*1000) for i in range(10)])
        f.write(";" + x_coords + "\n")
        
        # Write data rows
        for i, row in enumerate(sampled_data):
            y_label = (i+1) * 1000
            
            # Format numbers with comma decimal separator
            formatted_values = []
            for val in row:
                # Use comma for decimal
                v_str = f"{val:.5e}".replace('.', ',')
                formatted_values.append(v_str)
            
            line_str = f"{y_label};" + ";".join(formatted_values) + "\n"
            f.write(line_str)
            
    print(f"Generated input data for Phase 2: {output_csv_path}")

def run_experiment():
    app = QApplication(sys.argv)
    
    # --- PHASE 1 ---
    print("=== STARTING PHASE 1: 25 Sensors ===")
    
    # Paths
    csv_input_path = os.path.join(TEST_DATA_DIR, INPUT_CSV)
    config_25_path = os.path.join(SAVED_SIM_DIR, PHASE1_CONFIG)
    
    # Load Config
    sim_data = load_sim_config(config_25_path)
    grid_w = sim_data['grid']['width']
    grid_h = sim_data['grid']['height']
    sensors_25 = [Sensor(s['x'], s['y'], s['pollution_value']) for s in sim_data['sensors']]
    
    # Controller for data Loading
    controller = SimulationController(grid_w, grid_h, sensors_25, 0, 0)
    controller.import_csv_data(csv_input_path)
    
    # Config for Run (Wind 220, 20%)
    wind_dir = 220
    wind_strength = 20
    
    # Run Standard Simulation
    print("Running Simulation 1 (Standard)...")
    accumulated_grid = run_standard_simulation(grid_w, grid_h, controller.sensors, wind_dir, wind_strength)
    
    # Visualization
    print("Rendering Phase 1...")
    scene = QGraphicsScene()
    scene.setSceneRect(0, 0, grid_w * 20, grid_h * 20) # Scale up for visibility? 
    # GridRenderer uses CELL_SIZE from constants.py
    # We should probably import CELL_SIZE or check grid_renderer.py
    from constants import CELL_SIZE
    
    renderer = GridRenderer(scene, grid_w, grid_h)
    renderer.draw(accumulated_grid, show_grid=True, sensors=controller.sensors, is_accumulated=True, 
                  true_source_pos=controller.true_source_pos)
    
    # Assuming CELL_SIZE is 20 (standard) or whatever constants.py has.
    # We need to set scene rect correctly based on CELL_SIZE
    scene_w = grid_w * CELL_SIZE
    scene_h = grid_h * CELL_SIZE
    scene.setSceneRect(0, 0, scene_w, scene_h)
    
    capture_screenshot(scene, int(scene_w), int(scene_h), os.path.join(OUTPUT_DIR, 'phase1_25sensors.png'))
    
    # Data Conversion
    print("Converting data (Sampling at sensor positions)...")
    sampled_data = sample_at_sensor_positions(accumulated_grid)
    output_csv_path = os.path.join(OUTPUT_DIR, 'phase1_result_data.csv')
    write_csv_output(csv_input_path, sampled_data, output_csv_path)
    
    
    # --- PHASE 2 ---
    print("\n=== STARTING PHASE 2: 100 Sensors ===")
    
    config_100_path = os.path.join(SAVED_SIM_DIR, PHASE2_CONFIG)
    
    # Load Config
    sim_data_100 = load_sim_config(config_100_path)
    sensors_100 = [Sensor(s['x'], s['y'], s['pollution_value']) for s in sim_data_100['sensors']]
    
    # Controller
    controller2 = SimulationController(grid_w, grid_h, sensors_100, 0, 0)
    controller2.import_csv_data(output_csv_path) # Import the generated data!
    
    # Run Standard Simulation
    print("Running Simulation 2 (Standard)...")
    accumulated_grid_2 = run_standard_simulation(grid_w, grid_h, controller2.sensors, wind_dir, wind_strength)
    
    # Visualization
    print("Rendering Phase 2...")
    renderer.draw(accumulated_grid_2, show_grid=True, sensors=controller2.sensors, is_accumulated=True,
                  true_source_pos=controller2.true_source_pos) # True source should be preserved from CSV
    
    capture_screenshot(scene, int(scene_w), int(scene_h), os.path.join(OUTPUT_DIR, 'phase2_100sensors.png'))
    
    print("\nExperiment Complete.")

if __name__ == "__main__":
    run_experiment()
