
import sys
import os
import unittest
import math

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from ui.simulation_controller import SimulationController
from models import Sensor

class TestSimulationTermination(unittest.TestCase):
    def test_wind_termination(self):
        """
        Test that simulation runs to completion (all cells classified)
        even with wind conditions that create distance gaps.
        """
        grid_w, grid_h = 50, 50
        sensors = [
            Sensor(10, 10, 1.0),
            Sensor(40, 40, 0.5)
        ]
        
        # Wind parameters that might cause gaps
        wind_dir = 45
        wind_str = 50 # Strong wind
        
        controller = SimulationController(grid_w, grid_h, sensors, wind_dir, wind_str)
        
        # Run synchronous simulation
        steps = controller.run()
        
        print(f"Simulation finished in {steps} steps.")
        print(f"Max distance: {controller.sim.max_distance}")
        print(f"Target radius: {math.ceil(controller.sim.max_distance)}")
        
        # Check final grid for unclassified cells
        final_grid = controller.sim.steps[-1]
        
        unclassified_count = 0
        for y in range(grid_h):
            for x in range(grid_w):
                if final_grid[y][x].status is None:
                    unclassified_count += 1
                    
        print(f"Unclassified cells: {unclassified_count}")
        
        self.assertEqual(unclassified_count, 0, f"Found {unclassified_count} unclassified cells! Simulation terminated too early.")
        
        # Verify valid steps count
        self.assertGreaterEqual(controller.sim.current_radius, math.ceil(controller.sim.max_distance))

if __name__ == '__main__':
    unittest.main()
