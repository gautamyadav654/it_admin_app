"""
Vercel Serverless Function Entry Point
This file serves as the entry point for Vercel deployment.
"""
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

# Create the Flask app
app = create_app()

# Vercel requires the app to be named 'app' or 'handler'
# For Python, we export the Flask app directly

# This is needed for Vercel's Python runtime
if __name__ == "__main__":
    app.run(debug=True)