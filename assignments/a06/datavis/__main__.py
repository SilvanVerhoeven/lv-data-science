from datavis.preprocess import handle_pre_processing
from datavis.utils import get_filename, get_party_color, get_party_color_by_election, is_biggest_in_government, sort_by_popularity
import argparse
import json
import os
import pygal
from pygal.style import Style
import statistics

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

    DEFAULTS = [
        'output/absolute',
        'output/change',
        'output/misc'
    ]

    # all
    all_parser = subparsers.add_parser('all', help="Build all available charts at once.")
    all_parser.add_argument('-o', '--output',
        help="Directory for build results.",
        default=DEFAULTS)
    all_parser.add_argument('-a', '--average',
        help="Show nation-wide air-pollution average.",
        action='store_true')
    all_parser.set_defaults(func=build_all_charts)

    # change
    change_parser = subparsers.add_parser('change', help="Build charts that display the change of air pollution relative to the previous value.")
    change_parser.add_argument('-o', '--output',
        help="Directory for build results.",
        default=DEFAULTS[1])
    change_parser.add_argument('-a', '--average',
        help="Show nation-wide air-pollution average.",
        action='store_true')
    change_parser.set_defaults(func=build_change_charts)

    # absolute
    absolute_parser = subparsers.add_parser('absolute', help="Build charts that display the absolute of air pollution data.")
    absolute_parser.add_argument('-o', '--output',
        help="Directory for build results.",
        default=DEFAULTS[0])
    absolute_parser.add_argument('-a', '--average',
        help="Show nation-wide air-pollution average.",
        action='store_true')
    absolute_parser.set_defaults(func=build_absolute_charts)

    # party impact
    absolute_parser = subparsers.add_parser('impact', help="Build charts that display the impact of parties on air pollution.")
    absolute_parser.add_argument('-o', '--output',
        help="Directory for build results.",
        default=DEFAULTS[2])
    absolute_parser.set_defaults(func=build_party_impact_chart)

    return parser.parse_args()


def get_yearly_air_pollution_of_all_states(data_file_path):
    result = {}
    fields_of_interest = ['year_average', 'days_above_limit', 'days_above_limit_cleaned']
    with open(data_file_path) as datafile:
        data = json.load(datafile)
        for state in data.keys():
            for year in data[state]:
                if year not in result:
                    result[year] = {}
                for field in fields_of_interest:
                    result[year][field] = result[year].get(field, []) + \
                        [data[state][year]['pollution'][field] / data[state][year]['pollution'][field+'_counter']]
    return result


def get_nation_median_air_pollution(data_file_path):
    result = {}
    data = get_yearly_air_pollution_of_all_states(data_file_path)
    
    # calulcate median
    for year in data:
        if year not in result:
            result[year] = {}
        for field in data[year]:
            result[year][field] = statistics.median(data[year].get(field, [0]))
    
    return result


def get_nation_median_air_pollution_change(data_file_path):
    result = {}
    data = get_yearly_air_pollution_of_all_states(data_file_path)
    
    # calulcate median
    last_year_pollutions = data[min(data.keys())]
    for year in data:
        if year not in result:
            result[year] = {}
        for field in data[year]:
            result[year][field] = statistics.median(
                [this_year-last_year for this_year, last_year in zip(
                    data[year].get(field, [0]), last_year_pollutions.get(field, [0]))])
        last_year_pollutions = data[year]

    return result


def build_average_charts(data_file_path, output_dir, show_average, callback_build_chart, callback_title, callback_new_value, callback_nation_value):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if show_average:
        nation_graph = callback_nation_value(data_file_path)

    output_basename = os.path.join(output_dir, 'pollution.svg')
    with open(data_file_path) as datafile:
        data = json.load(datafile)
        for state in data.keys():
            chart = callback_build_chart()
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
                        'color': get_party_color_by_election(last_election)})
                last_year_pollution = year_state_average
            
            chart.add(state, graph_data)
            if show_average:
                chart.add('Nation', [ds['year_average'] for ds in nation_graph.values()][1:])
            chart.render_to_file(get_filename(output_basename, '_'+state))

    print("Charts created. Files are available under:\n{}".format(
        os.path.abspath(get_filename(output_basename, '_STATE'))))
    
    return output_dir


