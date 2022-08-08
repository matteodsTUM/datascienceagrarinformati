import pandas as pd
from sklearn.metrics import top_k_accuracy_score
import numpy as np
from sklearn.utils import axis0_safe_slice
import pathlib
import warnings



def evaluate(path_to_results):

    testset_folder = str(pathlib.Path(__file__).parent.resolve()) + '/DSA_Server/testset/' # activate when server runs!!!
#    warnings.warn('Change the static folder to the server style before pushing')
#    testset_folder = str(pathlib.Path(__file__).parent.resolve()) + '/testset/'


    prediction = pd.read_csv(path_to_results)

    if 'id' not in prediction.columns.values:
        return 'ID_not_found'
    if 'class' not in prediction.columns.values:
        return 'Label_class_not_found'
    if prediction['class'].dtype == np.float or prediction['class'].dtype == np.int:
        return 'Dtype_error'

    # load the prediction
    prediction.set_index('id', inplace=True)

    true_classes = pd.read_csv('{}test_classes.csv'.format(testset_folder), index_col='id')

    correct_results = 0
    total_amount_of_results = len(true_classes)

    for field in true_classes.index:
        true_class = true_classes['class'].loc[field]

        # make sure it does not interrupt if a student did not provide all data
        try:
            predicted_class = prediction['class'].loc[field]
        except KeyError:
            continue

        if str(true_class) == str(predicted_class):
            correct_results += 1

    accuracy = (correct_results / total_amount_of_results) * 100
    accuracy = np.round(accuracy, decimals=2)
    return accuracy







#    prediction.sort_index(axis=1, inplace=True)  # sort alphabetically


    # load the classes
#    true_classes = pd.read_csv('testset/test_classes.csv')

    # change classes to number alphabetically
    # corn = 0
    # rapeseed = 1
    # wheat = 2
    true_classes = true_classes.replace('corn', 0)
    true_classes = true_classes.replace('rapeseed', 1)
    true_classes = true_classes.replace('wheat', 2)


    # get the accuracy
    accuracy = top_k_accuracy_score(true_classes.to_numpy(), prediction, k=1, normalize=True)
    accuracy = np.round(accuracy, decimals=2) * 100 # *100 => ganze Zahlen

    return accuracy