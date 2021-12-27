#! /usr/bin/env python3

import argparse
import csv
import json
import os

def parse_arguments():
    parser = argparse.ArgumentParser(
        "Pre-process air pollution data.")
    parser.add_argument('data_dir', metavar="data-dir",
        help="Path to directory containing the raw CSV data files. Expected naming scheme for a file: FS-10_YYYY.")
    parser.add_argument('-o', '--output',
        help="Path for pre-processing result (CSV file).")
    
    return parser.parse_args()

def end_of_data(line):
    # empty line only consists of '\n' and denotes end of data
    return line == '\n'

def no_state_assigned(line):
    # 'UBA' means that the data point was entered by Umweltbundesamt, which is not assigned to a state
    return line.startswith("UBA;")

def output_path(file_path, suffix="", extension=".csv"):
    return file_path[:-4] + suffix + extension

args = parse_arguments()
files = sorted(
    [os.path.join(args.data_dir, file) for file in os.listdir(args.data_dir) 
    if os.path.isfile(os.path.join(args.data_dir, file))]
)
file_path = "FS-10.csv" if args.output is None else args.output

current_header = ""

print("Merging air pollution data...")
with open(output_path(file_path, "_total"), mode="w", encoding="utf-8") as output:
    data = []
    for file in files:
        year = file[-8:-4]
        with open(file) as input:
            header = input.readline()
            if len(header) > len(current_header):
                current_header = header
            for line in input:
                if no_state_assigned(line):
                    continue
                if end_of_data(line):
                    break
                data.append("{};{}".format(year,line))
    
    output.write('\ufeff')  # encode as BOM, see https://stackoverflow.com/questions/5202648/adding-bom-unicode-signature-while-saving-file-in-python/5202815
    output.write("year;state;station_code;station_name;station_surrounding;station_kind;year_average;days_above_limit;days_above_limit_cleaned\n")
    output.writelines(data)

print("Processing air pollution data...")
with open(output_path(file_path, "_total"), newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    fields_to_process = ['year', 'state', 'year_average', 'days_above_limit', 'days_above_limit_cleaned']
    data = {}
    with open(output_path(file_path, "_processed", ".json"), "w", newline="") as output:
        for row in reader:
            row['year'] = row['\ufeffyear']  # BOM encoding is read as field name
            if not row['state'] in data:
                data[row['state']] = {}
            if not row['year'] in data[row['state']]:
                data[row['state']][row['year']] = {}
            dataset = data[row['state']][row['year']]
            fields_to_aggregate = ['year_average', 'days_above_limit', 'days_above_limit_cleaned']
            for field in fields_to_aggregate:
                value = 0
                if row[field] is not None and not row[field] == '-':
                    value = row[field].replace(',', '.')
                dataset[field] = dataset.get(field, 0) + float(value)
        
        json.dump(data, output, indent=4)
