#!/bin/bash
# S3 + CloudFront deploy script for MED frontend
# Usage: bash deploy/s3_deploy.sh <EC2_PUBLIC_IP> <S3_BUCKET> [CLOUDFRONT_DISTRIBUTION_ID]
#
# Prerequisites:
#   - AWS CLI configured (aws configure)
#   - Node.js + npm installed
#   - S3 bucket with static website hosting enabled
#   - CloudFront distribution pointing to the S3 bucket (optional but recommended)
#
# Example:
#   bash deploy/s3_deploy.sh 54.123.45.67 my-med-bucket E1ABCDEFGHIJKL

set -e

EC2_IP="${1:?Usage: $0 <EC2_PUBLIC_IP> <S3_BUCKET> [CLOUDFRONT_ID]}"
S3_BUCKET="${2:?Usage: $0 <EC2_PUBLIC_IP> <S3_BUCKET> [CLOUDFRONT_ID]}"
CF_DISTRIBUTION_ID="${3:-}"

FRONTEND_DIR="$(dirname "$0")/../frontend"

echo "=== Building frontend ==="
cd "$FRONTEND_DIR"

# Write production env
echo "VITE_API_URL=http://${EC2_IP}/api" > .env.production

npm install
npm run build

echo "=== Uploading to S3: s3://${S3_BUCKET}/ ==="
aws s3 sync dist/ "s3://${S3_BUCKET}/" \
    --delete \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "index.html"

# index.html should not be cached long-term
aws s3 cp dist/index.html "s3://${S3_BUCKET}/index.html" \
    --cache-control "no-cache, no-store, must-revalidate"

echo "=== S3 upload complete ==="

if [ -n "$CF_DISTRIBUTION_ID" ]; then
    echo "=== Invalidating CloudFront cache ==="
    aws cloudfront create-invalidation \
        --distribution-id "$CF_DISTRIBUTION_ID" \
        --paths "/*"
    echo "=== CloudFront invalidation created ==="
else
    echo "(No CloudFront distribution ID provided, skipping invalidation)"
fi

echo ""
echo "=== Deploy complete! ==="
echo "Frontend URL: http://${S3_BUCKET}.s3-website-<region>.amazonaws.com"
echo "  (or your CloudFront domain if configured)"
echo "API URL: http://${EC2_IP}/api"