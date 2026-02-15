
import sys
import os
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from simulation import SimulationManager
from models import Sensor

# Setup 20x20 grid
# Place sensor at 5,5
# Wind shifts it by -10 in X. New source should be at -5, 5.
# We expect nothing at first.
# When radius > 5, we expect pixels at x=0 to fill.
# Wind strength: let's calc pixels.
# code: offset = (strength/100) * scale(20) = strength/5.
# want offset -10. strength = 50.
# direction: 0 is East (positive X). We want Negative X (West).
# Angle 180.
# Radians(-180) = -pi. Cos = -1. Sin = 0.
# offset_x = -10. offset_y = 0.

try:
    s = Sensor(5, 5)
    sim = SimulationManager(20, 20, [s], wind_direction=180, wind_strength=50)

    print(f"Initial: {sim.steps[0][5][5].status}") 
    # Init grid should have polluted at 5,5 because init uses raw coordinates.

    sim.next_step() # Radius 1. Source -5, 5. Range -6..-4. All < 0. No change expected?
    # Wait, init grid polluted 5,5. 
    # next_step copies prev. So 5,5 remains polluted.
    # New candidates: source at -5,5. radius 1. dx -1..1. nx -6..-4. Out of bounds.

    # Let's go to radius 6.
    # Radius 6. source -5. dx -6..6. nx -11..1.
    # nx=0, nx=1 should be valid.
    
    for i in range(10):
        sim.next_step()
        # s.radius becomes i+1.
        # check grid at 0,5
        cell = sim.steps[-1][5][0]
        print(f"Step {i+1}, Radius {s.radius}, Cell(0,5) status: {cell.status}")

except Exception as e:
    print(f"Error: {e}")
