from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({
        "status": {
            "code": 200,
            "message": "API is working properly",
        },
        "data": {
            'Project_Name': 'UV Index Prediction',
            'Team': 'Cangcimen',
            'Created_By': 'Cangcimen Team',
        }
    }), 200

@app.route("/prediction", methods=["GET", "POST"])
def prediction():
    if request.method == "GET":
        return jsonify({
            "status": {
                "code": 200,
                "message": "Test Successful. Use POST method to make predictions."
            },
            "data": {
                "description": "To test prediction, send POST request with 'features' data."
            }
        }), 200

    elif request.method == "POST":
        try:
            data = request.get_json()
            
            if not data or 'features' not in data:
                return jsonify({
                    "status": {
                        "code": 400,
                        "message": "'features' not found in request"
                    },
                    "data": None
                }), 400

            # Return dummy prediction for testing
            return jsonify({
                "status": {
                    "code": 200,
                    "message": "Success Predicting (Test Mode)",
                },
                "data": {
                    "uv_index": 2,
                    "uv_category": "Low"
                }
            }), 200

        except Exception as e:
            return jsonify({
                "status": {
                    "code": 400,
                    "message": f"Error: {str(e)}",
                },
                "data": None,
            }), 400

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)