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

def is_leading_in_government(party, election):
    if election == {}:
        return False
    for gov_party in election.get('government', []):
        if party not in election:
            return party == election['government'][0]  # probably leading party
        if election.get(party, 0) < election.get(gov_party, 0):
            return False
    return True


def get_party_name(party):
    colors = {
        'cdu_csu': 'CDU/CSU',
        'spd': 'SPD',
        'grüne': 'Die Grünen',
        'fdp': 'FDP',
        'linke': 'DIE LINKE',
        'afd': 'AfD'
    }

    return colors.get(party, 'Other')


def get_party_color(party, opacity=1):
    other_color = 'rgba(100, 100, 100, {})'

    colors = {
        'cdu_csu': 'rgba(0, 0, 0, {})',
        'spd': 'rgba(255, 0, 0, {})',
        'grüne': 'rgba(50, 200, 0, {})',
        'fdp': 'rgba(255, 240, 0, {})',
        'linke': 'rgba(200, 0, 200, {})',
        'afd': 'rgba(0, 150, 255, {})',
        'nation': 'rgba(65, 140, 245, {})'
    }

    return colors.get(party, other_color).format(opacity)


def get_leading_party(election_data):
    gov_parties = []
    party = election_data['government'][0]
    if party in election_data:
        for party in election_data['government']:
            gov_parties.append((party, election_data[party]))
        party = sorted(gov_parties, key=lambda ps: ps[1], reverse=True)[0][0]
    
    return party


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
