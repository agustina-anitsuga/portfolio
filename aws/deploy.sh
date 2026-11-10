#!/usr/bin/env bash
# Builds and deploys the stack, then publishes the login page.
#   ADMIN_EMAIL=you@example.com PORTFOLIO_SHEET_ID=... aws/deploy.sh
#
# Naming rule: everything this creates is named portfolio* and tagged
# project=portfolio -- including the bucket SAM uploads the code to, which is
# ours instead of SAM's default "aws-sam-cli-managed-default-..." stack.
set -euo pipefail
cd "$(dirname "$0")/.."
STACK=portfolio
TAG_KEY=project TAG_VALUE=portfolio
: "${ADMIN_EMAIL:?definí ADMIN_EMAIL}" "${PORTFOLIO_SHEET_ID:?definí PORTFOLIO_SHEET_ID}"
REGION=$(aws configure get region || echo us-east-1)
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
DEPLOY_BUCKET="portfolio-deploy-$ACCOUNT"

if ! aws s3api head-bucket --bucket "$DEPLOY_BUCKET" 2>/dev/null; then
  if [ "$REGION" = us-east-1 ]; then
    aws s3api create-bucket --bucket "$DEPLOY_BUCKET" >/dev/null
  else
    aws s3api create-bucket --bucket "$DEPLOY_BUCKET" \
      --create-bucket-configuration "LocationConstraint=$REGION" >/dev/null
  fi
  aws s3api put-public-access-block --bucket "$DEPLOY_BUCKET" --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  # old code packages are useless after a deploy
  aws s3api put-bucket-lifecycle-configuration --bucket "$DEPLOY_BUCKET" --lifecycle-configuration \
    '{"Rules":[{"ID":"portfolio-expire-packages","Status":"Enabled","Filter":{"Prefix":""},"Expiration":{"Days":30}}]}'
fi
aws s3api put-bucket-tagging --bucket "$DEPLOY_BUCKET" \
  --tagging "TagSet=[{Key=$TAG_KEY,Value=$TAG_VALUE}]"

aws/build.sh
sam deploy --template-file aws/template.yaml --stack-name "$STACK" \
  --s3-bucket "$DEPLOY_BUCKET" --s3-prefix portfolio \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --tags "$TAG_KEY=$TAG_VALUE" \
  --no-fail-on-empty-changeset \
  --parameter-overrides "AdminEmail=$ADMIN_EMAIL" "SheetId=$PORTFOLIO_SHEET_ID"

out() { aws cloudformation describe-stacks --stack-name "$STACK" \
          --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }
SITE_BUCKET=$(out SiteBucketName)
cat > .aws-build/config.js <<JS
window.PORTFOLIO_CONFIG = {
  apiUrl: "$(out ApiUrl)",
  cognitoDomain: "$(out CognitoDomain)",
  clientId: "$(out UserPoolClientId)"
};
JS
aws s3 cp aws/site/index.html "s3://$SITE_BUCKET/index.html" --content-type "text/html; charset=utf-8"
aws s3 cp .aws-build/config.js "s3://$SITE_BUCKET/config.js" --content-type "application/javascript"
echo
echo "Listo: $(out SiteUrl)"
