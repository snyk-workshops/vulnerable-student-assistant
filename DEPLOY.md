# Deploying to Google Cloud

This guide covers deploying the Vulnerable Student Assistant to Google Cloud using **Cloud Run** (recommended) or **App Engine**.

## Prerequisites

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured
2. A Google Cloud project with billing enabled
3. A [Google Gemini API key](https://aistudio.google.com/apikey)

```bash
# Authenticate with Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

---

## Option 1: Cloud Run (Recommended)

Cloud Run is ideal for this stateless application with automatic scaling and pay-per-use pricing.

### Step 1: Create a Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Step 2: Store the API Key in Secret Manager

```bash
# Enable Secret Manager
gcloud services enable secretmanager.googleapis.com

# Create the secret
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=-
```

### Step 3: Create a Service Account

Create a dedicated service account for Cloud Run to use:

```bash
# Create the service account
gcloud iam service-accounts create student-assistant-sa \
  --display-name="Student Assistant Service Account"

# Grant the service account permission to access the secret
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:student-assistant-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

> **Note:** Replace `YOUR_PROJECT_ID` with your actual Google Cloud project ID (not the project number).
> Run `gcloud config get-value project` to find your project ID.

### Step 4: Deploy to Cloud Run

**Option A: Deploy directly from source (simplest)**

```bash
gcloud run deploy student-assistant \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account=student-assistant-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
```

**Option B: Build and deploy separately**

```bash
# Build the container image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/student-assistant

# Deploy to Cloud Run
gcloud run deploy student-assistant \
  --image gcr.io/YOUR_PROJECT_ID/student-assistant \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account=student-assistant-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
```

### Step 5: Access Your Application

After deployment, you'll receive a URL like:
```
https://student-assistant-xxxxx-uc.a.run.app
```

---

## Option 2: App Engine

App Engine provides a fully managed platform with automatic scaling.

### Step 1: Create app.yaml

Create an `app.yaml` in the project root:

```yaml
runtime: python311

entrypoint: uvicorn main:app --host 0.0.0.0 --port $PORT

env_variables:
  GEMINI_API_KEY: "YOUR_GEMINI_API_KEY"

handlers:
  - url: /static
    static_dir: static
  - url: /.*
    script: auto
```

> **Security Note:** For production, use Secret Manager instead of hardcoding the API key. See [Accessing Secret Manager](https://cloud.google.com/appengine/docs/standard/python3/using-secret-manager).

### Step 2: Deploy

```bash
# Initialize App Engine (first time only)
gcloud app create --region=us-central

# Deploy
gcloud app deploy
```

### Step 3: Access Your Application

```bash
gcloud app browse
```

Your app will be available at: `https://YOUR_PROJECT_ID.uc.r.appspot.com`

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Generative AI API key | Yes |

---

## Updating the Deployment

### Cloud Run
```bash
gcloud run deploy student-assistant --source . --region us-central1
```

### App Engine
```bash
gcloud app deploy
```

---

## Updating the Gemini API Key

To rotate or update your Gemini API key in Secret Manager:

### Add a New Secret Version

```bash
# Create a new version of the secret with the updated key
echo -n "YOUR_NEW_GEMINI_API_KEY" | gcloud secrets versions add gemini-api-key --data-file=-
```

### Redeploy to Use the New Secret

Cloud Run needs to be redeployed to pick up the new secret version:

```bash
# Redeploy the service (uses "latest" version of secret by default)
gcloud run deploy student-assistant --source . --region us-central1
```

Or force a new revision without rebuilding:

```bash
gcloud run services update student-assistant \
  --region us-central1 \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
```

### View Secret Versions

```bash
# List all versions of the secret
gcloud secrets versions list gemini-api-key

# View details of a specific version
gcloud secrets versions describe VERSION_ID --secret=gemini-api-key
```

### Disable or Destroy Old Versions

```bash
# Disable an old version (can be re-enabled later)
gcloud secrets versions disable VERSION_ID --secret=gemini-api-key

# Permanently destroy an old version (cannot be undone)
gcloud secrets versions destroy VERSION_ID --secret=gemini-api-key
```

### Pin to a Specific Secret Version

If you need to use a specific version instead of latest:

```bash
gcloud run services update student-assistant \
  --region us-central1 \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:2"
```

> **Security Best Practice:** After confirming the new key works, disable or destroy old versions to prevent unauthorized use if the old key was compromised.

---

## Monitoring and Logs

### View Logs

```bash
# Cloud Run - view recent logs
gcloud run services logs read student-assistant --region us-central1

# Cloud Run - stream logs in real-time (follow mode)
gcloud run services logs tail student-assistant --region us-central1

# Cloud Run - view last 100 log entries
gcloud run services logs read student-assistant --region us-central1 --limit 100

# App Engine - stream logs in real-time
gcloud app logs tail

# App Engine - view recent logs
gcloud app logs read --limit 100
```

### Filter Logs by Severity

```bash
# Cloud Run - view only errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=student-assistant AND severity>=ERROR" --limit 50

# Cloud Run - view errors and warnings
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=student-assistant AND severity>=WARNING" --limit 50
```

### View in Console

- **Cloud Run:** https://console.cloud.google.com/run
- **App Engine:** https://console.cloud.google.com/appengine
- **Cloud Logging:** https://console.cloud.google.com/logs

---

## Autoscaling (Cloud Run)

Cloud Run has autoscaling enabled by default. It automatically scales from 0 to your configured maximum instances based on incoming traffic. You can fine-tune this behavior:

### Configure Instance Limits

```bash
# Set minimum and maximum instances
gcloud run services update student-assistant \
  --region us-central1 \
  --min-instances 1 \
  --max-instances 10
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--min-instances` | Minimum instances kept warm (reduces cold starts) | 0 |
| `--max-instances` | Maximum instances to scale up to | 100 |

> **Cost Note:** Setting `--min-instances` above 0 keeps instances running and incurs charges even without traffic. Use `--min-instances 0` for pay-per-use.

### Configure Concurrency

Control how many requests each instance handles simultaneously:

```bash
# Set max concurrent requests per instance
gcloud run services update student-assistant \
  --region us-central1 \
  --concurrency 80
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--concurrency` | Max concurrent requests per instance | 80 |

- **Higher concurrency** = fewer instances, better resource utilization
- **Lower concurrency** = more instances, better isolation per request

### Configure CPU Allocation

```bash
# CPU always allocated (better for consistent traffic)
gcloud run services update student-assistant \
  --region us-central1 \
  --cpu-boost \
  --no-cpu-throttling

# CPU only allocated during request processing (default, lower cost)
gcloud run services update student-assistant \
  --region us-central1 \
  --cpu-throttling
```

### Example: Production Configuration

```bash
gcloud run services update student-assistant \
  --region us-central1 \
  --min-instances 1 \
  --max-instances 20 \
  --concurrency 100 \
  --cpu-boost \
  --memory 512Mi \
  --cpu 1
```

### Example: Cost-Optimized Configuration

```bash
gcloud run services update student-assistant \
  --region us-central1 \
  --min-instances 0 \
  --max-instances 5 \
  --concurrency 80 \
  --cpu-throttling
```

### View Current Autoscaling Settings

```bash
gcloud run services describe student-assistant \
  --region us-central1 \
  --format="yaml(spec.template.spec.containerConcurrency, spec.template.metadata.annotations)"
```

---

## Stopping and Restarting

### Cloud Run

Cloud Run is serverless and automatically scales to zero when there's no traffic (you're not charged when idle).

**Disable public access (recommended):**

Use ingress settings to block all external traffic without deleting the service:

```bash
# Make inaccessible - only allow internal VPC traffic
gcloud run services update student-assistant \
  --region us-central1 \
  --ingress internal

# Make accessible again - allow all external traffic
gcloud run services update student-assistant \
  --region us-central1 \
  --ingress all
```

This is the cleanest approach because:
- The service stays deployed (no need to redeploy)
- All configuration is preserved
- External requests get a 403 Forbidden error
- No charges while idle (still scales to zero)

**Delete the service entirely:**

If you want to fully remove the service:

```bash
gcloud run services delete student-assistant --region us-central1
```

To redeploy after deletion:

```bash
gcloud run deploy student-assistant \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account=student-assistant-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
```

> **Note:** Deleting the service removes it entirely. The container image remains in Container Registry/Artifact Registry and can be redeployed. Your secrets and service account are not affected.

**Restart the service (deploy a new revision):**
```bash
# Force a new revision by updating an environment variable
gcloud run services update student-assistant \
  --region us-central1 \
  --update-env-vars="RESTART_TIME=$(date +%s)"

# Or redeploy from source
gcloud run deploy student-assistant --source . --region us-central1
```

**Check service status:**
```bash
gcloud run services describe student-assistant --region us-central1
```

**List all revisions:**
```bash
gcloud run revisions list --service student-assistant --region us-central1
```

### App Engine

**Stop a specific version:**
```bash
gcloud app versions stop VERSION_ID
```

**Start a stopped version:**
```bash
gcloud app versions start VERSION_ID
```

**List all versions:**
```bash
gcloud app versions list
```

**View current serving version:**
```bash
gcloud app versions list --filter="traffic_split>0"
```

---

## Cleanup

To avoid incurring charges, delete the resources when no longer needed:

```bash
# Delete Cloud Run service
gcloud run services delete student-assistant --region us-central1

# Delete App Engine (cannot be deleted, but you can disable it)
gcloud app services delete default

# Delete the secret
gcloud secrets delete gemini-api-key
```

---

## Troubleshooting

### "Permission denied" errors
Ensure the Cloud Run service account has access to Secret Manager:
```bash
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:student-assistant-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Application not responding
Check the logs for errors:
```bash
gcloud run services logs read student-assistant --region us-central1 --limit 50
```

### Port issues
Ensure your application listens on the port specified by the `PORT` environment variable (Cloud Run sets this automatically, default 8080).
