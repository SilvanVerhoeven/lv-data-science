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
        "Merge bahn and climate data.")
    parser.add_argument('-b', '--bahn-data-dir',
        help="Path to the directory containing bahn data files. Leave unset to not merge any data, but perform another operation.",
        default=None)
    parser.add_argument('-e', '--handle-end',
        help="If true, the selected operation is performed on the end column. Otherwise the start column.",
        action='store_true')
    parser.add_argument('-c', '--climate-data-dir',
        help="Directory containing climate data files.",
        default=None)
    parser.add_argument('-g', '--geo-data-path',
        help="Path to the file containing geo data (train stations with their respective coordinates).",
        default=None)
    parser.add_argument('-o', '--output-path',
        help="Path to output merge result (must end on .csv). File will be placed in bahn data directory if left unset.",
        default='')
    parser.add_argument('-d', '--output-dir',
        help="Path to output directory.",
        default='')
    parser.add_argument('-m', '--mapping-data-path',
        help="Path to mapping data file (must end on .csv). Mapping data and file will be newly created in geo_data_path directory if unset.",
        default='')
    parser.add_argument('-s', '--sort-bahn-data-path',
        help="Path to bahn data file which should be sorted (must end on .csv).",
        default=None)
    parser.add_argument('-t', '--split-bahn-data-path',
        help="Path to bahn data file being split.",
        default=None)
    parser.add_argument('-p', '--number-of-partitions',
        help="Number of directories to partition bahn_data_dir files into.",
        default=0, type=int)
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


def sort_data(bahn_data_path, output_path, prefix):
    """Sorts bahn_data by either start or end station."""

    print("Loading bahn data...")
    bahn_data = pd.read_csv(bahn_data_path, sep=';' if prefix == 'start' else ',')
    
    station_column = '{}_station'.format(prefix)

    print("Sorting bahn data by {}...".format(station_column))
    bahn_data.sort_values(station_column, inplace=True)
    sorted_bahn_data = bahn_data

    print("Writing sorted bahn data...")
    sorted_bahn_data.to_csv(output_path, index=False)
    
    print("Finished sorting.")


def split(bahn_data_path, output_dir, split_column):
    def clean(value):
        cleaned = ''
        for char in value.lower():
            cleaned += char if char.isalpha() else '-'
        return cleaned

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print("Loading bahn data...")
    sorted_bahn_data = pd.read_csv(bahn_data_path)
    values = list(sorted_bahn_data[split_column].unique())

    print("Splitting data...")
    for value in tqdm(values):
        data = sorted_bahn_data[sorted_bahn_data[split_column] == value]
        output_path = os.path.join(output_dir, "bahn_data_split_{}_{}.csv".format(split_column, clean(value)))
        data.to_csv(output_path, index=False)


def partition(bahn_data_dir, number_of_partitions):
    """Partition the files in the given directory into `number_of_partition` partitions."""

    filenames = set([filename for filename in os.listdir(bahn_data_dir) if os.path.isfile(os.path.join(bahn_data_dir, filename))])
    files_total = len(filenames)
    files_per_partition = files_total // number_of_partitions

    for index in range(number_of_partitions):
        print("Create partition {}/{}...".format(index+1, number_of_partitions))
        partition_dir = os.path.normpath(bahn_data_dir) + '_{}'.format(index)
        if not os.path.exists(partition_dir):
            os.makedirs(partition_dir)
        
        if index==number_of_partitions-1:
            partition_files = filenames
        else:
            partition_files = set(random.sample(filenames, files_per_partition))
            filenames -= partition_files
        
        for filename in tqdm(partition_files):
            file_path = os.path.join(bahn_data_dir, filename)
            output_path = os.path.join(partition_dir, filename)
            shutil.move(file_path, output_path)
    
    print("Data partitioned.")



