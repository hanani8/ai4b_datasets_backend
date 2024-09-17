from flask import Flask, jsonify, request, send_file, make_response
from flask_cors import CORS
import pandas as pd
import yaml
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Load dataset configurations
with open('datasets.yaml', 'r') as file:
    datasets_config = yaml.safe_load(file)

# Global dictionary to hold DataFrames
dataset_dfs = {}

# Load all datasets into global DataFrames at startup
for dataset, config in datasets_config.items():
    if config.get('path_to_csv') is not None:
        dataset_dfs[dataset] = pd.read_csv(config['path_to_csv'])


@app.route('/api/datasets')
def get_datasets():
    """Return the list of datasets."""
    return jsonify(list(datasets_config.values()))


@app.route('/api/data/<dataset>')
def get_dataset_data(dataset):
    """Return filtered dataset data."""
    if dataset not in datasets_config:
        return jsonify({"error": "Dataset not found"}), 404

    config = datasets_config[dataset]
    df = dataset_dfs.get(dataset)

    if df is None:
        return jsonify({"error": "Dataset not found"}), 400

    # Apply filters
    for filter in config['filters']:
        filter_values = request.args.getlist(filter)
        if filter_values:
            df = df[df[filter].isin(filter_values)]

    # Sample 10 random rows
    data = df.sample(n=min(10, len(df))).to_dict('records')

    return jsonify({
        "data": data,
        "total": len(df),
    })


@app.route('/api/filters/<dataset>')
def get_dataset_filters(dataset):
    """Return available filters for the dataset."""
    if dataset not in datasets_config:
        return jsonify({"error": "Dataset not found"}), 404

    config = datasets_config[dataset]
    df = dataset_dfs.get(dataset)

    if df is None:
        return jsonify({"error": "Dataset not found"}), 400

    filters = {filter: df[filter].unique().tolist() for filter in config['filters']}
    print(filters)
    return jsonify(filters)


@app.route('/api/serve_file/<dataset>')
def serve_file(dataset):
    """Serve audio file with caching headers."""
    if dataset not in datasets_config:
        return jsonify({"error": "Dataset not found"}), 404

    filename = request.args.get('filename')
    config = datasets_config[dataset]
    audio_directory = config['audio_directory']
    path = os.path.join(audio_directory, filename)

    print(path)

    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 500

    response = make_response(send_file(path, as_attachment=True))
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response


if __name__ == '__main__':
    # Run the app using a production server, e.g., Gunicorn:
    # gunicorn -w 4 -b 0.0.0.0:8000 app:app
    app.run(host='0.0.0.0', debug=False)  # Debug is turned off for production
    # pass

