import json
import os
import math

def generate_grid_sensors(count, width, height, filename):
    sensors = []
    
    # Determine best rows/cols for "ideal" (square-ish) distribution
    # We look for factors of 'count' that are closest to sqrt(count)
    best_r = 1
    best_c = count
    min_diff = count
    
    # Find factors
    for r in range(1, int(math.sqrt(count)) + 1):
        if count % r == 0:
            c = count // r
            diff = abs(c - r)
            if diff < min_diff:
                min_diff = diff
                best_r = r
                best_c = c
                
    # We want cols/rows to match grid aspect ratio if possible, but grid is 1:1.
    # Just take best_r and best_c.
    # Attempt to align with previous logic if possible (e.g. 10s).
    
    # Overrides for specific requests to ensure nicelooking grids if automated factorization is weird
    # 40: 5x8 (factorization yields 5x8) -> good
    # 60: 6x10 (factorization yields 6x10) -> good
    # 70: 7x10 (factorization yields 7x10) -> good
    # 80: 8x10 (factorization yields 8x10) -> good
    # 90: 9x10 (factorization yields 9x10) -> good
    
    rows = best_r
    cols = best_c
    
    # Swap if we want more columns than rows or vice versa? 
    # Usually standard is width (cols) x height (rows).
    # Since 5x8 (40) -> 8 is closer to 100/10=10 than 5 is? scaling doesn't matter much for 1:1 grid.
    # Let's keep cols >= rows usually to match landscape typical, but here it's square.
    # Let's verify:
    # 40 -> 5 rows, 8 cols? or 8 rows, 5 cols?
    # 8 cols x 5 rows: col_step = 100/8 = 12.5, row_step = 100/5 = 20.
    # 5 cols x 8 rows: col_step = 20, row_step = 12.5.
    # Let's default to larger dimension is columns (width) purely for convention unless specified.
    if rows > cols:
        rows, cols = cols, rows
        
    # Recalculate if we want to force specific orientation?
    # Actually, for 70 (7x10), 10 cols x 7 rows is nice.
    
    x_step = width / cols
    y_step = height / rows
    
    for r in range(rows):
        # Center in the cell
        y = int((r * y_step) + (y_step / 2))
        for c in range(cols):
            x = int((c * x_step) + (x_step / 2))
            sensors.append({
                "x": x,
                "y": y,
                "pollution_value": 0.0,
                "polluted": True
            })
            
    print(f"Generating {count} sensors: {cols} cols x {rows} rows. Output: {filename}")
    
    data = {
        "version": 1,
        "grid": {"width": width, "height": height},
        "wind": {"direction": 0, "strength": 0},
        "sensors": sensors
    }
    
    output_dir = os.path.join(os.path.dirname(__file__), '../savedSymulations/research')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"Saved to {output_path}")

def main():
    # Generate for all multiples of 5 from 5 to 100
    for count in range(5, 101, 5):
        filename = f'uniform_{count}_sensors.json'
        generate_grid_sensors(count, 100, 100, filename)

if __name__ == "__main__":
    main()
