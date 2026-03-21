from flask import Flask, render_template
from flask_flatpages import FlatPages
from cloud_resume.logger import *
from cloud_resume.db import increment_counter
from cloud_resume.markdown import (
    MARKDOWN_EXTENSIONS,
    MARKDOWN_EXTENSION_CONFIGS,
    render_markdown_safely
)

app = Flask(__name__)

app.config["FLATPAGES_ROOT"] = "pages"
app.config["FLATPAGES_EXTENSION"] = ".md"
app.config["FLATPAGES_MARKDOWN_EXTENSIONS"] = MARKDOWN_EXTENSIONS
app.config["FLATPAGES_EXTENSION_CONFIGS"] = MARKDOWN_EXTENSION_CONFIGS
app.config["FLATPAGES_HTML_RENDERER"] = render_markdown_safely

pages = FlatPages(app)

# Configure flask to use our logger
logger = configure_logging("webserver")
app.logger = logger

app.wsgi_app = RequestLoggerMiddleware(app, app.wsgi_app)

@app.route('/')
def index():
    counter = increment_counter()
    return render_template('index.html', counter=counter)


@app.route('/page/<path:slug>')
def markdown_page(slug):
    page = pages.get_or_404(slug)
    return render_template("markdown_page.html", page=page)


@app.route('/healthz')
def healthz():
    return {"status": "ok"}, 200