def merge_data(bahn_data_dir, climate_data_dir, map_path, output_path, prefix):
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

    all_columns = [
        'date','start_station','end_station','departure_at','arrival_at','train','delay','delay_category','canceled',
        'start_tf_std','start_v_te002','start_v_te020','start_rs_ind','start_absf_std','start_tt_std','start_qn_8','start_qn_3',
        'start_vp_std','start_qn_2','start_d','start_v_te100','start_f','start_v_te005','start_v_te010','start_fx_911','start_td_std',
        'start_qn_9','start_p_std','start_rf_std','start_r1','start_rf_tu','start_wrtr','start_v_te050','start_tt_tu',
        'end_tf_std','end_v_te002','end_v_te020','end_rs_ind','end_absf_std','end_tt_std','end_qn_8','end_qn_3',
        'end_vp_std','end_qn_2','end_d','end_v_te100','end_f','end_v_te005','end_v_te010','end_fx_911','end_td_std',
        'end_qn_9','end_p_std','end_rf_std','end_r1','end_rf_tu','end_wrtr','end_v_te050','end_tt_tu',
    ]

    print("Merging {}...".format(prefix))

    open_mode = 'w'
    filenames = os.listdir(bahn_data_dir)
    lap = 0
    lap_total = len(filenames)
    for filename in filenames:
        file_path = os.path.join(bahn_data_dir, filename)
        lap += 1
        print("Processing file {}/{}: {}".format(lap, lap_total, file_path))

        if not '_{}_'.format(prefix) in filename:
            continue
            
        bahn_data = pd.read_csv(file_path)

        new_cols = list(set(all_columns) - set(bahn_data.columns.values.tolist()))

        for column in new_cols:
            bahn_data[column] = NaN

        train_station = bahn_data.loc[0, '{}_station'.format(prefix)]

        filled_columns = []

        if train_station not in station_map:
            continue

        for cl_station in station_map[train_station]:
            station_id = cl_station[0]
            filename = 'processed_{:05d}_lnc.csv'.format(station_id)
            file_path = os.path.join(climate_data_dir, filename)
            cl_data = pd.read_csv(file_path, index_col='date')

            default_cl_cols = ['station_id', 'date', 'eor', 'height', 'latitude', 'longitude', 'location', 'train_station']
            available_cols = list(set(cl_data.columns.values.tolist()) - set(default_cl_cols))
            new_cols = list(set(available_cols) - set(filled_columns))
            if new_cols == []:
                continue
            prefixed_available_cols = ['{}_{}'.format(prefix, col_name.strip()) for col_name in new_cols]
            filled_columns += new_cols

            # insert all available values
            for index in tqdm(range(len(bahn_data.index))):
                bahn_datetime_str = bahn_data.loc[index, 'date'] + \
                    bahn_data.loc[index, 'departure_at' if prefix == 'start' else 'arrival_at']
                date_time = datetime.strptime(bahn_datetime_str, '%d/%m/%Y%H:%M')
                cl_datetime = int(datetime.strftime(date_time, '%Y%m%d%H'))
                for orig_col, prefixed_col in zip(new_cols, prefixed_available_cols):
                    try:
                        bahn_data.loc[index, prefixed_col]
                    except KeyError:
                        open('data/missing_cols.log', 'a').write(prefixed_col+'\n')
                    if math.isnan(bahn_data.loc[index, prefixed_col]):
                        try:
                            value = cl_data.at[cl_datetime, orig_col]
                        except KeyError:
                            continue
                        else:
                            bahn_data.loc[index, prefixed_col] = value

        open(output_path, open_mode, encoding="utf-8").write(bahn_data.to_csv(index=False, header=open_mode=='w', line_terminator='\n'))
        open_mode = 'a'
    
    print("Merging of {} finished.".format(prefix))


def merge():
    args = parse_arguments()

    prefix = 'end' if args.handle_end else 'start'

    map_path = args.mapping_data_path
    if args.geo_data_path is not None:
        map_path = get_climate_geo_map(args.climate_data_dir, args.geo_data_path, args.mapping_data_path)
    
    if args.sort_bahn_data_path is not None:
        output_path = args.output_path or os.path.join(os.path.dirname(args.sort_bahn_data_path), 'bahn_data_sorted_{}.csv'.format(prefix))
        sort_data(args.sort_bahn_data_path,output_path,  prefix)

    if args.split_bahn_data_path is not None and not args.handle_end:
        split(args.split_bahn_data_path, args.output_dir, 'start_station')
    
    if args.split_bahn_data_path is not None and args.handle_end:
        split(args.split_bahn_data_path, args.output_dir, 'end_station')
    
    if args.number_of_partitions > 0:
        partition(args.bahn_data_dir, args.number_of_partitions)
    
    # else:
        
    #     if args.annotate_climate:
    #         annotate_climate_data(args.climate_data_dir, map_path)

    if args.bahn_data_dir is not None and args.number_of_partitions == 0:
        output_path = args.output_path or os.path.join(args.bahn_data_dir, 'data_total.csv')
        merge_data(args.bahn_data_dir, args.climate_data_dir, map_path, output_path, prefix)


if __name__ == '__main__':
    merge()
