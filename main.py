from flask import Flask
import requests
from datetime import datetime, timedelta
from google.cloud import storage
import json
import pytz
import os


app = Flask(__name__)

def fetch_jira_issues():
    JIRA_DOMAIN = 'nirmalmanoharan.atlassian.net'
    JIRA_EMAIL = 'abeyk@stgit.com'
    JIRA_API_TOKEN = 'ATATT3xFfGF0qEd4BK-BxqRaRXO2VUbMQHCJdOMRNXaf0Te6yriTs-xgVTfwWgv9IYnm0EkXOqlasASV-ZDRsByK1NI1Eer85Z8VA0PamNSuuaAY5pF6kp8IXlLjjhUsWSNtvDJcYMqPjj_xAj26miFuQdpZcuQr_XWQFRHF9S4cIAO5RrgON6g=99AE30EC'
    JIRA_PROJECT_KEY = 'ISSUE'
    BUCKET_NAME = 'inbound_dev'
    FILE_NAME = f'jira_issues_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.json'
    
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {"Accept": "application/json"}
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    last_5_minutes = utc_now - timedelta(minutes=5)
    jql_query = f'project="{JIRA_PROJECT_KEY}" AND updatedDate>"-5m"'
    all_issues = []
    start_at = 0
    max_results = 50
    total = None
    
    while total is None or start_at < total:
        url = f'https://nirmalmanoharan.atlassian.net/rest/api/3/search?jql={jql_query}&startAt={start_at}&maxResults={max_results}'
        response = requests.get(url, auth=auth, headers=headers)
        
        if response.status_code == 200:
            response_json = response.json()
            issues = response_json.get('issues', [])
            all_issues.extend(issues)
            total = response_json.get('total', 0)
            start_at += len(issues)
        else:
            raise Exception(f"Failed to fetch issues from Jira: {response.text}")

    issues_json = json.dumps({"issues": all_issues}, indent=2)

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(FILE_NAME)
    blob.upload_from_string(issues_json, content_type='application/json')

    return f"Successfully uploaded {FILE_NAME} to {BUCKET_NAME}."

@app.route('/', methods=['GET'])
def run_fetch_jira_issues():
    try:
        result = fetch_jira_issues()
        return result
    except Exception as e:
        return str(e)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))  # Correctly use the PORT environment variable
    app.run(debug=False, host='0.0.0.0', port=port)

