import sys
import random
import json
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html", fanCounter="00h 27m", lights="Off")

if __name__ == "__main__":
    app.run()
