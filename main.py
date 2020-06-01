from flask import Flask, request, jsonify, render_template, abort 

app = Flask(__name__)

# import declared routes
import automata_cfg

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")
    
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404
    
if __name__ == "__main__":
    app.run(debug=True)