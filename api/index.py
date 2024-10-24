from serverless_wsgi import handle_request
from app import app  # Ensure 'app' is correctly imported from your Flask application

def handler(event, context):
    return handle_request(app, event, context)
