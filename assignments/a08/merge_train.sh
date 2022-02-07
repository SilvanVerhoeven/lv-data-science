#!/bin/bash

python3.9 -m merge -s=data/bahn_data_test.csv
python3.9 -m merge -t=data/bahn_data_sorted_start.csv -d=data/bahn_data_test_split_start
python3.9 -m merge -b=data/bahn_data_test_split_start -c=data/dwd-lnc -o=data/bahn_data_test_total_start.csv -m=data/geo_climate_map.csv

python3.9 -m merge -s=data/bahn_data_test_total_start.csv -e
python3.9 -m merge -t=data/bahn_data_sorted_end.csv -d=data/bahn_data_test_split_end -e
python3.9 -m merge -b=data/bahn_data_test_split_end -c=data/dwd-lnc -o=data/bahn_data_test_total.csv -m=data/geo_climate_map.csv -e