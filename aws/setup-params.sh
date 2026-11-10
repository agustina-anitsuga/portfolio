#!/usr/bin/env bash
# Stores the PPI keys in SSM Parameter Store (SecureString, encrypted with
# the account's aws/ssm key), named portfolio-ppi and tagged project=portfolio.
# Reads PPI_PUBLIC_KEY / PPI_PRIVATE_KEY from the environment: `source keys.txt` first.
set -euo pipefail
: "${PPI_PUBLIC_KEY:?source keys.txt first}" "${PPI_PRIVATE_KEY:?source keys.txt first}"
PARAM=portfolio-ppi
VALUE=$(python3 -c 'import json,os;print(json.dumps({"public_key":os.environ["PPI_PUBLIC_KEY"],"private_key":os.environ["PPI_PRIVATE_KEY"]}))')
aws ssm put-parameter --name "$PARAM" --type SecureString --overwrite --value "$VALUE" >/dev/null
aws ssm add-tags-to-resource --resource-type Parameter --resource-id "$PARAM" \
  --tags Key=project,Value=portfolio
echo "Guardado $PARAM"
