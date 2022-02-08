import argparse
from datetime import datetime
import math
import os
import random
import shutil
from numpy import NaN
import pandas as pd
from tqdm import tqdm

def parse_arguments():
    parser = argparse.ArgumentParser(
        "Evaluate bahn data.")
    parser.add_argument('-b', '--bahn-data-dir',
        help="Path to the directory containing bahn data files.",
        default=None)
    parser.add_argument('-c', '--count-output-path',
        help="Path to the file that contains the output of data counting (must end on .csv).",
        default=None)
    
    return parser.parse_args()


def count(bahn_data_dir, output_path):
    """Count the number of pairs of train_stations in the bahn data."""

    count = {}

    filenames = os.listdir(bahn_data_dir)
    for file_index, filename in enumerate(filenames):
        print("Counting file {}/{}: {}".format(file_index+1, len(filenames), filename))
        file_path = os.path.join(bahn_data_dir, filename)
        bahn_data = pd.read_csv(file_path)
        
        for index in tqdm(range(len(bahn_data.index))):
            start_station = bahn_data.at[index, "start_station"]
            end_station = bahn_data.at[index, "end_station"]
            station_counter = count.get(start_station, {})
            station_counter[end_station] = station_counter.get(end_station, 0) + 1
            count[start_station] = station_counter
        
        count_data = pd.DataFrame(columns=['start_station', 'end_station', 'number_of_journeys'])

        for start_station, data in count.items():
            for end_station, number_of_journeys in data.items():
                new_data = pd.DataFrame({
                    'start_station': [start_station],
                    'end_station': [end_station],
                    'number_of_journeys': [number_of_journeys]
                })
                count_data = pd.concat([count_data, new_data])
        
        count_data.sort_values(by=['number_of_journeys', 'start_station', 'end_station'], ascending=[False, True, True], inplace=True)
        count_data.to_csv(output_path, index=False)

    print("Counting finished.")


def eval():
    args = parse_arguments()

    if args.count_output_path is not None:
        output_path = args.count_output_path or os.path.join(args.bahn_data_dir, 'data_count.csv')
        count(args.bahn_data_dir, output_path)


if __name__ == '__main__':
    eval()
