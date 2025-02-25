import os
from flask import Flask
from institution_list import institution_bp
from research import research_bp
from seasonality import seasonality_bp
from etf_research import etf_research_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(institution_bp)
app.register_blueprint(research_bp)
app.register_blueprint(seasonality_bp)
app.register_blueprint(etf_research_bp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
