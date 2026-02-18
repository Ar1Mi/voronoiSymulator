import json
import os

def generate_100_sensors():
    # Grid 100x100
    # 100 sensors -> 10x10 grid
    # Spacing = 10
    # Centers: 5, 15, 25 ... 95
    
    sensors = []
    
    for y in range(5, 100, 10):
        for x in range(5, 100, 10):
            sensor = {
                "x": x,
                "y": y,
                "pollution_value": 0.0,
                "polluted": True
            }
            sensors.append(sensor)
            
    data = {
        "version": 1,
        "grid": {
            "width": 100,
            "height": 100
        },
        "wind": {
            "direction": 0,
            "strength": 0
        },
        "sensors": sensors
    }
    
    output_dir = os.path.join(os.path.dirname(__file__), '../savedSymulations/research')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'uniform_100_sensors.json')
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"Generated {len(sensors)} sensors at {output_path}")

if __name__ == "__main__":
    generate_100_sensors()
