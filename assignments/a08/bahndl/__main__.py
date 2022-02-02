import argparse
import json
import os
import pandas
import requests

def parse_arguments():
    parser = argparse.ArgumentParser(
        "Download Bahn Data Quickly.")
    parser.add_argument('data_url',
        metavar="data-url",
        help="URL to the Bahn API endpoint.")
    parser.add_argument('output_path',
        metavar="output-path",
        help="Path to output file of downloaded data (needs .csv extension).")
    parser.add_argument('-s', '--start',
        help="Index of first entry to query.",
        type=int,
        default=0)
    parser.add_argument('-o', '--overwrite',
        help="Overwrite output file if present.",
        action='store_true')
    parser.add_argument('-e', '--entries-per-request',
        help="Number of table entries to query per request.",
        type=int,
        default=10000)
    parser.add_argument('-n', '--nonce',
        help="WDT Nonce that will be sent with the request.",
        default="fd7361d203")

    return parser.parse_args()


def download():
    args = parse_arguments()
    
    if not os.path.exists(os.path.dirname(args.output_path)):
        os.makedirs(os.path.dirname(args.output_path))
    
    start = args.start
    data_fetched = True
    open_mode = 'w' if start == 0 or args.overwrite else 'a'

    while data_fetched:
        print("Querying {}...".format(start), end="\r")
        
        payload = {
            'draw': 8,
            'start': start,
            'length': args.entries_per_request,
            'wdtNonce': args.nonce
        }
        cookies = {
            'wordpress_logged_in_368dc516f0d1b637edd28ca58fa0cafc': 'verhoevens|1644927019|j5VPv9RELi4brk6VVsjxijWV2dkhdetmGJT4JsQUP1R|ca0e2bb89643800f677d3df10975556221531b93da834992dbb99af6b8d0eb23',
            'wordpress_sec_368dc516f0d1b637edd28ca58fa0cafc': '6e7b52a81ead8a407bedf003e19c56c32dd62fb30b15a6e704cc76340d9ad371'
        }

        request = requests.post(args.data_url, cookies=cookies, data=payload)
        
        if not request.status_code == 200:
            raise ValueError("({}) Download failed: {}, {}, {}".format(request.status_code, start, args.entries_per_request, args.nonce))
        
        fetched_data = request.json()['data']
        data_fetched = bool(fetched_data)

        with open(args.output_path, open_mode) as output:
            dataframe = pandas.read_json(json.dumps(fetched_data))
            output.write(dataframe.to_csv(sep=';', index=False, header=start==0))
    
        open_mode = 'a'
        start += args.entries_per_request
    
    print("Download finished. {} entries downloaded.".format(start-args.entries_per_request-1))

if __name__ == '__main__':
    download()
