from app import app  # Replace with your actual Flask app file name
from vercel_wsgi import app as vercel_app

handler = vercel_app(app)