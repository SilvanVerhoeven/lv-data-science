import argparse
import os
import pandas as pd
import requests
from tqdm import tqdm

def parse_arguments():
    parser = argparse.ArgumentParser(
        "Download Geo Data for Train Stations.")
    parser.add_argument('data_path',
        metavar="data-path",
        help="Path to the file containing bahn data.")
    parser.add_argument('-o', '--output-dir',
        help="Directory to output downloaded Geo Data and merged Bahn data. Result will be placed in directory of `data_path` if unset.",
        default='')
    parser.add_argument('-g', '--geo-data-path',
        help="Path to file with downloaded Geo data. If unset, Geo Data will be downloaded again.",
        default=None)
    parser.add_argument('-a', '--api-url',
        help="URL to the Geo Data API endpoint.",
        default="https://api.opencagedata.com/geocode/v1/json")
    parser.add_argument('-k', '--key',
        help="API key.",
        default="7c4214523aed4b3bb8861d85d76f719a")
    
    return parser.parse_args()


def download():
    args = parse_arguments()

    output_dir = args.output_dir or os.path.dirname(args.data_path)
    output_path = os.path.join(output_dir, "bahn_geo_data.csv")
    geo_output_path = os.path.join(output_dir, "geo_data.csv")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print("Reading bahn data...")
    bahn_data = pd.read_csv(args.data_path, sep=';')
    locations = pd.concat([bahn_data['start_station'], bahn_data['end_station']]).unique()
    
    bahn_data[[
        'start_latitude',
        'end_latitude',
        'start_longitude',
        'end_longitude'
    ]] = None

    if args.geo_data_path is not None:
        geo_data = pd.read_csv(args.geo_data_path)

    else:
        raw_geo_data = {}

        print("Querying geo data...")
        for location in tqdm(locations):        
            params = {
                'q': location,
                'key': args.key,
                'no_annotations': 1,  # do not request additional annotations to make query faster
                'language': 'de'
            }

            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0',
            }

            request = requests.get(args.api_url, params=params, headers=headers)
            
            if not request.status_code == 200:
                raise ValueError("({}) Download failed for {}".format(request.status_code, location))
            
            fetched_coordinates = request.json()['results'][0]['geometry']
            raw_geo_data[location] = [fetched_coordinates['lat'], fetched_coordinates['lng']]
        
        print("Download finished.")

        geo_data = pd.DataFrame.from_dict(raw_geo_data, orient='index', columns=['latitude', 'longitude'])
        geo_data.index.name = 'location'
        geo_data.to_csv(geo_output_path)

    print("Merging geo data...")
    for _, row in tqdm(geo_data.iterrows()):
        location = row['location']
        for prefix in ['start', 'end']:
            location_applys = bahn_data['{}_station'.format(prefix)] == location
            for coordinate in ['latitude', 'longitude']:
                column = '{}_{}'.format(prefix, coordinate)
                bahn_data.loc[location_applys, column] = row[coordinate]
    
    print("Merging finished. Writing data...")
    bahn_data.to_csv(output_path, index=False)

    print("Process finished.")

if __name__ == '__main__':
    download()
