"""
Script to normalize test data from 'dane gauss testy.xlsx' into 100 CSV files
compatible with the VoronoiSymulator format.

Input Excel format:
- Columns: x_true_source, y_true_source, -, -, x_index, y_index, -, -, pollution_value
- 10000 rows (including header), each 100 rows = 1 test

Output CSV format (matching Dane1.csv):
- Row 1: true_source_x;true_source_y;...;;;;;;;
- Row 2: ;1000;2000;3000;4000;5000;6000;7000;8000;9000;10000  (x axis labels)
- Rows 3-12: y_label;values...  (10 rows with y labels 1000-10000)

Usage: python normalize_test_data.py
"""

import pandas as pd
import os


def normalize_value_for_csv(value):
    """Convert float to CSV-compatible string with comma as decimal separator."""
    if value == 0:
        return "0"
    
    # Format in scientific notation or regular depending on magnitude
    if abs(value) < 0.001 or abs(value) >= 1e6:
        # Scientific notation
        formatted = f"{value:.2E}"
    else:
        formatted = str(value)
    
    # Replace dot with comma for CSV format
    return formatted.replace('.', ',')


def create_csv_content(true_x, true_y, grid_data):
    """
    Create CSV content in simulator format.
    
    Args:
        true_x: True source X coordinate (0-10000)
        true_y: True source Y coordinate (0-10000)
        grid_data: dict {(x_index, y_index): pollution_value} where indices are 1000-10000
    
    Returns:
        List of CSV lines
    """
    lines = []
    
    # Row 1: True source coordinates (x;y;;;;;;;;)
    true_x_str = normalize_value_for_csv(true_x)
    true_y_str = normalize_value_for_csv(true_y)
    line1 = f"{true_x_str};{true_y_str};" + ";" * 8
    lines.append(line1)
    
    # Row 2: X-axis labels (;1000;2000;...;10000)
    x_labels = [str(i) for i in range(1000, 10001, 1000)]
    line2 = ";" + ";".join(x_labels)
    lines.append(line2)
    
    # Rows 3-12: Y-label + pollution values
    for y_index in range(1000, 10001, 1000):
        row_values = [str(y_index)]
        for x_index in range(1000, 10001, 1000):
            value = grid_data.get((x_index, y_index), 0.0)
            row_values.append(normalize_value_for_csv(value))
        lines.append(";".join(row_values))
    
    return lines


def main():
    # Root Dir
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    
    # Input file path
    excel_path = os.path.join(ROOT_DIR, 'tests', 'docs', 'dane gauss testy.xlsx')
    
    # Output directory
    output_dir = os.path.join(ROOT_DIR, 'tests', 'data', 'data-auto-testing')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Reading Excel file: {excel_path}")
    
    # Read Excel file (header is already in first row)
    df = pd.read_excel(excel_path, header=None)
    
    print(f"Total rows: {len(df)}")
    
    # Column indices (0-based):
    # 0: x_true_source
    # 1: y_true_source
    # 2: ignored (-)
    # 3: ignored (-)
    # 4: x_index
    # 5: y_index
    # 6: ignored (-)
    # 7: ignored (-)
    # 8: pollution_value
    
    COL_TRUE_X = 0
    COL_TRUE_Y = 1
    COL_X_INDEX = 4
    COL_Y_INDEX = 5
    COL_POLLUTION = 8
    
    # Process data: 100 rows per test, 100 tests total
    ROWS_PER_TEST = 100
    num_tests = len(df) // ROWS_PER_TEST
    
    print(f"Expected tests: {num_tests}")
    
    for test_idx in range(num_tests):
        start_row = test_idx * ROWS_PER_TEST
        end_row = start_row + ROWS_PER_TEST
        
        # Get data for this test
        test_data = df.iloc[start_row:end_row]
        
        # Get true source (all rows in one test have the same true source)
        true_x = test_data.iloc[0, COL_TRUE_X]
        true_y = test_data.iloc[0, COL_TRUE_Y]
        
        # Build grid data dictionary
        grid_data = {}
        for _, row in test_data.iterrows():
            x_idx = int(row[COL_X_INDEX])
            y_idx = int(row[COL_Y_INDEX])
            pollution = row[COL_POLLUTION]
            grid_data[(x_idx, y_idx)] = pollution
        
        # Create CSV content
        csv_lines = create_csv_content(true_x, true_y, grid_data)
        
        # Write to file
        output_file = os.path.join(output_dir, f"Test_{test_idx + 1:03d}.csv")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(csv_lines))
        
        if (test_idx + 1) % 10 == 0:
            print(f"Created {test_idx + 1} files...")
    
    print(f"\n✅ Done! Created {num_tests} test files in: {output_dir}")
    print(f"\nSample files:")
    print(f"  - {os.path.join(output_dir, 'Test_001.csv')}")
    print(f"  - {os.path.join(output_dir, 'Test_050.csv')}")
    print(f"  - {os.path.join(output_dir, 'Test_100.csv')}")


if __name__ == "__main__":
    main()
