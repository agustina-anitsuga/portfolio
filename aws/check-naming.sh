#!/usr/bin/env bash
# After a deploy: lists every resource of the stack plus the ones created
# outside it, and flags any name that does not start with "portfolio" or any
# taggable resource missing project=portfolio.
set -euo pipefail
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
aws cloudformation list-stack-resources --stack-name portfolio \
  --query 'StackResourceSummaries[].[ResourceType,PhysicalResourceId]' --output text > /tmp/portfolio-resources.txt
aws resourcegroupstaggingapi get-resources --tag-filters Key=project,Values=portfolio \
  --query 'ResourceTagMappingList[].ResourceARN' --output text | tr '\t' '\n' > /tmp/portfolio-tagged.txt
python3 - "$ACCOUNT" <<'PY'
import sys
account = sys.argv[1]
tagged = open("/tmp/portfolio-tagged.txt").read()
# resource types CloudFormation/AWS cannot tag or name (they hang off a named parent)
untaggable = {"AWS::S3::BucketPolicy", "AWS::Lambda::Permission", "AWS::Lambda::EventInvokeConfig",
              "AWS::Cognito::UserPoolClient", "AWS::Cognito::UserPoolDomain",
              "AWS::Cognito::UserPoolUser", "AWS::Cognito::ManagedLoginBranding",
              "AWS::CloudFront::OriginAccessControl"}
import json, subprocess
def role_tagged(name):
    out = subprocess.run(["aws", "iam", "list-role-tags", "--role-name", name, "--output", "json"],
                         capture_output=True, text=True).stdout or "{}"
    return any(t["Key"] == "project" and t["Value"] == "portfolio"
               for t in json.loads(out).get("Tags", []))
problems = 0
for line in open("/tmp/portfolio-resources.txt"):
    rtype, physical = line.rstrip("\n").split("\t")
    if rtype == "AWS::IAM::Role":
        is_tagged = role_tagged(physical)
    else:
        is_tagged = f"/{physical}" in tagged or f":{physical}" in tagged
    flag = ""
    if rtype not in untaggable and not is_tagged:
        flag += " SIN-TAG"
    print(f"{rtype:40} {physical:60}{flag}")
    problems += bool(flag)
print("\nOK" if not problems else f"\n{problems} recursos con problemas")
PY
for p in portfolio-ppi portfolio-google-credentials; do
  printf "%-40s %-60s " "AWS::SSM::Parameter" "$p"
  aws ssm list-tags-for-resource --resource-type Parameter --resource-id "$p" \
    --query "TagList[?Key=='project'].Value" --output text 2>/dev/null || echo "(no existe)"
done
printf "%-40s %-60s " "AWS::S3::Bucket (deploy)" "portfolio-deploy-$ACCOUNT"
aws s3api get-bucket-tagging --bucket "portfolio-deploy-$ACCOUNT" --query "TagSet[?Key=='project'].Value" --output text
