import sys
import os
import math

# Add project root to path
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ui.simulation_controller import SimulationController
from models import Sensor

def test_wind_metric_logic():
    print("--- Testing Wind Metric Logic ---")
    
    # 1. Setup Controller
    # Grid 100x100
    controller = SimulationController(100, 100, [], 0, 0)
    
    # 2. Add sensors
    # S1 (Dirty, Winner) at (60, 50)
    # S2 (Clean, Loser) at (40, 50)
    # Midpoint is 50.
    s1_x, s1_y = 60, 50
    s2_x, s2_y = 40, 50
    
    controller.sensors.append(Sensor(s1_x, s1_y, 100.0))
    controller.sensors.append(Sensor(s2_x, s2_y, 10.0))
    
    # 3. Set Wind
    
    # Case A: Wind blows Right (0 deg).
    # Pollution moves Right. Source is to the LEFT of S1.
    # We expect S1's predicted source area to shift LEFT.
    # Centroid X should be < 60 (and ideally < 50 if shift is strong enough).
    wind_dir = 0
    wind_str = 50 
    controller.update_wind(wind_dir, wind_str)
    controller._create_sim()
    
    metrics = controller.calculate_accuracy_metrics()
    if not metrics:
        print("FAIL: Metrics returned None")
        return

    centroid = metrics['centroid']
    cx, cy = centroid
    
    print(f"Sensors: Dirty({s1_x}, {s1_y}), Clean({s2_x}, {s2_y})")
    print(f"Wind: Dir={wind_dir}, Str={wind_str} (Blows Right)")
    print(f"Predicted Centroid: {centroid}")
    
    # Standard centroids without wind would be:
    # S1 owns x > 50. Centroid x ~ 75.
    # We expect shift LEFT (Upwind). So cx should be LESS than 75.
    # Current BUG (Downwind shift): region moves Right. cx > 75.
    
    base_cx = 75.0 # Approx
    
    if cx < base_cx - 5: # significant left shift
        print(f"RESULT: PASS - Centroid shifted LEFT ({cx:.1f} < {base_cx}). Correctly looking Upwind.")
    elif cx > base_cx + 5:
        print(f"RESULT: FAIL - Centroid shifted RIGHT ({cx:.1f} > {base_cx}). Calculating Downwind.")
    else:
        print(f"RESULT: NEUTRAL/UNCLEAR - Centroid {cx:.1f} approx same as base {base_cx}.")

    print("-" * 30)
    
    # Case B: Wind blows UP (90 deg UI / South math?)
    # Simulation.py says: 0=East (Right). 90=South (Down) visually? 
    # Let's check simulaton.py again:
    # rad = math.radians(-wind_direction)
    # If dir=90 (Up on dial usually?), rad=-90.
    # cos(-90)=0, sin(-90)=-1 (Up in math, but Y is inverted in screen, so -1 is UP visually?)
    # Wait. Screen Y: 0 is Top. Max is Bottom.
    # dy = -1. Moves to smaller Y. That is UP.
    # So Dir=90 is UP.
    # Pollution moves UP. Source is DOWN.
    # S1 is at (60, 50). Source should be at (60, >50).
    
    wind_dir = 90
    controller.update_wind(wind_dir, wind_str)
    controller._create_sim()
    
    metrics = controller.calculate_accuracy_metrics()
    cx, cy = metrics['centroid']
    
    print(f"Wind: Dir={wind_dir} (Blows UP)")
    print(f"Predicted Centroid: {centroid}")
    
    # Base Centroid Y for S1 (60,50) is 50 (symmetry).
    base_cy = 50.0
    
    if cy > base_cy + 5: # Shift DOWN (Positive Y)
        print(f"RESULT: PASS - Centroid shifted DOWN ({cy:.1f} > {base_cy}). Correctly looking Upwind.")
    elif cy < base_cy - 5: # Shift UP (Negative Y)
        print(f"RESULT: FAIL - Centroid shifted UP ({cy:.1f} < {base_cy}). Calculating Downwind.")
    else:
         print(f"RESULT: NEUTRAL - Centroid {cy:.1f} approx same as base {base_cy}.")

if __name__ == "__main__":
    test_wind_metric_logic()
