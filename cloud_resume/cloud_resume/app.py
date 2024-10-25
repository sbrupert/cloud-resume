from flask import Flask, render_template, request
from cloud_resume.logger import *
from cloud_resume.db import increment_counter

app = Flask(__name__)

# Configure flask to use our logger
logger = configure_logging("webserver")
app.logger = logger

app.wsgi_app = RequestLoggerMiddleware(app, app.wsgi_app)

@app.route('/')
def index():
    counter = increment_counter()
    return render_template('index.html', counter=counter)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)