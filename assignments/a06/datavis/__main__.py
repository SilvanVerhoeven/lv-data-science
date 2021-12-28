from datavis.preprocess import handle_pre_processing
from datavis.utils import get_filename, get_party_color
import argparse
import json
import pygal
import os

def parse_arguments():
    parser = argparse.ArgumentParser(
        "Build charts.")
    parser.add_argument('-pd', '--pollution-data-dir',
        help="Path to directory containing the raw CSV pollution data files. Expected naming scheme for a file: 'FS-10_YYYY.csv.'",
        default="data/air-pollution")
    parser.add_argument('-ed', '--election-data-dir',
        help="Path to directory containing the raw CSV data files. Expected naming scheme for a file: 'WE-Landtag_STATE.csv'.",
        default="data/election")
    parser.add_argument('-gd', '--government-data-file',
        help="Path to file containing the governments JSON data.",
        default="data/government/governments.json")
    parser.add_argument('-po', '--processing-output',
        help="Directory for pre-processing results.",
        default='data/processed')

    subparsers = parser.add_subparsers()

    # change
    change_parser = subparsers.add_parser('change', help="Build charts that display the change of air pollution relative to the previous value.")
    change_parser.add_argument('-o', '--output',
        help="Directory for build results.",
        default='output/change')
    change_parser.set_defaults(func=build_change_charts)

    # absolute
    change_parser = subparsers.add_parser('absolute', help="Build charts that display the absolute of air pollution data.")
    change_parser.add_argument('-o', '--output',
        help="Directory for build results.",
        default='output/absolute')
    change_parser.set_defaults(func=build_absolute_charts)

    return parser.parse_args()


def build_average_charts(data_file_path, output_dir, chart, callback_title, callback_new_value):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Creating charts...")
    output_basename = os.path.join(output_dir, 'pollution.svg')
    with open(data_file_path) as datafile:
        data = json.load(datafile)
        for state in data.keys():
            chart.title = callback_title(state)
            chart.x_labels = sorted(data[state].keys())[1:]
            
            last_year_pollution = None
            graph_data = []
            last_election = {}
            for dataset in data[state].values():
                pollution = dataset['pollution']
                if not dataset['election'] == {}:
                    last_election = dataset['election']
                year_state_average = pollution.get('year_average', 0) / pollution.get('year_average_counter', 1)
                if last_year_pollution is not None:
                    graph_data.append({
                        'value': callback_new_value(year_state_average, last_year_pollution),
                        'color': get_party_color(last_election)})
                last_year_pollution = year_state_average
            
            chart.add('FM_10', graph_data)
            chart.render_to_file(get_filename(output_basename, '_'+state))

    print("Charts created. Files are available under:\n{}".format(
        os.path.abspath(get_filename(output_basename, '_STATE'))))
    
    return output_dir


def build_absolute_charts(data_file_path, output_dir):
    chart = pygal.Bar()
    build_average_charts(
        data_file_path,
        output_dir,
        chart,
        lambda state: "Average of FS_10 values in "+state,
        lambda current_value, prev_value: current_value)
    return output_dir


def build_change_charts(data_file_path, output_dir):
    chart = pygal.Bar()
    build_average_charts(
        data_file_path,
        output_dir,
        chart,
        lambda state: "Average change of FS_10 values in "+state,
        lambda current_value, prev_value: current_value - prev_value)
    return output_dir


def main():
    args = parse_arguments()

    data_file_path = handle_pre_processing(
        args.pollution_data_dir,
        args.election_data_dir,
        args.government_data_file,
        args.processing_output)

    args.func(data_file_path, args.output)

if __name__ == "__main__":
    main()
