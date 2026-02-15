
import json
import os
import random
import math


# Configuration
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
OUTPUT_DIR = os.path.join(ROOT_DIR, 'savedSymulations', 'research')
GRID_WIDTH = 100
GRID_HEIGHT = 100

def generate_uniform_grid_points(n, width, height):
    """
    Generates n points distributed uniformly on a grid.
    Strategies:
    - If n is a perfect square (e.g. 25 -> 5x5), use a square grid.
    - If n fits a rectangular grid (e.g. 10 -> 2x5, 15 -> 3x5), use that.
    - For 5, use a 'quincunx' (dice 5) pattern for better coverage than a line.
    """
    points = []
    
    # Strategy for 5: Quincunx (Corners + Center)
    if n == 5:
        margin = 20
        # Center
        points.append((width // 2, height // 2))
        # Top-Left
        points.append((margin, margin))
        # Top-Right
        points.append((width - margin, margin))
        # Bottom-Left
        points.append((margin, height - margin))
        # Bottom-Right
        points.append((width - margin, height - margin))
        return points

    # Find best grid factors for Rectangular Grid
    best_rows = 1
    best_cols = n
    
    # Try to find factors close to sqrt(n)
    sqrt_n = int(math.sqrt(n))
    for r in range(sqrt_n, 0, -1):
        if n % r == 0:
            best_rows = r
            best_cols = n // r
            break
            
    # If 10 -> 2x5.
    rows = best_rows
    cols = best_cols
    
    # Calculate step sizes
    # We want to center the grid.
    # Spacing = Size / (Steps + 1) if we don't want points on edges?
    # Or Spacing = Size / Steps if we assume points are centers of influence.
    
    # Let's use Margin approach.
    x_step = width / cols
    y_step = height / rows
    
    for r in range(rows):
        for c in range(cols):
            # Center of the cell
            x = int((c + 0.5) * x_step)
            y = int((r + 0.5) * y_step)
            points.append((x, y))
            
    return points

def generate_uniform_config(filename, sensor_count):
    points = generate_uniform_grid_points(sensor_count, GRID_WIDTH, GRID_HEIGHT)
    
    sensors = []
    for (x, y) in points:
        val = 0.0 # Will be populated by Test Data
        sensors.append({
            "x": x,
            "y": y,
            "pollution_value": val,
            "polluted": True
        })
        
    data = {
        "version": 1,
        "grid": {
            "width": GRID_WIDTH,
            "height": GRID_HEIGHT
        },
        "wind": {
            "direction": 0,
            "strength": 0
        },
        "sensors": sensors
    }
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f"Generated: {filepath} ({len(sensors)} sensors, Uniform)")

def main():
    # Clean old Research files
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            if f.endswith('.json'):
                os.remove(os.path.join(OUTPUT_DIR, f))
    else:
        os.makedirs(OUTPUT_DIR)
        
    print(f"Generating uniform research scenarios in: {OUTPUT_DIR}")
    
    # Scenarios requested: 5, 10, 15, 20, 25
    densities = [5, 10, 15, 20, 25]
    
    for d in densities:
        filename = f"uniform_{d}_sensors.json"
        generate_uniform_config(filename, d)

if __name__ == "__main__":
    main()
