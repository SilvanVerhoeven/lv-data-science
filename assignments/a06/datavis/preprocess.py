from datavis.utils import get_basename, get_filename, get_state, get_year, is_date, is_end_of_data, is_no_state_assigned, set_extension
import argparse
import csv
import json
import os

def parse_arguments():
    parser = argparse.ArgumentParser(
        "Pre-process election and air pollution data.")
    parser.add_argument('pollution_data_dir', metavar="pollution-data-dir",
        help="Path to directory containing the raw CSV pollution data files. Expected naming scheme for a file: FS-10_YYYY.")
    parser.add_argument('election_data_dir', metavar="election-data-dir",
        help="Path to directory containing the raw CSV data files. Expected naming scheme for a file: WE-Landtag_STATE.")
    parser.add_argument('governments_data_file', metavar="governments-data-file",
        help="Path to file containing the governments JSON data.")
    parser.add_argument('-o', '--output',
        help="Directory for pre-processing results.",
        default='')
    
    return parser.parse_args()


def merge_pollution_data(files, merge_file_path):
    print("Merging air pollution data...")
    with open(set_extension(merge_file_path, '.csv'), mode="w", encoding="utf-8") as output:
        data = []
        for file in files:
            year = file[-8:-4]
            with open(file) as input:
                input.readline()  # skip header
                for line in input:
                    if is_no_state_assigned(line):
                        continue
                    if is_end_of_data(line):
                        break
                    data.append("{};{}".format(year,line))
        
        output.write('\ufeff')  # encode as BOM, see https://stackoverflow.com/questions/5202648/adding-bom-unicode-signature-while-saving-file-in-python/5202815
        output.write("year;state;station_code;station_name;station_surrounding;station_kind;year_average;days_above_limit;days_above_limit_cleaned\n")
        output.writelines(data)


def reformat_pollution_data(file, output_file_path):
    print("Processing air pollution data...")
    with open(file, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        data = {}
        with open(set_extension(output_file_path, '.json'), "w", newline="") as output:
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
                    dataset[field+'_counter'] = dataset.get(field+'_counter', 0) + 1
            
            json.dump(data, output, indent=4, ensure_ascii=False)


def process_pollution_data(
    pollution_data_dir,
    pollution_data_filename_base,
    processing_output_dir
):
    if not os.path.exists(processing_output_dir):
        os.makedirs(processing_output_dir)
    
    pollution_files = sorted(
        [os.path.join(pollution_data_dir, file)
            for file in os.listdir(pollution_data_dir) 
            if get_basename(file) == pollution_data_filename_base and 
                os.path.isfile(os.path.join(pollution_data_dir, file))
        ]
    )

    merge_filename = get_filename(pollution_data_filename_base, '_total')
    merge_file_path = os.path.join(processing_output_dir, merge_filename)
    merge_pollution_data(
        pollution_files,
        merge_file_path
    )

    result_file_path = os.path.join(processing_output_dir, 'processed_pollution_data.json')
    reformat_pollution_data(merge_file_path, result_file_path)

    return result_file_path


def get_government_data(government_data_file, data={}):
    with open(government_data_file) as govfile:
        gov_data = json.load(govfile)
        for state in gov_data:
            if state not in data:
                data[state] = {}
            for year, government in gov_data[state].items():
                if year not in data[state]:
                    data[state][year] = {}
                data[state][year]['government'] = government
    return data


def get_election_data(election_files, data={}):
    for file in election_files:
        with open(file, newline='', encoding="cp1252") as csvfile:
            reader = csv.DictReader(
                csvfile,
                delimiter=';',
                fieldnames=['date', 'area_code', 'area', 'eligible_voters', 'turnout', 'valid_votes', 'cdu_csu', 'spd', 'grüne', 'fdp', 'linke', 'afd', 'other']
            )
            row = {}
            while True:
                row = next(reader)
                if is_date(row['date']):
                    break
            last_date = ''
            while not row['date'] == '':
                if row['date'] == last_date:
                    row = next(reader)
                    continue
                if not is_date(row['date']):
                    break
                last_date = row['date']
                state = get_state(row['area'])
                if not state in data:
                    data[state] = {}
                year = get_year(row['date'])
                if not year in data[state]:
                    data[state][year] = {}
                dataset = data[state][year]
                fields_of_interest = ['date', 'eligible_voters', 'valid_votes', 'cdu_csu', 'spd', 'grüne', 'fdp', 'linke', 'afd', 'other']
                for field in fields_of_interest:
                    value = "0" if row[field] == '-' or row[field] == 'x' else row[field]
                    if not is_date(value):
                        value = int(value)
                    dataset[field] = value
                row = next(reader)
    return data


def process_election_data(
    election_data_dir,
    election_data_filename_base,
    government_data_file,
    processing_output_dir
):
    election_files = [
        os.path.join(election_data_dir, file) 
            for file in os.listdir(election_data_dir) 
            if get_basename(file) == election_data_filename_base and 
                os.path.isfile(os.path.join(election_data_dir, file))
    ]

    print("Processing election data...")
    data = get_government_data(government_data_file)
    data = get_election_data(election_files, data)

    result_file_path = os.path.join(processing_output_dir, 'processed_election_data.json')
    with open(result_file_path, mode="w") as output:
        json.dump(data, output, indent=4, ensure_ascii=False)
    
    return result_file_path


def merge_processed_data(
    processed_pollution_data_filepath,
    processed_election_data_filepath,
    processing_output_dir
):
    print("Merging processed data...")
    results_file_path = os.path.join(processing_output_dir, 'processed_data.json')
    with open(processed_pollution_data_filepath) as pollution_file, \
         open(processed_election_data_filepath) as election_file, \
         open(results_file_path, "w") as output:
        election_data = json.load(election_file)
        pollution_data = json.load(pollution_file)
        result_data = {}
        for state, state_data in pollution_data.items():
            if not state in result_data:
                result_data[state] = {}

            latest_election_year = ''
            for year in state_data.keys():
                if not year in result_data[state]:
                    result_data[state][year] = {
                        "pollution": {},
                        "election": {},
                    }
            
                result_data[state][year]["pollution"] = pollution_data[state][year]
                
                if not state in election_data:
                    continue

                if year in election_data[state] or latest_election_year == '':
                    if latest_election_year == '':
                        for offset in range(1,5):
                            year_candidate = str(int(year) - offset)
                            if year_candidate in election_data[state]:
                                latest_election_year = year_candidate
                                break
                    else:
                        latest_election_year = year
                    result_data[state][year]["election"] = election_data[state][latest_election_year]
        
        json.dump(result_data, output, indent=4, ensure_ascii=False)
    
    return results_file_path


def handle_pre_processing(
    pollution_data_dir,
    election_data_dir,
    government_data_file,
    processing_output_dir,
    pollution_data_filename_base="FS-10.csv",
    election_data_filename_base="WE-Landtag.csv"
):

    processed_pollution_data_filepath = process_pollution_data(
        pollution_data_dir,
        pollution_data_filename_base,
        processing_output_dir
    )

    processed_election_data_filepath = process_election_data(
        election_data_dir,
        election_data_filename_base,
        government_data_file,
        processing_output_dir
    )

    process_result_filepath = merge_processed_data(
        processed_pollution_data_filepath,
        processed_election_data_filepath,
        processing_output_dir
    )

    print("Preprocessing finished. Results are available at:\n{}.".format(process_result_filepath))

    return process_result_filepath


if __name__ == "__main":
    handle_pre_processing(parse_arguments())
