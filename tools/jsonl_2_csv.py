import json
import csv
import argparse

def jsonl_to_csv(jsonl_path, csv_path, fields):
    with open(jsonl_path, 'r', encoding='utf-8') as jsonl_file, \
         open(csv_path, 'w', encoding='utf-8-sig', newline='') as csv_file:

        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()

        for line in jsonl_file:
            data = json.loads(line)
            row = {field: data.get(field, '') for field in fields}
            writer.writerow(row)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert JSONL to CSV with selected fields.')
    parser.add_argument('--jsonl', type=str, required=True, help='Path to input JSONL file')
    parser.add_argument('--csv', type=str, required=True, help='Path to output CSV file')
    parser.add_argument('--fields', type=str, required=True, help='Comma-separated list of fields to keep')

    args = parser.parse_args()
    fields = [field.strip() for field in args.fields.split(',')]

    jsonl_to_csv(args.jsonl, args.csv, fields)

