#author: @mvbOnline

from typing import Text
from backend import Backend
from flask import Flask, url_for, request, render_template, redirect, session, g, send_file, flash, make_response
import flask_login
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
import os
import sys
import logging
import pathlib
from datetime import date, datetime
import evaluation

# set some general settings and define pathes
UPLOADFOLDER = str(pathlib.Path(__file__).parent.resolve()) + '/uploads/'  # uploadfolder
DOWNLOADFILE = str(pathlib.Path(__file__).parent.resolve()) + '/dataset.csv'
TESTSET_FEATURES_FILE = str(pathlib.Path(__file__).parent.resolve()) + '/testset/test_features.csv'


# get a backend object
backend = Backend()


# start the app and flask
app = Flask(__name__) # init the application
app.secret_key = os.urandom(16)  # define the secret key for a session

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///user_db.db' # the database where we store the users in 


# setup the logging
logging.basicConfig(filename='error.log')
logging.getLogger('werkzeug').setLevel(logging.INFO)


db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = 'Welcome to the DSA Server. Submit your models or check out your ranking. Good luck!'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# create a User object - this method is extending flask UserMixin and the database Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # must be called 'id' => otherwise the method from 'UserMixin' will not work (User extends UserMixin)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    alias = db.Column(db.String(20), nullable=False)



# check before request if user has id => if not set g.user to None to avoid unauthorized behavior
@app.before_request
def before_request():
    if 'user_id' in session:
        user = [x for x in users if x.id == session['user_id']][0]
        g.user = user  # g is kind of global variable for a single flask session
    else:
        g.user = None  # set the flask global variable to None


# Page 1
@app.route('/', methods=['GET', 'POST'])
def login():
    app.logger.info('{} accessed the login page.'.format(request.environ.get('HTTP_X_REAL_IP', request.remote_addr)))
    if request.method == 'POST':
        session.pop('user_id', None)   # remove the user-id if there is one already in the session
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):  # werkzeug.security
                login_user(user)
                app.logger.info('{} {} logged in successfull'.format(request.environ.get('HTTP_X_REAL_IP', request.remote_addr), flask_login.current_user.alias))
                return redirect(url_for('upload'))
            else:
                app.logger.warning('{} had a wrong login'.format(request.environ.get('HTTP_X_REAL_IP', request.remote_addr)))
        else:
            app.logger.warning('{} had a wrong login'.format(request.environ.get('HTTP_X_REAL_IP', request.remote_addr)))
            return redirect(url_for('login'))  # redirect the user to the login page if the login was not correct

    return render_template('login.html')  # if it is not a POST we render the login.html

# Page 2
@app.route("/upload", methods = ['GET', 'POST'])
@login_required
def upload():

    accuracy = 'None' # init the accuracy

    if request.method == 'POST':  # wenn post dann hochladen
        if 'uploadfile' not in request.files:
            return redirect(request.url)
        file = request.files['uploadfile']  # file auslesen
        if file.filename == '':
            return redirect(request.url)

        if backend.allowed_extensions(file.filename):
            filename = secure_filename(file.filename)  # ganz wichtig! checkt den filename auf Sicherheit!

            # filename um usernamen und timestamp erweitern
            filename_without_extension = filename.rsplit('.')[0]; extension = filename.rsplit('.')[-1]
            time = datetime.now()
            time = time.strftime("%d_%m_%Y_%H_%M")
            new_filename = filename_without_extension + '_{}_{}.{}'.format(flask_login.current_user.alias, time, extension)

            file.save(os.path.join(UPLOADFOLDER, new_filename))
            app.logger.info('User {} uploaded a model. It got soaved under {}'.format(flask_login.current_user.alias, new_filename))