def build_absolute_charts(data_file_path, output_dir, **kwargs):
    def build_chart():
        return pygal.Bar()

    print("Creating absolute charts...")
    build_average_charts(
        data_file_path,
        output_dir,
        kwargs['show_average'],
        build_chart,
        lambda state: "Average of FS_10 values in "+state,
        lambda current_value, prev_value: current_value,
        get_nation_median_air_pollution)
    return output_dir


def build_change_charts(data_file_path, output_dir, **kwargs):
    def build_chart():
        return pygal.Bar()
    
    print("Creating change charts...")
    build_average_charts(
        data_file_path,
        output_dir,
        kwargs['show_average'],
        build_chart,
        lambda state: "Average change of FS_10 values in "+state,
        lambda current_value, prev_value: current_value - prev_value,
        get_nation_median_air_pollution_change)
    return output_dir


def build_party_impact_chart(data_file_path, output_dir, **kwargs):
    def build_chart():
        chart = pygal.Box()
        chart.title = "Parties' Impact on Air Pollution"
        chart.x_title = "Nationwide yearly average changes of air pollution values in \
            years in which the respective party is part of the government (alternative row: in which party is the biggest in government)."  # abuse x axis as description
        chart.y_title = "Yearly change of PM10 concentration in µg/m³"
        return chart
    
    print("Creating party impact chart...")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    party_data = {
        'part': {},
        'biggest' : {}
    }

    # aggregate values per party
    with open(data_file_path) as jsonfile:
        data = json.load(jsonfile)
        for state in data:
            last_year = min(data[state].keys())
            election = {}
            for year in data[state]:                    
                dataset = data[state][year]['pollution']
                prev_dataset = data[state][last_year]['pollution']
                relative_pollution_change = dataset.get('year_average', 0) / dataset.get('year_average_counter', 1) - \
                    prev_dataset.get('year_average', 0) / prev_dataset.get('year_average_counter', 1)
                if abs(relative_pollution_change) > 50:
                    print(state, year, relative_pollution_change)
                
                election_candidate = data[state][year].get('election', {})
                if not election_candidate == {}:
                    election = election_candidate

                for party in election.get('government', []):                    
                    if is_biggest_in_government(party, election):
                        party_data['biggest'][party] = party_data['biggest'].get(party, []) + [relative_pollution_change]
                    party_data['part'][party] = party_data['part'].get(party, []) + [relative_pollution_change]

                last_year = year
        
        chart = build_chart()
        party_colors = []
        for party, values in sort_by_popularity(party_data['part']):
            chart.add(party, [{'value': value, 'label': '{} years in government'.format(len(values))} for value in values])
            chart.add(party + ' (biggest)', [{'value': value, 'label': '{} years in government'.format(len(party_data['biggest'].get(party, [])))} for value in party_data['biggest'].get(party, [])])
            party_colors.append(get_party_color(party))
            party_colors.append(get_party_color(party, 0.4))
        chart.style = Style(colors=party_colors)
    
    output_file_path = os.path.join(output_dir, 'pollution_impact_all_parties.svg')
    chart.render_to_file(output_file_path)
    print("Chart created. File is available under:\n{}".format(
        os.path.abspath(output_file_path)))

    return output_dir


def build_all_charts(data_file_path, output_dirs, show_average):
    build_absolute_charts(data_file_path, output_dirs[0], show_average)
    build_change_charts(data_file_path, output_dirs[1], show_average)
    build_party_impact_chart(data_file_path, output_dirs[2])


def main():
    args = parse_arguments()

    data_file_path = handle_pre_processing(
        args.pollution_data_dir,
        args.election_data_dir,
        args.government_data_file,
        args.processing_output)

    args.func(data_file_path, args.output, **vars(args))

if __name__ == "__main__":
    main()
