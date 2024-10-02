y#!/bin/bash
# Purpose: To deploy the App to Cloud Run.

# Google Cloud Project ID
PROJECT=rahul-research-test

# Google Cloud Region
LOCATION=asia-south1

# Deploy app from source code
gcloud run deploy document-summarization-app --source . --region=$LOCATION --project=$PROJECT --allow-unauthenticated