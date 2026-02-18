import json
import os
import random
import math

def generate_cvt_sensors(count, width, height, iterations=50):
    """
    Generates 'count' sensors in a 'width' x 'height' grid using 
    Centroidal Voronoi Tessellation (Lloyd's Algorithm).
    """
    
    # 1. Initialize random points
    # We use a margin to avoid sensors being too close to the edge initially, 
    # though CVT handles this naturally.
    sensors = []
    for _ in range(count):
        sensors.append({
            "x": random.randint(0, width - 1),
            "y": random.randint(0, height - 1)
        })

    # 2. Lloyd's Algorithm Loop
    for it in range(iterations):
        # Accumulators for centroids: sum_x, sum_y, pixel_count
        centroids = [[0, 0, 0] for _ in range(count)]
        
        # Iterate over every pixel in the grid
        for y in range(height):
            for x in range(width):
                # Find nearest sensor
                best_dist_sq = float('inf')
                best_idx = -1
                
                for idx, s in enumerate(sensors):
                    dx = x - s["x"]
                    dy = y - s["y"]
                    dist_sq = dx*dx + dy*dy
                    
                    if dist_sq < best_dist_sq:
                        best_dist_sq = dist_sq
                        best_idx = idx
                
                # Add pixel to that sensor's region
                centroids[best_idx][0] += x
                centroids[best_idx][1] += y
                centroids[best_idx][2] += 1
        
        # Move sensors to centroids
        max_shift = 0
        for idx in range(count):
            sum_x, sum_y, pixel_count = centroids[idx]
            if pixel_count > 0:
                new_x = sum_x / pixel_count
                new_y = sum_y / pixel_count
                
                # Check how much it moved (convergence check)
                dx = new_x - sensors[idx]["x"]
                dy = new_y - sensors[idx]["y"]
                shift = math.sqrt(dx*dx + dy*dy)
                if shift > max_shift:
                    max_shift = shift
                
                sensors[idx]["x"] = new_x
                sensors[idx]["y"] = new_y
            else:
                # If a sensor has no pixels (rare, but possible if initialized poorly), 
                # respawn it randomly
                sensors[idx]["x"] = random.randint(0, width - 1)
                sensors[idx]["y"] = random.randint(0, height - 1)
                max_shift = 999 # Force another iteration

        # Convergence optimized break
        if max_shift < 0.1:
            print(f"Converged after {it+1} iterations.")
            break
            
    # Round to integers for final output
    final_sensors = []
    for s in sensors:
        final_sensors.append({
            "x": int(round(s["x"])),
            "y": int(round(s["y"])),
            "pollution_value": 0.0,
            "polluted": True
        })
        
    return final_sensors

def save_configuration(sensors, width, height, filename):
    data = {
        "version": 1,
        "grid": {
            "width": width,
            "height": height
        },
        "wind": {
            "direction": 0,
            "strength": 0
        },
        "sensors": sensors
    }
    
    output_dir = os.path.join(os.path.dirname(__file__), '../savedSymulations/research')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"Saved {len(sensors)} sensors to {output_path}")

def main():
    # Generate for all multiples of 5 from 5 to 100
    # Also include specific requested counts if any
    
    # Using a fixed seed for reproducibility across runs if needed, 
    # but randomness helps explore different local minima. 
    # Let's use a seed to make it deterministic for now.
    random.seed(42)
    
    width = 100
    height = 100
    
    for count in range(5, 101, 5):
        print(f"Generating optimized positions for {count} sensors...")
        sensors = generate_cvt_sensors(count, width, height)
        filename = f'uniform_{count}_sensors.json'
        save_configuration(sensors, width, height, filename)

if __name__ == "__main__":
    main()
