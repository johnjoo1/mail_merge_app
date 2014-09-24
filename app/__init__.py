from flask import Flask

app = Flask(__name__)
app.config.from_object('config')
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'csv', 'tsv'])

from app import views
