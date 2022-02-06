import argparse
from datetime import datetime
import math
import os
import pandas as pd
from tqdm import tqdm

def parse_arguments():
    parser = argparse.ArgumentParser(
        "Merge bahn and climate data.")
    parser.add_argument('bahn_data_path',
        metavar="bahn-data-path",
        help="Path to the file containing bahn data.")
    parser.add_argument('climate_data_dir',
        metavar="climate-data-dir",
        help="Directory containing climate data files.")
    parser.add_argument('geo_data_path',
        metavar="geo-data-path",
        help="Path to the file containing geo data (train stations with their respective coordinates).")
    parser.add_argument('-o', '--output-path',
        help="Path to output merge result (must end on .csv). File will be placed in bahn data directory if left unset.",
        default='')
    parser.add_argument('-m', '--mapping-data-path',
        help="Path to mapping data file (must end on .csv). Mapping data and file will be newly created in geo_data_path directory if unset.",
        default='')
    parser.add_argument('-a', '--annotate-climate',
        help="Annotate the climate data with the nearest train station.",
        action='store_true')
    
    return parser.parse_args()


def get_climate_geo_map(climate_data_dir, geo_data_path, mapping_data_path=''):
    """Creates DataFrame mapping a climate station to the closes train station. Returns path to DataFrame."""

    geo_data = pd.read_csv(geo_data_path, index_col='location')
    climate_geo_data = set()
    mapping_data_path = mapping_data_path or os.path.join(os.path.dirname(geo_data_path), 'geo_climate_map.csv')
    
    if os.path.exists(mapping_data_path) and os.path.isfile(mapping_data_path):
        print("Using cached mapping data...")
        return mapping_data_path

    print("Creating new mapping data ...")
    mapping = pd.DataFrame(columns=['station_id', 'train_station', 'distance'])
    mapping.index.name = 'location'

    print("Collect climate geo data...")
    for filename in tqdm(os.listdir(climate_data_dir)):
        file_path = os.path.join(climate_data_dir, filename)
        climate_data = pd.read_csv(file_path)
        climate_geo_data = set.union(climate_geo_data, set(zip(climate_data['location'], climate_data['station_id'], climate_data['latitude'], climate_data['longitude'])))
    
    print("Create train and climate station mapping...")
    for climate_location in tqdm(climate_geo_data):
        for location, coordinates in geo_data.iterrows():
            lat_diff = abs(climate_location[2] - coordinates['latitude'])
            long_diff = abs(climate_location[3] - coordinates['longitude'])
            distance = math.sqrt(lat_diff ** 2 + long_diff ** 2)
            train_station = location
            climate_station = climate_location[0]
            station_id = climate_location[1]
            if climate_station not in mapping.index or distance < mapping.at[climate_station, 'distance']:
                mapping.at[climate_station, 'station_id'] = station_id
                mapping.at[climate_station, 'train_station'] = train_station
                mapping.at[climate_station, 'distance'] = distance
    
    mapping.to_csv(mapping_data_path)
    
    return mapping_data_path
 

def annotate_climate_data(climate_data_dir, map_path):
    """Adds column with closest train station to climate data."""

    mapping = pd.read_csv(map_path, index_col='location')

    print("Annotate climate data...")
    for filename in tqdm(os.listdir(climate_data_dir)):
        file_path = os.path.join(climate_data_dir, filename)
        climate_data = pd.read_csv(file_path)
        climate_data['train_station'] = None
        for index, row in climate_data.iterrows():
            climate_data.loc[index, 'train_station'] = mapping.at[row['location'], 'train_station']
        climate_data.to_csv(file_path, index=False)


def merge_data(bahn_data_path, climate_data_dir, map_path, output_path):
    """Merges bahn and climate data into one single file."""

    mapping = pd.read_csv(map_path, index_col='location').to_dict(orient='index')
    station_map = {}  # dict mapping a train_station to all closest climate_stations

    print("Reshape map...")
    for climate_station in mapping.values():
        train_station = climate_station['train_station']
        station_id = int(climate_station['station_id'])
        distance = climate_station['distance']
        station_map[train_station] = station_map.get(train_station, []) + [(station_id, distance)]
    
    for train_station, climate_stations in station_map.items():
        station_map[train_station] = sorted(climate_stations, key=lambda station: station[1])
    
    print("Loading bahn data...")
    bahn_data = pd.read_csv(bahn_data_path, sep=';')

    print("Merge data...")
    for train_station, climate_stations in tqdm(station_map.items()):
        for prefix in ['start', 'end']:
            for cl_station in climate_stations:
                station_id = cl_station[0]
                filename = 'processed_{:05d}_lnc.csv'.format(station_id)
                file_path = os.path.join(climate_data_dir, filename)
                cl_data = pd.read_csv(file_path, index_col='date')

                default_cl_cols = ['station_id', 'date', 'eor', 'height', 'latitude', 'longitude', 'location', 'train_station']
                available_cols = list(set(cl_data.columns.values.tolist()) - set(default_cl_cols))
                prefixed_available_cols = ['{}_{}'.format(prefix, col_name.strip()) for col_name in available_cols]

                # insert all available values
                for index, row in bahn_data.iterrows():
                    bahn_datetime_str = row['date'] + row['departure_at' if prefix == 'start' else 'arrival_at']
                    date_time = datetime.strptime(bahn_datetime_str, '%d/%m/%Y%H:%M')
                    cl_datetime = int(datetime.strftime(date_time, '%Y%m%d%H'))
                    for orig_col, prefixed_col in zip(available_cols, prefixed_available_cols):
                        if prefixed_col not in row or row[prefixed_col] is None:
                            bahn_data.loc[index, prefixed_col] = cl_data.at[cl_datetime, orig_col]
    
        bahn_data.to_csv(output_path)


def merge():
    args = parse_arguments()
    map_path = get_climate_geo_map(args.climate_data_dir, args.geo_data_path, args.mapping_data_path)
    if args.annotate_climate:
        annotate_climate_data(args.climate_data_dir, map_path)
    output_path = args.output_path or os.path.join(os.path.dirname(args.bahn_data_path), 'data_total.csv')
    merge_data(args.bahn_data_path, args.climate_data_dir, map_path, output_path)


if __name__ == '__main__':
    merge()
