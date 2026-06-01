from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def index():
    # name = request.args.get("name", "")
    a="../../../../../../../../flag"
    return render_template(a)

if __name__ == "__main__":
    app.run(debug=True)
