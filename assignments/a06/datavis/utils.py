### File utils ##########

def get_basename(filename):
    """Returns the basename of a filename.

    Given the filename `LK-data_partial.json`, the basename were `LK-data.json`.
    The filename `LK-data.json` has the basename `LK-data.json`.
    The filename `data` has the basename `data`.
    """
    extension_start = filename.index('.') if '.' in filename else 0
    prefix_end = filename.index('_') if '_' in filename else 0
    return filename[:prefix_end] + filename[extension_start:]


def get_filename(basename, suffix='', extension=None):
    """Returns the filename according to a basename.

    Given the basename `LK-data.json`, a suffix `_total` and an extension `.csv`, the filename were `LK-data_total.csv`.

    Parameters
    ----------
    basename
        Basename used for filename. Extension required.

    suffix
        Inserted after basename without extension and before extension.
    
    extension
        Extension used in filename. Overwrites extension of basename.
    """
    extension_start = basename.index('.')
    extension = basename[extension_start:] if extension is None else extension
    return basename[:extension_start] + suffix + extension


def set_extension(filename, extension):
    """Returns filename with given extension. The filename does not need to have an extension beforehand.
    
    """
    filename_without_extension = filename
    if '.' in filename:
        extension_start = filename.index('.')
        filename_without_extension = filename[:extension_start]
    return filename_without_extension + extension


### CSV parsing utils ##########

def is_end_of_data(line):
    # empty line only consists of '\n' and denotes end of data
    return line == '\n'


def is_no_state_assigned(line):
    # 'UBA' means that the data point was entered by Umweltbundesamt, which is not assigned to a state
    return line.startswith("UBA;")


### Type verification ##########

def is_date(str):
    if not len(str) == 10:
        return False
    check_numbers = str[0:2] + str[3:5] + str[6:]
    check_dots = str[2] + str[5]
    return check_dots == '..' and check_numbers.isnumeric()


### Data parsing ##########

def get_year(date_str):
    return date_str[6:]


def get_state(str):
    return str[:str.index(',')] if ',' in str else str


### Party handling ##########

def is_biggest_in_government(party, election):
    if election == {}:
        return False
    for gov_party in election.get('government', []):
        if party not in election:
            return party == election['government'][0]  # probably biggest party
        if election.get(party, 0) < election.get(gov_party, 0):
            return False
    return True


def get_party_color(part_name, opacity=1):
    color = 'rgba(100, 100, 100, {})'

    if part_name == 'cdu_csu':
        color = 'rgba(0, 0, 0, {})'
    elif part_name == 'spd':
        color = 'rgba(255, 0, 0, {})'
    elif part_name == 'grüne':
        color = 'rgba(50, 200, 0, {})'
    elif part_name == 'fdp':
        color = 'rgba(255, 240, 0, {})'
    elif part_name == 'linke':
        color = 'rgba(200, 0, 200, {})'
    elif part_name == 'afd':
        color = 'rgba(0, 150, 255, {})'

    return color.format(opacity)


def get_party_color_by_election(election_data):
    gov_parties = []
    party = election_data['government'][0]
    if party in election_data:
        for party in election_data['government']:
            gov_parties.append((party, election_data[party]))
        party = sorted(gov_parties, key=lambda ps: ps[1], reverse=True)[0][0]
    
    return get_party_color(party)


def sort_by_popularity(parties):
    order = {
        'cdu_csu': 0,
        'spd': 1,
        'grüne': 2,
        'fdp': 3,
        'linke': 4,
        'other': 5,
    }
    sorted_parties = [None] * len(order.keys())
    for party, value in parties.items():
        party_index = order.get(party, None)
        if party_index is not None:
            sorted_parties[party_index] = (party, value)
        else:
            sorted_parties.append((party, value))
    return [item for item in sorted_parties if item is not None]
