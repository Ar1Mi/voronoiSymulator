
import sys
import os
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from ui.simulation_controller import SimulationController

def verify():
    # Mock Controller
    controller = SimulationController(100, 100, [], "N", 10)
    
    # 1. Mock CSV (2x2)
    # 10 20
    # 30 40
    # Max is 40. Thresh 50% is 20.
    # Hotspot (>20) is (1,1)=40 and (0,1)=30. (Note: (0,0)=10 <= 20, (0,1)=20 <= 20 if strict >)
    # Check logic: " > threshold ". 20 is not > 20.
    # So Hotspot is (0,1)=30 and (1,1)=40.
    controller.csv_grid = [
        [10.0, 20.0],
        [30.0, 40.0]
    ]
    
    # Scale: 50x50 blocks.
    # Source Area: 2 blocks * 2500 = 5000 cells.
    
    # 2. Mock Sim Grid (100x100)
    # Create 100x100 empty
    sim_grid = [[0.0 for _ in range(100)] for _ in range(100)]
    
    # Set Sim Max to 100. Thresh 50% = 50.
    # Scenario:
    # 1. Perfect Intersection block: 10x10 at (60,60). Val 80. (Inside Source(1,1))
    #    Size: 100 cells.
    # 2. False Positive block: 10x10 at (0,0). Val 80. (Inside Source(0,0) which is NOT hotspot)
    #    Size: 100 cells.
    
    # Block 1 (Overlap)
    for y in range(60, 70):
        for x in range(60, 70):
            sim_grid[y][x] = 80.0

    # Block 2 (False Positive)
    for y in range(0, 10):
        for x in range(0, 10):
            sim_grid[y][x] = 80.0
            
    controller.accumulated_grid = sim_grid
    
    print("running stats...")
    stats = controller.calculate_area_overlap(0.5)
    
    print("Stats:", stats)
    
    # Validation
    # Source Area: 5000
    if stats['source_area_cells'] == 5000:
        print("PASS: Source Area 5000.")
    else:
        print(f"FAIL: Source Area {stats['source_area_cells']}")
        
    # Overlap: 100 (Block 1)
    if stats['overlap_cells'] == 100:
        print("PASS: Overlap 100.")
    else:
        print(f"FAIL: Overlap {stats['overlap_cells']}")
        
    # Overlap %: 100/5000 = 2.0%
    if abs(stats['overlap_percent'] - 2.0) < 0.1:
         print("PASS: Overlap % 2.0")
    else:
         print(f"FAIL: Overlap % {stats['overlap_percent']}")

    # False Positive: 100 (Block 2)
    # Sim Area = 200. Overlap = 100. FP = 100.
    if stats['false_positive_cells'] == 100:
        print("PASS: False Positive 100.")
    else:
        print(f"FAIL: False Positive {stats['false_positive_cells']}")

if __name__ == "__main__":
    verify()
