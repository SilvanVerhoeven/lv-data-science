import argparse
from datetime import datetime
from distutils.cygwinccompiler import Mingw32CCompiler
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score

def parse_arguments():
    parser = argparse.ArgumentParser(
        "Perform logisitc regression on data.")
    parser.add_argument('data_path',
        help="Path to file with data (must end on .csv).",
        default=None)
    parser.add_argument('-o', '--output-dir',
        help="Path to directory to put output in.",
        default=None)
    parser.add_argument('-s', '--split-fraction',
        help="Split data in training and test data, training data should have the given fraction (0..1).",
        default=-1, type=float)
    parser.add_argument('-t', '--test-data-path',
        help="Train the model and perform fitness test on given data.",
        default=None)
    parser.add_argument('-tl', '--test-logistic-data-path',
        help="Train the logistic regression model and perform fitness test on given data.",
        default=None)
    parser.add_argument('-v', '--visualize-fraction',
        help="Visualize fraction of canceled trains.",
        action='store_true')
    
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
        'canceled': "Zugausfall (0-nicht ausgefallen, 1-Ausfall m Startbahnhof, 2-Ausfall an Zielbahnhof)",
        'delayed': "Verspätet (ab Verspätung von 5min oder Ausfall)"
    }
    return mapper[label_id]


def split(data_path, output_dir, training_fraction):
    """Splits data into training and test data, respecting the given fraction for training data."""

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    data = pd.read_csv(data_path)

    print("Splitting data...")
    training_data = data.sample(frac=training_fraction)
    test_data = pd.concat([data, training_data]).drop_duplicates(keep=False)

    timestamp = datetime.strftime(datetime.now(), '%Y%m%d-%H%M%S')
    
    print("Writing data...")
    training_data.to_csv(os.path.join(output_dir, '{}_data_training.csv'.format(timestamp)), index=False)
    test_data.to_csv(os.path.join(output_dir, '{}_data_test.csv'.format(timestamp)), index=False)

    print("Splitting finished.")


def visualize(data_path):
    """Visualize given data."""
    
    print("Loading data...")
    raw_data = pd.read_csv(data_path)
    
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

    data = raw_data[~raw_data.isnull().any(axis=1)]
    data.loc[data['canceled'] > 0, 'canceled'] = 1

    # Plot outputs
    for index, base_column in enumerate(base_columns):
        plt.figure(index)

        for prefix in ["start", "end"]:
            column = "{}_{}".format(prefix, base_column)

            count = data.loc[data['canceled'] == (1 if prefix=="start" else 2)].groupby(column).size()
            count_total = data.groupby(column).size()

            for index in count_total.index:
                try:
                    number = count[index]
                except KeyError:
                    number = 0
                count_total[index] = number / count_total[index]

            plt.plot(count_total, color="blue" if prefix=="start" else "red", alpha=0.5)

        plt.xlabel(get_label(base_column))
        plt.ylabel("Anteil ausgefallener Züge")

        plt.xticks(())
        plt.yticks(())

    plt.show()


def visualize(data_path):
    """Visualize given data."""
    
    print("Loading data...")
    raw_data = pd.read_csv(data_path)
    
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

    data = raw_data[~raw_data.isnull().any(axis=1)]
    data.loc[data['canceled'] > 0, 'canceled'] = 1

    # Plot outputs
    for index, base_column in enumerate(base_columns):
        plt.figure(index)

        for prefix in ["start"]:
            column = "{}_{}".format(prefix, base_column)

            stepsize = 1
            bins = np.arange(data[column].min(), data[column].max() + stepsize, stepsize)
            groups = pd.cut(data[column], bins=bins, labels=bins[:-1])
            count = data.loc[data['canceled'] == (1 if prefix=="start" else 2)].groupby(groups).size()
            count_total = data.groupby(groups).size()

            for index in count_total.index:
                try:
                    number = count[index]
                except KeyError:
                    number = 0
                count_total[index] = number / count_total[index]

            plt.bar(count_total.index, count_total.values, width=stepsize*0.8, color="blue" if prefix=="start" else "red", alpha=0.5)

        plt.xlabel(get_label(base_column))
        plt.ylabel("Anteil ausgefallener Züge")

        plt.xticks(())
        plt.yticks(())

    plt.show()


def test(training_data_path, test_data_path):
    """Perform linear regression on data and test fitness."""

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
    output_column = 'delay'

    print("Portioning data...")
    training_data_without_nan = training_data[~training_data.isnull().any(axis=1)]
    training_data_without_nan = training_data_without_nan[training_data_without_nan['canceled'] == 0]
    training_data_input = training_data_without_nan[input_columns]
    training_data_output = training_data_without_nan[output_column]

    # Turn dense data frame into sparse data frame. See https://stackoverflow.com/a/70601233/8325653
    sparse_training_data = training_data_input.astype(pd.SparseDtype("float64",0)).sparse.to_coo().tocsr()
    
    print("Training model...")
    model.fit(sparse_training_data, training_data_output.values)

    test_data_without_nan = test_data[~test_data.isnull().any(axis=1)]
    test_data_without_nan = test_data_without_nan[test_data_without_nan['canceled'] == 0]
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

        size = 2
        plt.scatter(test_data_input[start_column], test_data_output, color="black", alpha=0.5, s=size)
        plt.scatter(test_data_input[end_column], test_data_output, color="green", alpha=0.5, s=size)
        plt.scatter(test_data_input[start_column], prediction, color="blue", alpha=0.5, s=size)
        plt.scatter(test_data_input[end_column], prediction, color="red", alpha=0.5, s=size)

        # show mean per sensor value
        # mean_df = test_data_without_nan.groupby(start_column).mean()
        # median_data = mean_df[output_column]
        # plt.plot(median_data, color="yellow", linewidth=1)

        plt.xlabel(get_label(column))
        plt.ylabel(get_label(output_column))

        plt.xticks(())
        plt.yticks(())

    plt.show()


