import argparse
import os
import zipfile

def parse_arguments():
    parser = argparse.ArgumentParser(
        "Unzip a lot of files at once.")
    parser.add_argument('zip_dir',
        metavar="zip-dir",
        help="URL to the folder containing all zip files to decode.")
    parser.add_argument('-o', '--output-dir',
        dest="output_dir",
        help="Path to output directory of decoded data. Inside zip file folder by default.",
        default="")
    parser.add_argument('-r', '--recursive',
        help="If set, all zip files in zip-dir and all its subdirectories are recursively decoded.",
        action='store_true')

    return parser.parse_args()


def unzip_dir(zip_dir, output_dir):
    """Unzip all zip files in a single directory.

    Parameters
    ----------
    zip_dir : str
              Directory of which all contained zip files are unzipped.
    output_dir : str
                 Directory in which all unzipped file directories will be placed.
    """

    zip_files = [file for file in os.listdir(zip_dir) 
        if os.path.isfile(os.path.join(zip_dir, file)) and
        os.path.splitext(file)[1] == '.zip']

    for zip_file_name in zip_files:
        output_zip_dir = os.path.join(output_dir, os.path.splitext(zip_file_name)[0])
        zip_file_path = os.path.join(zip_dir, zip_file_name)
        
        if not os.path.exists(output_zip_dir):
            os.makedirs(output_zip_dir)

        zip_file = zipfile.ZipFile(zip_file_path)
        zip_file.extractall(output_zip_dir)


def unzip():
    args = parse_arguments()
    
    if not args.recursive:
        unzip_dir(args.zip_dir, args.output_dir or args.zip_dir)
    else:
        for dir_path, _, _ in os.walk(args.zip_dir, topdown=False):
            output_dir = args.output_dir or dir_path
            unzip_dir(dir_path, output_dir)

if __name__ == '__main__':
    unzip()
