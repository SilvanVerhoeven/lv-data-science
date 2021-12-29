# DataVis

DataVis lets you create various visualizations of air pollution data in combination with government data.

## Installation

1. Copy the folder `datavis` and its content to a designated location.
2. Enter the folder: `cd datavis`.
3. Install dependencies: `pip install -r requirements.txt`.

## Usage

You can start DataVis with several commands, which create different types of charts.

```bash

# create all available chart types at once
python3 -m datavis all

# create charts showing absolute air pollution values per state
python3 -m datavis absolute

# create charts showing relative changes of air pollution values per state
python3 -m datavis changes

# create chart showing the overall impact of all parties on air pollution
python3 -m datavis impact
```

### Parameters

DataVis offers several optional parameters to control things like directories containing the data files or the output files for the charts. Some charts also support the optional display of the nation-wide average next to the state-specific values.

To see all available commands and parameters, run `python3 -m datavis -h`. To see command-specific options, run `python3 -m datavis COMMAND -h`.

## Data Input Structure

DataVis expects the following data input files.

### Air Pollution Data

One CSV file per year, all in one folder. Expected filename format: `FS-10_YYYY.csv`, e.g. `FS-10_2020.csv`.

The following file structure is expected (the header names can be different, as long as the semantic and order is correct):

```csv
state;station_code;station_name;kind_of_station_sourrounding;kind_of_station;yearly_average_in_µg/m³;days_above_50_µg/m3;days_above_50_µg/m3_cleaned
Baden-Württemberg;DEBW004;Eggenstein;ländlich stadtnah;Hintergrund;22;10;-
Bayern;DEBY120;Nürnberg/Von-der-Tann-Straße;städtisches Gebiet;Verkehr;24;6;4
...
```

### Election Data

One CSV file per state, all in one folder. Expected filename format: `WE-Landtag_[State].csv`, e.g. `WE-Landtag_Brandenburg.csv`.

The following file structure is expected (there is no header expected as long as the semantic and order of the values is identical).

**Notice** that

- the metadata at the top and bottom is separated by at least one blank line.
- the first line of a date must contain the state-wide results, following lines with the same date usually contain district results and are skipped.
- `-` is a valid input vor voter numbers to make clear if a party was not part of the election at that time

```csv
Some Information
Metadata
etc...

year;zip_code;district;no_eligible_voters;turnout_percent;no_voters;votes_cdu_csu;votes_spd;votes_grüne;votes_fdp;votes_linke;votes_afd;votes_other
01.09.2019;12;Brandenburg;2088592;61,3;1265106;196988;331238;136364;51660;135558;297484;115814
01.09.2019;12051;Brandenburg an der Havel, kreisfreie Stadt;59696;52,6;30928;5378;7950;3672;1115;3131;6659;3023
01.09.2019;12052;Cottbus, kreisfreie Stadt;79600;61,6;48435;7467;11967;4001;2733;5274;13003;3990
01.09.2019;12053;Frankfurt (Oder), kreisfreie Stadt;45561;55,7;25052;3744;5833;2270;953;4385;6138;1729
01.09.2019;12054;Potsdam, kreisfreie Stadt;137613;69,3;94585;11356;24639;21019;4335;13545;12902;6789
01.09.2019;12060;Barnim, Landkreis;154732;59,2;90425;12242;21120;9526;2652;11807;20414;12664
...
14.09.2014;12;Brandenburg;2094458;47,9;987321;226835;315202;60767;14376;183178;120077;66886
14.09.2014;12051;Brandenburg an der Havel, kreisfreie Stadt;61179;38,2;23008;5737;8341;1342;229;4045;2378;936
...
11.09.1994;12073;Uckermark, Landkreis;121555;49,6;59285;11581;33580;1522;1173;10108;-;1321

Some Footer Data
```

### Government Data

One JSON file for all governments. No filename format expected, the file path must be denoted in the software.

The following file structure is expected:

```json
{
	"[state]": {
		"[YYYY]": [
			"[government party 1]",
			"[government party 2",
			...
		],
		"1996": [
			"cdu_csu",
			"fdp"
		],
		"2001": [
			"cdu_csu"
		],
		...
		"2021": [
			"grüne",
			"cdu_csu"
		]
	},
	"Bayern": {
		"1990": [
		...
		]
	}
}
```