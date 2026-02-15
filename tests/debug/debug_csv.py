import csv
import os

def verify_dane1_parsing():
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    file_path = os.path.join(ROOT_DIR, 'tests', 'data', 'data-manual-testing', 'Dane1.csv')
    if not os.path.exists(file_path):
        print(f"{file_path} not found")
        return

    start_x, end_x = 1, 10
    start_y, end_y = 2, 11

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        rows = list(reader)

    print(f"Total rows: {len(rows)}")
    
    for r_idx in range(start_y, end_y + 1):
        row = rows[r_idx]
        parsed_row = []
        for c_idx in range(start_x, end_x + 1):
            try:
                val_str = row[c_idx].replace(',', '.')
                val = float(val_str)
                parsed_row.append(val)
            except ValueError:
                parsed_row.append("ERR")
        
        print(f"Row {r_idx}: {parsed_row}")

if __name__ == "__main__":
    verify_dane1_parsing()
