#!/bin/bash
# Script to empty S3 bucket with versioning enabled
# This deletes all object versions and delete markers

set -e

BUCKET_NAME="aws-config-$(aws sts get-caller-identity --query Account --output text)"

echo "Emptying bucket: $BUCKET_NAME"
echo "This will delete all objects and versions..."

# Delete all object versions
echo "Deleting object versions..."
aws s3api list-object-versions \
  --bucket "$BUCKET_NAME" \
  --output json \
  --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' | \
jq -r '.Objects // [] | .[] | "\(.Key)\t\(.VersionId)"' | \
while IFS=$'\t' read -r key versionId; do
  if [ -n "$key" ] && [ -n "$versionId" ]; then
    echo "Deleting version: $key ($versionId)"
    aws s3api delete-object --bucket "$BUCKET_NAME" --key "$key" --version-id "$versionId" || true
  fi
done

# Delete all delete markers
echo "Deleting delete markers..."
aws s3api list-object-versions \
  --bucket "$BUCKET_NAME" \
  --output json \
  --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' | \
jq -r '.Objects // [] | .[] | "\(.Key)\t\(.VersionId)"' | \
while IFS=$'\t' read -r key versionId; do
  if [ -n "$key" ] && [ -n "$versionId" ]; then
    echo "Deleting delete marker: $key ($versionId)"
    aws s3api delete-object --bucket "$BUCKET_NAME" --key "$key" --version-id "$versionId" || true
  fi
done

echo "Bucket emptied successfully!"
echo "You can now run: terragrunt destroy"