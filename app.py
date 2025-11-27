from flask import Flask, request, jsonify
from google.cloud import bigquery
import os

app = Flask(__name__)

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

@app.route('/checkin', methods=['POST'])
def update_checkin():
    """
    Update the checkin field for a customer with the given email address
    Expected JSON body: {"email": "customer@example.com"}
    """
    try:
        # Get email from request
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
        
        # Update the checkin field to "si" for the given email
        update_query = f"""
            UPDATE `{table_ref}`
            SET checkin = 'si'
            WHERE email = @email
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", email)
            ]
        )
        
        # Execute the update query
        update_job = client.query(update_query, job_config=job_config)
        update_job.result()  # Wait for the query to complete
        
        # Check if any rows were updated
        if update_job.num_dml_affected_rows == 0:
            return jsonify({
                "error": f"No customer found with email: {email}"
            }), 404
        
        # Fetch the updated row
        select_query = f"""
            SELECT *
            FROM `{table_ref}`
            WHERE email = @email
        """
        
        select_job = client.query(select_query, job_config=job_config)
        results = select_job.result()
        
        # Convert results to dictionary
        updated_row = None
        for row in results:
            updated_row = dict(row.items())
            break
        
        if updated_row:
            return jsonify({
                "success": True,
                "message": f"Successfully updated checkin for {email}",
                "updated_row": updated_row
            }), 200
        else:
            return jsonify({
                "error": "Failed to retrieve updated row"
            }), 500
            
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
