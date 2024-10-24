import sys
from io import BytesIO
from flask import Flask
from werkzeug.wrappers import Request, Response
from app import app  # Ensure 'app' is the Flask instance in app.py

def handler(request):
    # Build the WSGI environment dictionary
    environ = {
        'REQUEST_METHOD': request.method,
        'PATH_INFO': request.path,
        'QUERY_STRING': request.query_string.decode('utf-8'),
        'CONTENT_TYPE': request.headers.get('Content-Type', ''),
        'CONTENT_LENGTH': request.headers.get('Content-Length', '0'),
        'wsgi.input': BytesIO(request.body or b''),
        'wsgi.errors': sys.stderr,
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }

    # Add HTTP headers to environ
    for key, value in request.headers.items():
        header_key = f'HTTP_{key.upper().replace("-", "_")}'
        environ[header_key] = value

    # Create a WSGI Request object
    req = Request(environ)

    # Get the WSGI response from Flask
    resp = Response.from_app(app.wsgi_app, environ)

    # Convert Flask response to Vercel response format
    return {
        'statusCode': resp.status_code,
        'headers': dict(resp.headers),
        'body': resp.get_data(as_text=True),
    }
