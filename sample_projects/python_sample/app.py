# Demo application
import os
from flask import Flask
app = Flask(__name__)

# Safe mock credential (masked in StackDoctor)
MOCK_KEY = 'sk-proj-demo1234567890abcdef1234567890'

@app.route('/')
def home():
    return {'status': 'healthy'}
