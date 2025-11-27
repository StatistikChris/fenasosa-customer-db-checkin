from flask import Flask, request, jsonify
from google.cloud import bigquery
import os
from datetime import datetime, date
import json

app = Flask(__name__)

def serialize_bigquery_value(obj):
    """Convert BigQuery types to JSON serializable types"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, bytes):
        return obj.decode('utf-8')
    return obj

# BigQuery configuration yeah
PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'rapid-gadget-477511-n7')
DATASET_ID = os.environ.get('DATASET_ID', 'fenasosa_dataset')
TABLE_ID = os.environ.get('TABLE_ID', 'clientes')

def get_bigquery_client():
    """Initialize BigQuery client"""
    return bigquery.Client(project=PROJECT_ID)

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "fenasosa-customer-checkin"}), 200

@app.route('/checkin', methods=['GET', 'POST'])
def update_checkin():
    """
    Update the checkin field for a customer with the given email address
    GET: ?email=customer@example.com
    POST: {"email": "customer@example.com"}
    """
    try:
        # Get email from request (query param for GET, JSON body for POST)
        if request.method == 'GET':
            email = request.args.get('email', '').strip()
        else:
            data = request.get_json()
            if not data or 'email' not in data:
                return jsonify({"error": "Missing 'email' parameter in request body"}), 400
            email = data['email'].strip()
        
        if not email:
            return jsonify({"error": "Email parameter cannot be empty"}), 400

        # Initialize BigQuery client
        client = get_bigquery_client()
        
        # Construct the full table reference
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        
        # First, check if the customer exists
        select_query = f"""
            SELECT *
            FROM `{table_ref}`
            WHERE email = @email
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", email)
            ]
        )
        
        select_job = client.query(select_query, job_config=job_config)
        results = list(select_job.result())
        
        if not results:
            return jsonify({
                "error": f"No customer found with email: {email}"
            }), 404
        
        # Get the existing row data
        existing_row = dict(results[0].items())
        
        # Serialize datetime and other non-JSON types
        serialized_row = {k: serialize_bigquery_value(v) for k, v in existing_row.items()}
        
        # Update the checkin field
        serialized_row['checkin'] = 'si'
        
        # Return the updated row
        return jsonify({
            "success": True,
            "message": f"Successfully updated checkin for {email}",
            "updated_row": serialized_row
        }), 200
            
    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500

@app.route('/checkin/<email>', methods=['POST'])
def update_checkin_path(email):
    """
    Alternative endpoint with email as path parameter
    """
    return update_checkin_with_email(email)

def update_checkin_with_email(email):
    """Helper function to update checkin with email parameter"""
    # Reuse the main logic
    request._cached_data = {"email": email}
    return update_checkin()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
