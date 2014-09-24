from app import app
from flask import render_template, redirect, request, url_for
from werkzeug.utils import secure_filename
import pandas as pd
import os
import pymysql as mdb

con = mdb.connect(user="root", host="localhost", db="mail_merge", charset="utf8")

@app.route('/')
@app.route('/index')
def index():
   return render_template("index.html")

@app.route('/authenticate')
def authenticate():
	import httplib2

	from apiclient.discovery import build
	from oauth2client.client import flow_from_clientsecrets
	from oauth2client.file import Storage
	from oauth2client.tools import run


	# Path to the client_secret.json file downloaded from the Developer Console
	CLIENT_SECRET_FILE = 'app/cs_native.json'

	# Check https://developers.google.com/gmail/api/auth/scopes for all available scopes
	OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.modify'

	# Location of the credentials storage file
	STORAGE = Storage('gmail.storage')

	# Redirect URI
	REDIRECT_URI = '/index'

	# Start the OAuth flow to retrieve credentials
	flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
	flow.redirect_uri = REDIRECT_URI
	http = httplib2.Http()

	# Try to retrieve credentials from storage or run the flow to generate them
	credentials = STORAGE.get()
	if credentials is None or credentials.invalid:
	  credentials = run(flow, STORAGE, http=http)

	# Authorize the httplib2.Http object with our credentials
	http = credentials.authorize(http)

	# Build the Gmail service from discovery
	gmail_service = build('gmail', 'v1', http=http)
	
	return redirect('/choose_file')


@app.route('/choose_file')
def choose_file():
	return render_template("choose_file.html")

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

class MailMergeData(object):
	def __init__(self, tsv_path):
		self.mm_data = pd.read_csv(tsv_path, delimiter = "\t")
		self.headers = self.mm_data.columns.values

# Route that will process the file upload
# code from http://runnable.com/UiPcaBXaxGNYAAAL/how-to-upload-a-file-to-the-server-in-flask-for-python
@app.route('/compose', methods=['POST'])
def upload_file():
    # Get the name of the uploaded file
    file = request.files['file']
    # Check if the file is one of the allowed types/extensions
    if file and allowed_file(file.filename):
        # Make the filename safe, remove unsupported chars
        filename = secure_filename(file.filename)
        # Move the file form the temporal folder to
        # the upload folder we setup
        with con:
        	cur=con.cursor()
        	cur.execute("SELECT primary_key FROM previous_jobs ORDER BY primary_key desc LIMIT 1;")
        	last_pkey = cur.fetchone()[0]
    	new_filename = str(last_pkey+1)+'.tsv'
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
        mmo = MailMergeData(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
        headers = mmo.mm_data.columns.values
    	with con:
    		cur = con.cursor()
    		cur.execute("INSERT INTO previous_jobs (tsv_filename) VALUES (%s)", os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
        session = last_pkey
        return render_template('compose.html', headers = headers, session= session)

@app.route('/test', methods=['POST'])
def test():
	print request.form['fromEmail']
	print request.form['toEmail']
	print request.form['subjectEmail']
	print request.form['textEmail']
	print request.form['htmlEmail']
	print request.form['session_num']
	try:
		print request.form['attachmentEmail']
		with con:
			cur = con.cursor()
			cur.execute('''UPDATE previous_jobs
				SET from_email =%s, 
				to_email =%s, 
				subject=%s, 
				attachment_filename =%s,
				text_body = %s,
				html_body = %s
				WHERE primary_key = %s''', 
				[
				request.form['fromEmail'], 
				request.form['toEmail'],
				request.form['subjectEmail'],
				request.form['attachmentEmail'],
				request.form['textEmail'],
				request.form['htmlEmail'],
				request.form['session_num']
				])
	except:
		with con:
			cur = con.cursor()
			cur.execute('''UPDATE previous_jobs
				SET from_email =%s, 
				to_email =%s, 
				subject=%s, 
				text_body = %s,
				html_body = %s
				WHERE primary_key = %s''', 
				[
				request.form['fromEmail'], 
				request.form['toEmail'],
				request.form['subjectEmail'],
				request.form['textEmail'],
				request.form['htmlEmail'],
				request.form['session_num']
				])
	with con:
		cur = con.cursor()
		cur.execute('''SELECT primary_key, tsv_filename 
			FROM previous_jobs 
			ORDER BY primary_key desc 
			LIMIT 1;
			''')
		tsv_filename = cur.fetchone()[1]
	mmo = MailMergeData(tsv_filename)
	to_list = list(mmo.mm_data[request.form['toEmail']])
	return render_template('test.html', to_list=to_list)

@app.route('/send_test_email', methods=['POST'])
def send_test_email():
	return 'done'
