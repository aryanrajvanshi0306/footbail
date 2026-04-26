#!/bin/bash
# LocalStack initialisation — runs once when LocalStack is ready
# Creates: S3 buckets, DynamoDB table, SQS queue

set -e
ENDPOINT=http://localhost:4566

echo "🚀  footbAIl LocalStack init starting..."

# ── S3 Buckets ────────────────────────────────────────────────────────────────
echo "📦  Creating S3 buckets..."
aws --endpoint-url=$ENDPOINT s3 mb s3://footbail-raw-videos      --region ap-south-1 2>/dev/null || true
aws --endpoint-url=$ENDPOINT s3 mb s3://footbail-processed-videos --region ap-south-1 2>/dev/null || true

# Set CORS on raw bucket so the browser can PUT directly
aws --endpoint-url=$ENDPOINT s3api put-bucket-cors \
  --bucket footbail-raw-videos \
  --cors-configuration '{
    "CORSRules": [{
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET","PUT","POST","DELETE","HEAD"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3600
    }]
  }' 2>/dev/null || true

echo "✅  S3 buckets ready"

# ── DynamoDB — MatchEvents ─────────────────────────────────────────────────────
echo "🗄️   Creating DynamoDB MatchEvents table..."
aws --endpoint-url=$ENDPOINT dynamodb create-table \
  --table-name MatchEvents \
  --attribute-definitions \
    AttributeName=match_id,AttributeType=S \
    AttributeName=event_timestamp,AttributeType=N \
  --key-schema \
    AttributeName=match_id,KeyType=HASH \
    AttributeName=event_timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1 2>/dev/null || true

echo "✅  DynamoDB MatchEvents ready"

# ── SQS — Video Processing Queue ──────────────────────────────────────────────
echo "📨  Creating SQS queue..."
aws --endpoint-url=$ENDPOINT sqs create-queue \
  --queue-name footbail-video-processing \
  --region ap-south-1 2>/dev/null || true

echo "✅  SQS queue ready"

# ── Seed placeholder HLS content in processed bucket ──────────────────────────
echo "🎬  Seeding placeholder HLS content..."
TMPDIR=$(mktemp -d)

# Create a minimal valid m3u8 playlist
cat > "$TMPDIR/playlist.m3u8" << 'EOF'
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXTINF:10.000,
segment_000.ts
#EXT-X-ENDLIST
EOF

# Create a minimal TS segment (just header bytes for demo)
dd if=/dev/urandom bs=1024 count=512 2>/dev/null | head -c 524288 > "$TMPDIR/segment_000.ts" || true

# Upload placeholder
aws --endpoint-url=$ENDPOINT s3 cp "$TMPDIR/playlist.m3u8" \
  s3://footbail-processed-videos/placeholder/playlist.m3u8 2>/dev/null || true
aws --endpoint-url=$ENDPOINT s3 cp "$TMPDIR/segment_000.ts" \
  s3://footbail-processed-videos/placeholder/segment_000.ts 2>/dev/null || true

rm -rf "$TMPDIR"
echo "✅  Placeholder HLS seeded"

echo ""
echo "🎉  footbAIl LocalStack initialisation COMPLETE"
echo "   S3:       footbail-raw-videos, footbail-processed-videos"
echo "   DynamoDB: MatchEvents"
echo "   SQS:      footbail-video-processing"
