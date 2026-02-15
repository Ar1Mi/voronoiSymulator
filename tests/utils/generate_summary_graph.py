import matplotlib.pyplot as plt
import os

# Data provided by the user
densities = [5, 10, 15, 20, 25]
ec_values = [0.3498, 0.2108, 0.1534, 0.1240, 0.1112]

# Output directory
output_dir = 'TestResults_81-100/graphs'
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'Summary_Ec_vs_Density.png')

# Create the graph
plt.figure(figsize=(10, 6))
plt.plot(densities, ec_values, 's-', color='orange', label='Avg Classification Error (Ec)')

# Styling to match existing graphs
plt.title('Impact of Sensor Density on Classification Error (Ec) - Summary')
plt.xlabel('Number of Sensors')
plt.ylabel('Classification Error (Ratio)')
plt.grid(True)
plt.legend()

# Save the graph
plt.savefig(output_path)
print(f"Graph generated at: {output_path}")
