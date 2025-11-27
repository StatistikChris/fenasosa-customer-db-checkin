# Fenasosa Customer Check-In Service

A Docker-based Flask application that updates customer check-in status in BigQuery and can be deployed to Google Cloud Run with automated GitHub Actions deployment.

## Features

- ✅ Updates `checkin` field to "si" for customers by email
- ✅ Returns the updated customer row
- ✅ Automated deployment to Google Cloud Run via GitHub Actions
- ✅ Secure BigQuery integration
- ✅ Health check endpoint
- ✅ Error handling and validation

## API Endpoints

### Health Check
```
GET /
```
Returns service health status.

### Update Check-In
```
POST /checkin
Content-Type: application/json

{
  "email": "customer@example.com"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Successfully updated checkin for customer@example.com",
  "updated_row": {
    "email": "customer@example.com",
    "checkin": "si",
    ...
  }
}
```

**Response (Not Found):**
```json
{
  "error": "No customer found with email: customer@example.com"
}
```

## Local Development

### Prerequisites
- Python 3.11+
- Docker
- Google Cloud credentials with BigQuery access

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/StatistikChris/fenasosa-customer-db-checkin.git
   cd fenasosa-customer-db-checkin
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Cloud credentials:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/credentials.json"
   ```

4. **Run locally:**
   ```bash
   python app.py
   ```
   The service will be available at `http://localhost:8080`

### Test locally with Docker

1. **Build the Docker image:**
   ```bash
   docker build -t fenasosa-checkin .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8080:8080 \
     -v /path/to/credentials.json:/app/credentials.json \
     -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
     -e GCP_PROJECT_ID=rapid-gadget-477511-n7 \
     fenasosa-checkin
   ```

3. **Test the endpoint:**
   ```bash
   curl -X POST http://localhost:8080/checkin \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com"}'
   ```

## Cloud Run Deployment

### Prerequisites
1. Google Cloud Project: `rapid-gadget-477511-n7`
2. BigQuery dataset: `fenasosa_dataset`
3. BigQuery table: `clientes`
4. Service Account with BigQuery permissions

### GitHub Secrets Setup

Add the following secret to your GitHub repository:

**`GCP_SA_KEY`**: Service Account JSON key with the following permissions:
- BigQuery Data Editor
- BigQuery Job User
- Cloud Run Admin
- Artifact Registry Writer

To create and download the service account key:
```bash
# Create service account
gcloud iam service-accounts create fenasosa-deployer \
  --display-name="Fenasosa Deployer"

# Grant necessary permissions
gcloud projects add-iam-policy-binding rapid-gadget-477511-n7 \
  --member="serviceAccount:fenasosa-deployer@rapid-gadget-477511-n7.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding rapid-gadget-477511-n7 \
  --member="serviceAccount:fenasosa-deployer@rapid-gadget-477511-n7.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding rapid-gadget-477511-n7 \
  --member="serviceAccount:fenasosa-deployer@rapid-gadget-477511-n7.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding rapid-gadget-477511-n7 \
  --member="serviceAccount:fenasosa-deployer@rapid-gadget-477511-n7.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Create and download key
gcloud iam service-accounts keys create key.json \
  --iam-account=fenasosa-deployer@rapid-gadget-477511-n7.iam.gserviceaccount.com
```

Then add the contents of `key.json` to GitHub:
1. Go to repository Settings → Secrets and variables → Actions
2. Create new secret named `GCP_SA_KEY`
3. Paste the entire content of `key.json`

### Create Artifact Registry Repository

```bash
gcloud artifacts repositories create fenasosa-customer-checkin \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker repository for Fenasosa check-in service"
```

### Automated Deployment

The application automatically deploys to Cloud Run when you push to the `main` or `master` branch.

```bash
git add .
git commit -m "Deploy to Cloud Run"
git push origin master
```

### Manual Deployment

If you prefer manual deployment:

```bash
# Authenticate
gcloud auth login
gcloud config set project rapid-gadget-477511-n7

# Build and deploy
gcloud run deploy fenasosa-customer-checkin \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=rapid-gadget-477511-n7,DATASET_ID=fenasosa_dataset,TABLE_ID=clientes
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GCP_PROJECT_ID` | `rapid-gadget-477511-n7` | Google Cloud Project ID |
| `DATASET_ID` | `fenasosa_dataset` | BigQuery dataset name |
| `TABLE_ID` | `clientes` | BigQuery table name |
| `PORT` | `8080` | Port for the Flask application |

## BigQuery Table Requirements

The `clientes` table must have at least the following columns:
- `email` (STRING): Customer email address (used for lookup)
- `checkin` (STRING): Check-in status (will be set to "si")

## Usage Example

Once deployed, you can use the service:

```bash
# Get your Cloud Run URL
SERVICE_URL=$(gcloud run services describe fenasosa-customer-checkin \
  --region us-central1 --format 'value(status.url)')

# Update a customer's check-in status
curl -X POST $SERVICE_URL/checkin \
  -H "Content-Type: application/json" \
  -d '{"email":"customer@example.com"}'
```

## Security

- Service Account authentication for BigQuery
- SQL injection protection via parameterized queries
- Non-root user in Docker container
- HTTPS-only on Cloud Run

## Troubleshooting

### Deployment fails
- Verify `GCP_SA_KEY` secret is correctly set
- Ensure Service Account has necessary permissions
- Check that Artifact Registry repository exists

### BigQuery errors
- Verify table structure matches requirements
- Check Service Account has BigQuery permissions
- Ensure project ID, dataset, and table names are correct

### No customer found
- Verify email exists in the `clientes` table
- Check email spelling and format

## License

MIT
