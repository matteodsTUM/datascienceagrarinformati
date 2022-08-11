FROM python:3.9-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
#RUN pip install --no-cache-dir -r requirements.txt

RUN pip3 install numpy
RUN pip3 install Flask
RUN pip3 install gunicorn
RUN pip3 install Flask_Login
RUN pip3 install Flask_SQLAlchemy
RUN pip3 install pandas
RUN pip3 install pylint
RUN pip3 install typing
RUN pip3 install scikit-learn
RUN pip3 install xgboost

#RUN pip install gunicorn

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 __init__:app
