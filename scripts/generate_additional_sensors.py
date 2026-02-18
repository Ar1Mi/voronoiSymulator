
import json
import os

def generate_sensors(count, width, height, filename):
    sensors = []
    
    # Simple logic for 50 and 75 (assuming 100x100 grid)
    # 50: 10x5 grid -> x step 10, y step 20
    # 75: 5x15 grid -> x step 20 (or 5 cols), y step ~6.6
    
    if count == 50:
        # 10 cols x 5 rows
        # X: 5, 15, ..., 95 (10 items)
        # Y: 10, 30, 50, 70, 90 (5 items) -> Step 20. Centers at 10, 30...
        
        for y in range(10, 100, 20):
            for x in range(5, 100, 10):
                sensors.append({"x": x, "y": y, "pollution_value": 0.0, "polluted": True})
                
    elif count == 75:
        # 5 cols x 15 rows
        # X: 10, 30, 50, 70, 90 (5 items)
        # Y: 15 rows distributed in 100. Step = 100/15 = 6.66
        # Let's try to centre them.
        
        cols = 5
        rows = 15
        
        x_step = 100 // cols # 20
        y_step = 100 / rows  # 6.66
        
        for r in range(rows):
            y = int((r * y_step) + (y_step / 2))
            for c in range(cols):
                x = int((c * x_step) + (x_step / 2))
                sensors.append({"x": x, "y": y, "pollution_value": 0.0, "polluted": True})
                
    data = {
        "version": 1,
        "grid": {"width": 100, "height": 100},
        "wind": {"direction": 0, "strength": 0},
        "sensors": sensors
    }
    
    output_dir = os.path.join(os.path.dirname(__file__), '../savedSymulations/research')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"Generated {len(sensors)} sensors at {output_path}")

if __name__ == "__main__":
    generate_sensors(50, 100, 100, 'uniform_50_sensors.json')
    generate_sensors(75, 100, 100, 'uniform_75_sensors.json')
