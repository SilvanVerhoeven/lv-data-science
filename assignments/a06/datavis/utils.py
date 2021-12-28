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

def get_party_color(election_data):
    gov_parties = []
    party = election_data['government'][0]
    if party in election_data:
        for party in election_data['government']:
            gov_parties.append((party, election_data[party]))
        party = sorted(gov_parties, key=lambda ps: ps[1], reverse=True)[0][0]
    color = 'rgb(100, 100, 100)'
    if party == 'cdu_csu':
        color = 'rgb(0, 0, 0)'
    elif party == 'spd':
        color = 'rgb(255, 0, 0)'
    elif party == 'grüne':
        color = 'rgb(50, 200, 0)'
    elif party == 'fdp':
        color = 'rgb(255, 255, 0)'
    elif party == 'linke':
        color = 'rgb(200, 0, 200)'
    elif party == 'afd':
        color = 'rgb(0, 150, 255)'
    return color
