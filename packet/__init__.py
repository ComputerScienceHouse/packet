from flask import Flask

app = Flask(__name__)
app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))


@app.route('/')
def hello_world():
        return 'Hello, World!'
