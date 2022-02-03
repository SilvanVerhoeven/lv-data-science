import argparse
from fileinput import filename
import os
import pandas as pd
import re
from tqdm import tqdm
from datetime import datetime

CONFIG = {
    'SEPERATOR': ';',
    'ENCODING': 'cp1252',  # codec for ANSI encoding
    'REMOVE_LOCATION_COLS': ['Stations_id', 'von_datum', 'bis_datum'],
}

FILENAME_FORMATS = {
    'CLIMATE_DATA': 'produkt_[a-z]{2}_stunde_(\d{8}_\d{8})?_(\d*).txt',
    'LOCATION_DATA': 'Metadaten_Geographie_(\d*).txt',
}


def get_output_filename(station_id, operation_suffix, extension='csv'):
    return 'processed_{:05d}_{}.{}'.format(station_id, operation_suffix, extension)


def parse_arguments():
    parser = argparse.ArgumentParser(
        "Pre-process climate data.")
    parser.add_argument('data_dir',
        metavar="data-dir",
        help="Directory containing the climate data.")
    parser.add_argument('-o', '--output-dir',
        help="Path to output pre-processed files. Same as data directory if unset.",
        default="")
    parser.add_argument('-l', '--location',
        help="Create location files. Merges data files with location files",
        action='store_true')
    parser.add_argument('-r', '--recursive',
        help="If set, all climate data files in data-dir and all its subdirectories are recursively pre-processed.",
        action='store_true')

    return parser.parse_args()


def get_filename(directory, pattern):
    """Returns filename of file in directory matching the regex. Returns None at no matches."""
    
    regex = re.compile(pattern)
    for filename in os.listdir(directory):
        if regex.match(filename):
            return filename
    
    return None


def merge_location_data(data_dir, output_dir):
    """Merges climate data with station location data.
    The output file will be named `station_{station ID}_l.csv`.

    Parameters
    ----------
    data_dir : str
               Directory containing the location and climate data.
    output_dir : str
                 Directory in which the merge result should be placed.
    """

    data_file_path = os.path.join(
        data_dir,
        get_filename(data_dir, FILENAME_FORMATS['CLIMATE_DATA']) or ""
    )
    location_file_path = os.path.join(
        data_dir,
        get_filename(data_dir, FILENAME_FORMATS['LOCATION_DATA']) or ""
    )

    if not os.path.isfile(data_file_path) or not os.path.isfile(location_file_path):
        return

    data = pd.read_csv(data_file_path, sep=CONFIG['SEPERATOR'], encoding=CONFIG['ENCODING'])
    data = data.apply(pd.to_numeric, errors='ignore')
    location = pd.read_csv(location_file_path, sep=CONFIG['SEPERATOR'], encoding=CONFIG['ENCODING'])
    location = location.apply(pd.to_numeric, errors='ignore')
    # The 'bis_datum' value of the latest entry is an empty string and thus must be set to NaN to be handled later
    location['bis_datum'] = location['bis_datum'].apply(pd.to_numeric, errors='coerce')
    location['bis_datum'] = location['bis_datum'].apply(
        lambda val: int(datetime.today().strftime('%Y%m%d')) 
            if pd.isnull(val) else int(val)
    )
    # data['MESS_DATUM'] has the format YYYmmddhh, means we have to take location['von_datum', 'bis_datum'] by 100 to compare them with MESS_DATUM later
    location[['von_datum', 'bis_datum']] = location[['von_datum', 'bis_datum']].apply(lambda val: val*100)

    dl = pd.merge(data, location, how='inner', left_on='STATIONS_ID', right_on='Stations_id')
    data_with_location = dl.loc[(dl['MESS_DATUM'] >= dl['von_datum']) & (dl['MESS_DATUM'] <= dl['bis_datum'])].copy()
    
    data_with_location.drop(CONFIG['REMOVE_LOCATION_COLS'], axis=1, inplace=True)

    station_id = data_with_location.iloc[0, 0]

    data_with_location.to_csv(os.path.join(
        output_dir,
        get_output_filename(station_id, 'l')
    ), index=False)


def process_dir(data_dir, output_dir, processing_steps):
    """Pre-processes climate data in given directory.

    Parameters
    ----------
    data_dir : str
               Directory containing a station's data which should be pre_processed.
    output_dir : str
                 Directory in which the pre-processing results should be placed.
    """

    if processing_steps['merge_location']:
        merge_location_data(data_dir, output_dir)


def pre_process():
    args = parse_arguments()

    processing_steps = {
        'merge_location': args.location,
    }
    
    if not args.recursive:
        process_dir(args.data_dir, args.output_dir or args.data_dir, processing_steps)
    else:
        for dir_path, _, _ in tqdm(os.walk(args.data_dir, topdown=False)):
            output_dir = args.output_dir or dir_path
            process_dir(dir_path, output_dir, processing_steps)

if __name__ == '__main__':
    pre_process()
