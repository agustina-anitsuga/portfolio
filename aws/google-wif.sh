#!/usr/bin/env bash
# Lets the worker Lambda read the spreadsheet as the Google service account
# WITHOUT any key: Google's Workload Identity Federation trusts the Lambda's
# AWS role and hands it short-lived tokens of the service account.
#
# Idempotent: re-running it only creates what is missing. Needs gcloud logged
# in with your user (gcloud auth login) and the AWS CLI.
#   GCP_PROJECT=... GCP_SERVICE_ACCOUNT=...@....iam.gserviceaccount.com aws/google-wif.sh
set -euo pipefail
: "${GCP_PROJECT:?definí GCP_PROJECT}" "${GCP_SERVICE_ACCOUNT:?definí GCP_SERVICE_ACCOUNT}"
POOL=portfolio-aws
PROVIDER=portfolio-aws-provider
PARAM=portfolio-google-credentials
ROLE=portfolio-refresh-worker           # fixed name, see WorkerRole in template.yaml
GCLOUD="${GCLOUD:-gcloud}"

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
NUMBER=$("$GCLOUD" projects describe "$GCP_PROJECT" --format='value(projectNumber)')
POOL_PATH="projects/$NUMBER/locations/global/workloadIdentityPools/$POOL"

"$GCLOUD" services enable sts.googleapis.com iamcredentials.googleapis.com \
  drive.googleapis.com --project "$GCP_PROJECT"

"$GCLOUD" iam workload-identity-pools describe "$POOL" --location global \
    --project "$GCP_PROJECT" >/dev/null 2>&1 ||
  "$GCLOUD" iam workload-identity-pools create "$POOL" --location global \
    --project "$GCP_PROJECT" --display-name "portfolio (AWS)"

# The default AWS attribute mapping sets attribute.aws_role to
# arn:aws:sts::<account>:assumed-role/<role>; the condition rejects anything
# that is not the worker role, even from the same AWS account.
"$GCLOUD" iam workload-identity-pools providers describe "$PROVIDER" \
    --workload-identity-pool "$POOL" --location global --project "$GCP_PROJECT" >/dev/null 2>&1 ||
  "$GCLOUD" iam workload-identity-pools providers create-aws "$PROVIDER" \
    --workload-identity-pool "$POOL" --location global --project "$GCP_PROJECT" \
    --account-id "$AWS_ACCOUNT" \
    --attribute-condition "attribute.aws_role == 'arn:aws:sts::$AWS_ACCOUNT:assumed-role/$ROLE'"

"$GCLOUD" iam service-accounts add-iam-policy-binding "$GCP_SERVICE_ACCOUNT" \
  --project "$GCP_PROJECT" --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/$POOL_PATH/attribute.aws_role/arn:aws:sts::$AWS_ACCOUNT:assumed-role/$ROLE" \
  >/dev/null

CONFIG=$(mktemp)
trap 'rm -f "$CONFIG"' EXIT
"$GCLOUD" iam workload-identity-pools create-cred-config "$POOL_PATH/providers/$PROVIDER" \
  --service-account "$GCP_SERVICE_ACCOUNT" --aws --output-file "$CONFIG"
# The file holds no secret: only which pool, provider and service account to use.
aws ssm put-parameter --name "$PARAM" --type String --overwrite --value "file://$CONFIG" >/dev/null
aws ssm add-tags-to-resource --resource-type Parameter --resource-id "$PARAM" \
  --tags Key=project,Value=portfolio
echo "Listo: Workload Identity Federation configurado y guardado en $PARAM"
