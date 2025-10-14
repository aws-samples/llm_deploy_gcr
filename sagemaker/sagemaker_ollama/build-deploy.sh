#!/bin/bash

set -e  # Exit immediately on error

echo "=== Ollama FastAPI SageMaker Endpoint - CodeBuild Deployment ==="

# Configuration parameters - use environment variables first, fallback to defaults
PROJECT_NAME=${PROJECT_NAME:-"sagemaker_endpoint_ollama"}
REPO_TAG=${REPO_TAG:-"0.12.5"}
ARCHITECTURE=${ARCHITECTURE:-"arm64"}  # Options: arm64, x86_64, amd64
REGION=${AWS_DEFAULT_REGION:-$(aws configure get region 2>/dev/null || echo "us-west-2")}
ACCOUNT=${ACCOUNT:-$(aws sts get-caller-identity --query Account --output text)}

# S3 configuration - use SageMaker default bucket format
S3_BUCKET=${S3_BUCKET:-"sagemaker-${REGION}-${ACCOUNT}"}
S3_KEY=${S3_KEY:-"codebuild/${PROJECT_NAME}.zip"}

# Architecture-specific configuration
if [ "$ARCHITECTURE" = "arm64" ]; then
  CONTAINER_TYPE="ARM_CONTAINER"
  CODEBUILD_IMAGE="aws/codebuild/amazonlinux2-aarch64-standard:3.0"
  DOCKER_PLATFORM="linux/arm64"
elif [ "$ARCHITECTURE" = "x86_64" ] || [ "$ARCHITECTURE" = "amd64" ]; then
  CONTAINER_TYPE="LINUX_CONTAINER"
  CODEBUILD_IMAGE="aws/codebuild/standard:7.0"
  DOCKER_PLATFORM="linux/amd64"
else
  echo "Error: Unsupported architecture: $ARCHITECTURE"
  echo "Supported architectures: arm64, x86_64, amd64"
  exit 1
fi

echo "Configuration:"
echo "  Project Name: $PROJECT_NAME"
echo "  Architecture: $ARCHITECTURE"
echo "  Container Type: $CONTAINER_TYPE"
echo "  CodeBuild Image: $CODEBUILD_IMAGE"
echo "  Docker Platform: $DOCKER_PLATFORM"
echo "  S3 Bucket: $S3_BUCKET"
echo "  S3 Key: $S3_KEY"
echo "  Repo Tag: $REPO_TAG"
echo "  Region: $REGION"
echo "  Account: $ACCOUNT"
echo ""

# ===== Step 1: Create/Update CodeBuild Project =====
echo "Step 1: Setting up CodeBuild project..."

# Create service role
ROLE_NAME="CodeBuildServiceRole-${PROJECT_NAME}"
ROLE_ARN="arn:aws:iam::${ACCOUNT}:role/${ROLE_NAME}"

echo "Checking IAM role: $ROLE_NAME"

# Check if role exists
aws iam get-role --role-name $ROLE_NAME > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Creating IAM role..."
  
  # Create trust policy
  cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

  # Create role
  aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document file://trust-policy.json

  rm trust-policy.json
  echo "IAM role created"
else
  echo "IAM role already exists"
fi

# Create/update permissions policy
echo "Updating IAM permissions..."
cat > permissions-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": [
        "arn:aws:logs:${REGION}:${ACCOUNT}:log-group:/aws/codebuild/${PROJECT_NAME}",
        "arn:aws:logs:${REGION}:${ACCOUNT}:log-group:/aws/codebuild/${PROJECT_NAME}:*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:GetAuthorizationToken",
        "ecr:CreateRepository",
        "ecr:DescribeRepositories",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::${S3_BUCKET}/*"
    },
    {
      "Effect": "Allow",
      "Action": "sts:GetCallerIdentity",
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name CodeBuildPolicy \
  --policy-document file://permissions-policy.json

rm permissions-policy.json
echo "IAM permissions updated"

# Create CodeBuild project configuration
cat > codebuild-project.json << EOF
{
  "name": "$PROJECT_NAME",
  "description": "Build and push Ollama FastAPI SageMaker Endpoint Docker image for ${ARCHITECTURE}",
  "source": {
    "type": "S3",
    "location": "$S3_BUCKET/$S3_KEY",
    "buildspec": "buildspec.yml"
  },
  "artifacts": {
    "type": "NO_ARTIFACTS"
  },
  "environment": {
    "type": "$CONTAINER_TYPE",
    "image": "$CODEBUILD_IMAGE",
    "computeType": "BUILD_GENERAL1_LARGE",
    "privilegedMode": true,
    "environmentVariables": [
      {
        "name": "DOCKER_PLATFORM",
        "value": "$DOCKER_PLATFORM"
      }
    ]
  },
  "serviceRole": "$ROLE_ARN",
  "timeoutInMinutes": 30
}
EOF

# Check if project already exists
aws codebuild batch-get-projects --names $PROJECT_NAME > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "Updating existing CodeBuild project..."
  aws codebuild update-project --cli-input-json file://codebuild-project.json
else
  echo "Creating new CodeBuild project..."
  aws codebuild create-project --cli-input-json file://codebuild-project.json
fi

rm codebuild-project.json
echo "CodeBuild project ready"
echo ""

# ===== Step 2: Upload Source Code to S3 =====
echo "Step 2: Uploading source code to S3..."

# Check if S3 bucket exists
aws s3 ls "s3://$S3_BUCKET" > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Creating S3 bucket: $S3_BUCKET"
  if [ "$REGION" = "us-east-1" ]; then
    aws s3 mb "s3://$S3_BUCKET"
  else
    aws s3 mb "s3://$S3_BUCKET" --region $REGION
  fi
fi

# Create source code zip file
echo "Creating source code archive..."
zip -r source.zip ./app buildspec.yml dockerfile requirements.txt \
  -x "*.git*" \
  -x "*.DS_Store*" \
  -x "*.pyc" \
  -x "*__pycache__*" \
  -x "source.zip" \
  -x "codebuild-template.yaml" \
  -x "deploy-codebuild.sh" \
  -x "create-codebuild-simple.sh" \
  -x "upload-source.sh" \
  -x "trigger-build.sh" \
  -x "config.sh"

# Upload to S3
echo "Uploading to S3..."
aws s3 cp source.zip "s3://$S3_BUCKET/$S3_KEY"

if [ $? -eq 0 ]; then
  echo "Source code uploaded successfully!"
  echo "S3 Location: s3://$S3_BUCKET/$S3_KEY"
  rm source.zip
else
  echo "Failed to upload source code!"
  exit 1
fi
echo ""

# ===== Step 3: Trigger Build =====
echo "Step 3: Starting CodeBuild..."

BUILD_ID=$(aws codebuild start-build \
  --project-name $PROJECT_NAME \
  --environment-variables-override \
    name=REPO_TAG,value=$REPO_TAG \
  --query 'build.id' \
  --output text)

if [ $? -eq 0 ]; then
  echo "Build started successfully!"
  echo "Build ID: $BUILD_ID"
  echo ""
  echo "Monitor build progress:"
  echo "  aws codebuild batch-get-builds --ids $BUILD_ID"
  echo ""
  echo "View in AWS Console:"
  echo "  https://$REGION.console.aws.amazon.com/codesuite/codebuild/projects/$PROJECT_NAME/build/$BUILD_ID"
  echo ""
  echo "=== Deployment Complete! ==="
  echo "Your $ARCHITECTURE Docker image will be available in ECR once the build completes."
else
  echo "Failed to start build!"
  exit 1
fi