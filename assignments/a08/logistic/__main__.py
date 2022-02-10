import argparse
from datetime import datetime
import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score

def parse_arguments():
    parser = argparse.ArgumentParser(
        "Perform logistic regression on data.")
    parser.add_argument('data_path',
        help="Path to file with data (must end on .csv).",
        default=None)
    parser.add_argument('-o', '--output-dir',
        help="Path to directory to put output in.",
        default=None)
    parser.add_argument('-t', '--test-data-path',
        help="Train the model and perform fitness test on given data.",
        default=None)
    
    return parser.parse_args()


def get_label(label_id):
    mapper = {
        'tt_tu': "Lufttemperatur in °C",
        'rf_tu': "Relative Luftfeuchte in %",
        'r1': "Niederschlag in mm",
        'p_std': "Luftdruck in hpa",
        'f': "Windgeschwindigkeit in m/s",
        'fx_911': "Windspitze in der Stunde in m/s",
        'delay': "Verspätung in min",
        'canceled': "Zugausfall (0-nicht ausgefallen, 1-Ausfall m Startbahnhof, 2-Ausfall an Zielbahnhof)"
    }
    return mapper[label_id]


def test(training_data_path, test_data_path):
    """Perform logistic regression on data and test fitness."""

    model = linear_model.LinearRegression()
    
    print("Loading data...")
    training_data = pd.read_csv(training_data_path)
    test_data = pd.read_csv(test_data_path)
    
    base_columns = [
        # 'date','departure_at','arrival_at','train',# 'delay','canceled',
        'tt_tu','rf_tu','r1','p_std','f','fx_911'
    ]
    input_columns = [
        # 'date','departure_at','arrival_at','train',# 'delay','canceled',
        'start_tt_tu','end_tt_tu','start_rf_tu','end_rf_tu','start_r1','end_r1',
        'start_p_std','end_p_std','start_f','end_f','start_fx_911','end_fx_911'
    ]
    output_column = 'canceled'

    print("Portioning data...")
    training_data_without_nan = training_data[~training_data.isnull().any(axis=1)]
    training_data_input = training_data_without_nan[input_columns]
    training_data_output = training_data_without_nan[output_column]

    # Turn dense data frame into sparse data frame. See https://stackoverflow.com/a/70601233/8325653
    sparse_training_data = training_data_input.astype(pd.SparseDtype("float64",0)).sparse.to_coo().tocsr()
    
    print("Training model...")
    model.fit(sparse_training_data, training_data_output.values)

    test_data_without_nan = test_data[~test_data.isnull().any(axis=1)]
    test_data_input = test_data_without_nan[input_columns]
    test_data_output = test_data_without_nan[output_column]

    # Turn dense data frame into sparse data frame. See https://stackoverflow.com/a/70601233/8325653
    sparse_test_data = test_data_input.astype(pd.SparseDtype("float64",0)).sparse.to_coo().tocsr()

    print("Testing model...")
    prediction = model.predict(sparse_test_data)

    # The coefficients
    print("Coefficients: \n", model.coef_)
    # The mean squared error
    print("Mean squared error: %.2f" % mean_squared_error(test_data_output.values, prediction))
    # The coefficient of determination: 1 is perfect prediction
    print("Coefficient of determination: %.2f" % r2_score(test_data_output.values, prediction))

    # Plot outputs
    for index, column in enumerate(base_columns):
        plt.figure(index)

        start_column = "start_{}".format(column)
        end_column = "end_{}".format(column)

        plt.scatter(test_data_input[start_column], test_data_output, color="black", alpha=0.5, s=2)
        plt.scatter(test_data_input[end_column], test_data_output, color="green", alpha=0.5, s=2)
        plt.scatter(test_data_input[start_column], prediction, color="blue", alpha=0.5, s=2)
        plt.scatter(test_data_input[end_column], prediction, color="red", alpha=0.5, s=2)

        plt.xlabel(get_label(column))
        plt.ylabel(get_label(output_column))

        plt.xticks(())
        plt.yticks(())

    plt.show()


def main():
    args = parse_arguments()

    if not args.split_fraction == -1:
        split(args.data_path, args.output_dir, args.split_fraction)

    elif args.test_data_path is not None:
        test(args.data_path, args.test_data_path)

if __name__ == '__main__':
    main()