#            app.logger.info('{} {} uploaded a model successfully'.format(request.environ.get('HTTP_X_REAL_IP', request.remote_addr), 
#            flask_login.current_user.alias))

            accuracy = evaluation.evaluate(os.path.join(UPLOADFOLDER, new_filename))
            if accuracy == 'ID_not_found':
                flash('In your upload file no columns "id" was found. Make sure you wrote it correctly')
                return redirect(request.url)
            if accuracy == 'Label_class_not_found':
                flash('In your upload file no columns "class" was found. Make sure you wrote it correctly')
                return redirect(request.url)
            if accuracy == 'Dtype_error':
                flash('Your predictions are not strings. Maybe you submit one-hot-encoded class predictions?')
                return redirect(request.url)

            backend.write_results(flask_login.current_user.username, flask_login.current_user.alias, accuracy)
            accuracy = str(accuracy)

            #return redirect(url_for('ranking'))  # without setting a cookie
            app.logger.info('For user {} a cookie got set after the model got evaluated successfully. The cookie has value {}'.format(flask_login.current_user.alias, accuracy))
            resp = make_response(redirect(url_for('ranking')))  # create and return a response to set a cookie - mjammi
            resp.set_cookie('Accuracy', accuracy)
            return resp 

        else:
            flash('This file format is not accepted!')
            app.logger.warning('{} {} tried to upload files that are not allowed'.format(request.environ.get('HTTP_X_REAL_IP', request.remote_addr), 
            flask_login.current_user.alias))

    resp = make_response(render_template('upload.html'))  # create and return a response to set a cookie - mjammi
    resp.set_cookie('Accuracy', accuracy)
    return resp 

#    return render_template('upload.html')

# Page 2.1 download the dataset
@app.route('/download_dataset', methods = ['GET', 'POST'])
@login_required
def download_dataset():
    path = DOWNLOADFILE
    #print('This is the download path: {}'.format(path), file=sys.stdout)
    app.logger.info('{} {} accessed the download file'.format(request.environ.get('HTTP_X_REAL_IP', request.remote_addr), flask_login.current_user.alias))
    return send_file(path, as_attachment=True)

@app.route('/download_testset_features', methods=['GET', 'POST'])
@login_required
def download_testset_features():
    path = TESTSET_FEATURES_FILE
    #print('This is the download path: {}'.format(path), file=sys.stdout)
    app.logger.info('{} {} accessed the download file'.format(request.environ.get('HTTP_X_REAL_IP', request.remote_addr), flask_login.current_user.alias))
    return send_file(path, as_attachment=True)

# Page 3 (after model upload)
@app.route('/ranking', methods=['GET'])
@login_required
def ranking():
    headings, data = backend.read_ranking()
    current_user_result = request.cookies.get('Accuracy')
    app.logger.info('User {} reached the ranking site and the accuracy cookie has a value of {}'.format(flask_login.current_user.alias, current_user_result))
    if current_user_result == 'None':
        current_user_result = ' '
    else:
        current_user_result = '{}%'.format(current_user_result)
    best_user_result = backend.get_best_user_result(flask_login.current_user.username)
    attempts_left = backend.get_left_attempts(flask_login.current_user.username)

    return render_template('ranking.html', best_user_result=str(best_user_result),attempts_left=str(attempts_left),current_user_result=current_user_result, headers=headings, data=data)


# page 4 -> logout
@app.route('/logout')
@login_required
def logout():
    app.logger.info('{} {} logged out successfully'.format(request.environ.get('HTTP_X_REAL_IP', request.remote_addr), flask_login.current_user.alias))
    logout_user()
    return redirect(url_for('login'))


# page 5 -> manual site with explanations about the project
@app.route('/howitworks')
@login_required
def howitworks():
    app.logger.info('{} {} entered the how-it-works page'.format(request.environ.get('HTTP_X_REAL_IP', request.remote_addr), flask_login.current_user.alias))
    return render_template('howItworks.html')

# get => vom backend was ziehen
# post => daten ans backend schicken, logins, user gibt daten an

# run the programm
if __name__ == '__main__':

    logging.basicConfig(filename='error.log')
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))  # debug mode
