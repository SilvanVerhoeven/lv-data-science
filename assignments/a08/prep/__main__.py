import argparse
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
    'CLIMATE_DATA': 'produkt_[a-z]{2}_stunde_(\d{8}_\d{8})?_(?P<station_id>\d*).txt',
    'LOCATION_DATA': 'Metadaten_Geographie_(?P<station_id>\d*).txt',
    'PROCESSED_LOCATION_DATA': 'processed_(?P<station_id>\d*)_l.csv',
    'PROCESSED_RENAMED_DATA': 'processed_(?P<station_id>\d*)_ln.csv',
    'PROCESSED_CLIMATE_DATA': 'processed_(?P<station_id>\d*)_lnc.csv',
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
    parser.add_argument('-n', '--rename',
        help="Renames column of processed location files. Requires -l to have run first.",
        action='store_true')
    parser.add_argument('-c', '--merge-cl',
        help="Merge all climate data of a station into one file. Requires -ln to have run first.",
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


def get_file_path(file_paths, pattern):
    """Returns file_path in file_paths whose filename is matching the regex. Returns None at no matches."""
    
    regex = re.compile(pattern)
    for file_path in file_paths:
        if regex.match(os.path.basename(file_path)):
            return file_path
    
    return None


def merge_location_data(station_id, data_file_paths, output_dir):
    """Merges climate data with station location data.
    The output file will be named according to `get_output_filename()`.

    Parameters
    ----------
    data_file_paths : str[]
        List containing the location and climate data file path.
    output_dir : str
        Directory in which the merge result should be placed. If empty, result will be placed in the directory of the climate data file.
    """

    data_file_path = get_file_path(data_file_paths, FILENAME_FORMATS['CLIMATE_DATA'])
    location_file_path = get_file_path(data_file_paths, FILENAME_FORMATS['LOCATION_DATA'])

    if data_file_path is None or location_file_path is None:
        return

    output_dir = output_dir or os.path.dirname(data_file_path)

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


def rename_location_data(station_id, data_file_paths, output_dir):
    """Renames columns of pre-processed location data.
    The output file will be named according to `get_output_filename()`.

    Parameters
    ----------
    data_file_paths : str
        List of file paths containing the pre-processed location data files.
    output_dir : str
        Directory in which the merge result should be placed. Will be directory of pre-processed location data file if empty. 
    """

    data_file_path = get_file_path(data_file_paths, FILENAME_FORMATS['PROCESSED_LOCATION_DATA'])

    if not os.path.isfile(data_file_path):
        return
    
    output_dir = output_dir or os.path.dirname(data_file_path)

    try:
        column_map = {
            'STATIONS_ID': 'station_id',
            'MESS_DATUM': 'date',
            'Stationshoehe': 'height',
            'Geogr.Breite': 'latitude',
            'Geogr.Laenge': 'longitude',
            'Stationsname': 'location',
        }

        data = pd.read_csv(data_file_path)
        data.rename(columns=column_map, inplace=True)
        data.rename(columns=str.lower, inplace=True)

        station_id = data.iloc[0, 0]

        data.to_csv(os.path.join(
            output_dir,
            get_output_filename(station_id, 'ln')
        ), index=False)

    except IndexError:
        print("Failed to rename {}".format(data_file_path))


def merge_climate_data(station_id, data_files_paths, output_dir):
    """Merges all given climate data files into one."""

    merged_data = pd.read_csv(data_files_paths[0])

    output_dir = output_dir or os.path.dirname(data_files_paths[0])

    for file_path in data_files_paths[1:]:
        data = pd.read_csv(file_path)
        non_overlapping_columns = data.columns.difference(merged_data.columns).values.tolist()
        merged_data = pd.merge(
            merged_data,
            data[['date']+non_overlapping_columns],
            on='date',
            how='left'
        )
    
    merged_data.to_csv(os.path.join(
        output_dir,
        get_output_filename(station_id, 'lnc')
    ), index=False)


def _get_matching_file_paths(dir, regexes):
    """
    Returns a dict matching a station_id to a list of file paths whose file names match one of the given RegEx patterns.

    Parameters
    ----------
    dir : str
        Directory to search for files in.
    regexes : pattern object[]
        RegEx Pattern Objects to match filenames with.

    Returns
    -------
    Dict station_id : int -> file_paths : str[]
    """

    matches = {}

    for filename in os.listdir(dir):
        file_path = os.path.join(dir, filename)
        if not os.path.isfile(file_path):
            continue
        for regex in regexes:
            match = regex.match(filename)
            if not match:
                continue
            station_id = int(match.group('station_id'))
            matches[station_id] = matches.get(station_id, []) + [file_path]
    
    return matches


def get_file_paths(root_dir, patterns, recursive=False):
    """
    Returns a dict matching a station_id to a list of file paths whose file names matched one of the given RegEx patterns.

    Parameters
    ----------
    root_dir : str
        Directory to search for files in.
    patterns : str[]
        RegEx patterns to match filenames with.
    recursive : bool
        If true, the whole file tree starting in `root_dir` is walked for matches.

    Returns
    -------
    Dict station_id : int -> file_paths : str[]
    """

    res = [re.compile(pattern) for pattern in patterns]

    if not recursive:
        return _get_matching_file_paths(root_dir, res)
    
    all_matches = {}

    for dir_path, _, _ in tqdm(os.walk(root_dir, topdown=False)):
        matches = _get_matching_file_paths(dir_path, res)
        for station_id, file_paths in matches.items():
            all_matches[station_id] = all_matches.get(station_id, []) + file_paths
    
    return all_matches


def get_process_strategy(strategy_id):
    """Returns a strategy for the given strategy_id.
    
    Parameters
    ----------
    strategy_id : 'merge_location' | 'rename_location' | 'merge_climate_data'
        Identifier for one of the available strategies.
    
    Returns
    -------
    Dict function_id : str -> process_function : () => {}
    """

    strategy = {
        'collect_files': lambda data_dir, file_formats, recursive: None,
        'process': lambda station_id, file_paths, output_dir: None
    }

    if strategy_id == 'merge_location':
        strategy['collect_files'] = lambda data_dir, recursive: get_file_paths(
            data_dir,
            [FILENAME_FORMATS['CLIMATE_DATA'], FILENAME_FORMATS['LOCATION_DATA']],
            recursive
        )
        strategy['process'] = merge_location_data
    elif strategy_id == 'rename_location':
        strategy['collect_files'] = lambda data_dir, recursive: get_file_paths(
            data_dir,
            [FILENAME_FORMATS['PROCESSED_LOCATION_DATA']],
            recursive
        )
        strategy['process'] = rename_location_data
    elif strategy_id == 'merge_climate_data':
        strategy['collect_files'] = lambda data_dir, recursive: get_file_paths(
            data_dir,
            [FILENAME_FORMATS['PROCESSED_RENAMED_DATA']],
            recursive
        )
        strategy['process'] = merge_climate_data

    return strategy


def pre_process():
    args = parse_arguments()

    processing_steps = {
        'merge_location': args.location,
        'rename_location': args.rename,
        'merge_climate_data': args.merge_cl,
    }

    for step_id, active in processing_steps.items():
        if not active:
            continue
        print("++ Execute {} ++++++++++".format(step_id))

        strategy = get_process_strategy(step_id)

        print("Collecting files...")
        file_paths_by_station_id = strategy['collect_files'](
            args.data_dir,
            args.recursive
        )

        print("Processing files...")
        for station_id, file_paths in tqdm(file_paths_by_station_id.items()):
                strategy['process'](station_id, file_paths, args.output_dir)

if __name__ == '__main__':
    pre_process()
