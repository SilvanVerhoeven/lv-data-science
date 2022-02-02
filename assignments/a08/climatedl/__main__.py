import argparse
import collections
import os
import requests
from bs4 import BeautifulSoup

def parse_arguments():
    parser = argparse.ArgumentParser(
        "Download DWD Open Data.")
    parser.add_argument('data_url',
        metavar="data-url",
        help="URL to the folder containing all data files.")
    parser.add_argument('output_dir',
        metavar="output-dir",
        help="Path to output directory of downloaded data.")
    parser.add_argument('-e', '--file-extension',
        dest='extension',
        help="Extension of the files to download (e.g. 'zip'). If none is given, the type is guessed by the URL content.",
        default="")

    return parser.parse_args()


def get_extension(filenames):
    """Returns most often extension in the given filenames."""
    occurences = collections.Counter(
        [os.path.splitext(filename)[1] for filename in filenames])
    return max(occurences, key=occurences.get)[1:]


def download():
    args = parse_arguments()
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    request = requests.get(args.data_url)

    if not request.status_code == 200:
        raise ValueError("Data download failed with HTTP Status Code {}".format(request.status_code))

    soup = BeautifulSoup(request.text, 'html.parser');
    links = [link.get('href') for link in soup.find_all('a') if not link == '../']
    
    extension = '.{}'.format(args.extension or get_extension(links))
    
    for link in links:
        if link.endswith(extension):
            url = os.path.join(args.data_url, link)
            request = requests.get(url)
            if not request.status_code == 200:
                print("({}) Failed to download {}".format(request.status_code, url))
            output_file_name = os.path.join(args.output_dir, link)
            open(output_file_name, 'wb').write(request.content)


if __name__ == '__main__':
    download()
