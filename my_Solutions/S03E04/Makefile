# ============================================================
# S03E04 Pipeline
# ============================================================
# Steps:
#   1. get-data      — download CSV files from the data source
#   2. setup-db      — load CSVs into SQLite (replaces stock table)
#   3. health-check  — validate DB schema, row count, and data integrity
# ============================================================

.PHONY: all get-data setup-db health-check deploy-local deploy-remote test-local

# Default target: run the full pipeline
all: get-data setup-db health-check deploy-local test-local deploy-remote

# Step 1: Download CSV data files
get-data:
	@echo "MAKE STEP [1/5] get-data - downloading CSV files..."
	python get_data.py

# Step 2: Build SQLite DB from downloaded CSVs
setup-db:
	@echo "MAKE STEP [2/5] setup-db - building SQLite DB from CSVs..."
	python db_setup.py

# Step 3: Validate DB schema, row count, and data integrity
health-check:
	@echo "MAKE STEP [3/5] health-check - validating DB schema and data..."
	python db_health_check.py

# Step 4: Build and start the container locally
deploy-local:
	@echo "MAKE STEP [4/5] deploy-local - building and starting container..."
	docker compose -f tool_deploy/docker-compose.yml up -d --build

# Step 5: Run smoke + domain tests against the local container (localhost:8001)
# give 3 sec for container to start running
test-local:
	@echo "MAKE STEP [5/5] test-local - waiting 3s for container to start..."
	python -c "import time; time.sleep(3)"
	@echo "test-local - running tests..."
	pytest test_local_deploy.py -v

#!!! DO MANUALLY !!!
# Step 6: Upload tool_deploy to hetzner-prod
# cd my_Solutions\S03E04
# scp -r tool_deploy hetzner-prod:/deploy/S03E04-tool-deploy/

# Step 7: Build container
# cd /deploy/S03E04-tool-deploy/tool_deploy && docker-compose up -d --build
