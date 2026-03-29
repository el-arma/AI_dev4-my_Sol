#!/bin/bash

set -e

REPO_URL="https://github.com/el-arma/AI_dev4-my_Sol.git"
SPARSE_PATH="templates/S0105_VPS-deploy-ai-agent"
DEPLOY_DIR="/opt/build-app"

if [ ! -d "$DEPLOY_DIR/.git" ]; then
  git clone --filter=blob:none --sparse "$REPO_URL" "$DEPLOY_DIR"
  cd "$DEPLOY_DIR"
  git sparse-checkout set "$SPARSE_PATH"
else
  cd "$DEPLOY_DIR"
  git fetch origin
  git reset --hard origin/master
fi

cd "$DEPLOY_DIR/$SPARSE_PATH"

docker-compose up -d --build

echo "Deployment completed at $(date)"