def test_log(training_data_path, test_data_path):
    """Perform logistic regression on data and test fitness."""

    def convertToDelayed(dataframe):
        """Returns a dataframe with column `delayed` with binary value (0, 1) with 1 meaning a delay of >=15 min or cancellation of train."""
        df = dataframe.copy()
        df['delayed'] = 0
        df.loc[(df['delay'] >= 15) | (df['canceled'] > 0), 'delayed'] = 1
        return df

    def getEqualSample(dataframe, column, binSize):
        """Returns dataframe with equal number of data points per bin."""
        bins = np.arange(dataframe[column].min(), dataframe[column].max() + binSize, binSize)
        groups = pd.cut(dataframe[column], bins=bins, labels=bins[:-1])
        grouped_data = dataframe.groupby(groups)
        # print number of elements per group
        print(grouped_data.size())
        min_group_size = grouped_data.size().min()
        print(min_group_size)
        group_samples = grouped_data.sample(n=min_group_size*5, replace=True)
        return group_samples, groups, bins

    model = linear_model.LogisticRegression(C=1.2, penalty='l1', solver='saga')
    
    print("Loading data...")
    training_data = pd.read_csv(training_data_path)
    test_data = pd.read_csv(test_data_path)
    
    base_columns = [
        # 'date','departure_at','arrival_at','train',# 'delay','canceled',
        'tt_tu',# 'rf_tu','r1','p_std','f','fx_911'
    ]
    input_columns = [
        # 'date','departure_at','arrival_at','train','delay','canceled',
        'start_tt_tu',
        'end_tt_tu',
        'start_rf_tu',
        'end_rf_tu',
        # 'start_r1',
        # 'end_r1',
        # 'start_p_std',
        # 'end_p_std',
        'start_f',
        'end_f',
        'start_fx_911',
        'end_fx_911'
    ]
    output_column = 'delayed'

    print("Portioning data...")
    training_data_without_nan, groups, bins = getEqualSample(convertToDelayed(training_data[~training_data.isnull().any(axis=1)]), input_columns[0], 5)
    training_data_input = training_data_without_nan[input_columns]
    training_data_output = training_data_without_nan[output_column]

    # Turn dense data frame into sparse data frame. See https://stackoverflow.com/a/70601233/8325653
    sparse_training_data = training_data_input.astype(pd.SparseDtype("float64",0)).sparse.to_coo().tocsr()
    
    print("Training model...")
    model.fit(training_data_input, training_data_output.values)

    test_data_without_nan, _, _ = getEqualSample(convertToDelayed(test_data[~test_data.isnull().any(axis=1)]), input_columns[0], 5)
    test_data_input = test_data_without_nan[input_columns]
    test_data_output = test_data_without_nan[output_column]

    # Turn dense data frame into sparse data frame. See https://stackoverflow.com/a/70601233/8325653
    sparse_test_data = test_data_input.astype(pd.SparseDtype("float64",0)).sparse.to_coo().tocsr()

    print("Testing model...")
    prediction = model.predict_proba(test_data_input)

    # The coefficients
    print("Coefficients: \n", list(zip(input_columns, model.coef_[0])))
    # The mean squared error
    print("Score: %.2f" % model.score(test_data_input, test_data_output))

    # Plot outputs
    for index, base_column in enumerate(base_columns):
        plt.figure(index)

        column = "end_{}".format(base_column)

        # group input data to bars
        stepsize = 3
        # bins = np.arange(test_data_input[column].min(), test_data_input[column].max() + stepsize, stepsize)
        # groups = pd.cut(test_data_input[column], bins=bins, labels=bins[:-1])
        eval_data = training_data_without_nan
        count = eval_data.loc[eval_data[output_column] == 1].groupby(groups).size()
        count_total = eval_data.groupby(groups).size()
        share = count.div(count_total)
        total = count_total.div(count_total.max())

        size = 2
        # plt.scatter(test_data_input[start_column], test_data_output, color="green", alpha=0.5, s=size)
        plt.bar(bins[:-1], share, color="blue", alpha=0.5, width=stepsize*0.8)
        plt.bar(bins[:-1], total, color="green", alpha=0.5, width=stepsize*0.4)
        plt.scatter(test_data_input[column], prediction[:,1], color="red", alpha=0.5, s=size)

        # show mean per sensor value
        # mean_df = test_data_without_nan.groupby(start_column).mean()
        # median_data = mean_df[output_column]
        # plt.plot(median_data, color="yellow", linewidth=1)

        # draw trend
        # coefficients = np.polyfit(test_data_input[start_column], test_data_output, 2)
        # trend = np.poly1d(coefficients)
        # plt.plot(test_data_input[start_column], trend(test_data_input[start_column]), color="yellow", linewidth=1)

        plt.xlabel(get_label(base_column))
        plt.ylabel(get_label(output_column))

        plt.xticks(())
        plt.yticks(())

    plt.show()


def main():
    args = parse_arguments()

    if not args.split_fraction == -1:
        split(args.data_path, args.output_dir, args.split_fraction)

    elif args.visualize_fraction:
        visualize(args.data_path)

    elif args.test_logistic_data_path:
        test_log(args.data_path, args.test_logistic_data_path)

    elif args.test_data_path is not None:
        test(args.data_path, args.test_data_path)

if __name__ == '__main__':
    main()
