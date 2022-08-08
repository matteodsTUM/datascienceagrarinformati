# author: @mvbOnline
from glob import glob
import pathlib
import re
import numpy as np
import pandas as pd
import warnings

class Backend:


    def __init__(self):
        self.extensions = set(['csv'])  # pickle file in which the sklearn model should be stored

        self.static_folder = str(pathlib.Path(__file__).parent.resolve()) + '/DSA_Server/static/' # activate when server runs
#        warnings.warn('Change the static folder to the server style before pushing')
#        self.static_folder = str(pathlib.Path(__file__).parent.resolve()) + '/static/'


    def allowed_extensions(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.extensions  # check filename

    def get_best_user_result(self, username):
        result_table = pd.read_csv(self.static_folder + 'result_log.csv', index_col='Username')
        try:
            best_result_string = '{}%'.format(round(float(result_table['Accuracy'].loc[username].max()),2))
        except KeyError:
            return 'None'
        return best_result_string

    def get_left_attempts(self, username):
        attempts_table = pd.read_csv(self.static_folder + 'attempt_counter.csv', index_col='Username')
        return int(attempts_table['Attempts_left'].loc[username])


    def write_results(self, username, alias, result):
        
        result_log = pd.read_csv(self.static_folder + 'result_log.csv')
        
        # check if the username exists and write it if not
        if not username in result_log['Username'].tolist():
            new_user = {'Username' : username, 'Alias' : alias, 'Accuracy' : 0, 'Attempt_no' : 0}
            result_log = pd.concat([result_log, pd.DataFrame(new_user, index=[0])])

        # get latest attempt
        result_log_copy = result_log.copy()
        result_log_copy.set_index('Username', inplace=True)
        past_attempts_no = result_log_copy['Attempt_no'].loc[username].max()

        # append result to the existing result logfile
        attempt = int(past_attempts_no) +1
        new_result = pd.DataFrame({'Username':username, 'Alias':alias, 'Accuracy':result, 'Attempt_no': attempt}, index=[0])
        result_log = result_log.append(new_result)
        result_log.to_csv(self.static_folder + 'result_log.csv', index=False)

        # create new ranking table
        # sort the result_log by result and slice the top10 from it and write it as 'ranking.csv'
        result_log.sort_values('Accuracy', inplace=True, ascending=False)
        top10 = result_log[:10].reset_index(drop=True)
        top10.index.name = 'Rank'
        top10 = top10[['Alias', 'Accuracy']]  # slice the dataframe
        top10.to_csv(self.static_folder + '/ranking.csv')



        # update attempts counter
        attempt = pd.read_csv(self.static_folder + '/attempt_counter.csv')
        # check if the username exists and write it if not
        if not username in attempt['Username'].tolist():
            new_user = {'Username' : username, 'Attempts_done' : 0, 'Default_no_attempts' : 999, 'Attempts_left' : 999}
            attempt = pd.concat([attempt, pd.DataFrame(new_user, index=[0])])

        attempt.set_index('Username', inplace=True)
        attempt['Attempts_done'].loc[username] += 1
        attempt['Attempts_left'].loc[username] = attempt['Default_no_attempts'].loc[username] - attempt['Attempts_done'].loc[username]
        attempt.to_csv(self.static_folder + '/attempt_counter.csv', index=True)
        return None


    def read_ranking(self):
        headers = ['Rank', 'Alias', 'Accuracy']
        results = pd.read_csv(self.static_folder + '/result_log.csv')
        results.sort_values('Accuracy', inplace=True, ascending=False)
        top10 = results[:10]
        top10['Rank'] = np.arange(1,11)
        top10 = top10[headers]  # slice the dataframe

        # create a tuple of tuples wheres each tuple is a datarow with (Rank, Alias, Accuracy)
        tuples = tuple(tuple(datarow) for datarow in top10.to_numpy())
        return headers, tuples
