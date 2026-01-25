# DeepThought Manual Testing Guide

This guide provides step-by-step instructions for manually testing the DeepThought backend service. Follow these steps to set up your local environment and verify all components work correctly.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Clone the Repository](#step-1-clone-the-repository)
3. [Set Up Python Environment](#step-2-set-up-python-environment)
4. [Configure Environment Variables](#step-3-configure-environment-variables)
5. [Start Infrastructure (DynamoDB + Ollama)](#step-4-start-infrastructure)
6. [Set Up Ollama Models](#step-5-set-up-ollama-models)
7. [Create Table and Seed Data](#step-6-create-table-and-seed-data)
8. [Start the FastAPI Server](#step-7-start-the-fastapi-server)
9. [Test Health Endpoint](#step-8-test-health-endpoint)
10. [Test Calculate Endpoint](#step-9-test-calculate-endpoint)
11. [Test All Operations (Add, Multiply, Divide)](#step-10-test-all-operations)
12. [Test Error Scenarios](#step-11-test-error-scenarios)
13. [Explore API Documentation](#step-12-explore-api-documentation)
14. [Run Automated Tests](#step-13-run-automated-tests)
15. [Cleanup](#step-14-cleanup)
16. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have the following installed on your system:

| Requirement | Minimum Version | Check Command |
|-------------|-----------------|---------------|
| Python | 3.11+ | `python3 --version` |
| Docker | 20.0+ | `docker --version` |
| Docker Compose | 2.0+ | `docker compose version` |
| Git | 2.0+ | `git --version` |
| curl | Any | `curl --version` |

You will also need:
- **LLM Provider** (choose one):
  - **Ollama** (Recommended for local/free): Runs open source models locally, no API key needed
  - **Anthropic API Key**: For cloud-based Claude models. Get one at [console.anthropic.com](https://console.anthropic.com/)
- **~2GB disk space**: For Docker images, Python dependencies, and LLM models
- **Internet connection**: For downloading dependencies and models

---

## Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/aaronbengochea/DeepThought.git

# Navigate to the project directory
cd DeepThought
```

Verify you're in the correct directory:
```bash
ls -la
```

You should see files like `pyproject.toml`, `docker-compose.yml`, and directories like `src/` and `tests/`.

---

## Step 2: Set Up Python Environment

### 2.1 Create a Virtual Environment

```bash
# Create a new virtual environment
python3 -m venv .venv
```

### 2.2 Activate the Virtual Environment

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

**On Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**On Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

Your terminal prompt should now show `(.venv)` at the beginning.

### 2.3 Upgrade pip

```bash
pip install --upgrade pip
```

### 2.4 Install the Package with Dev Dependencies

```bash
pip install -e ".[dev]"
```

This installs:
- FastAPI and Uvicorn (web framework)
- LangGraph and LangChain (AI agent framework)
- Boto3 (AWS SDK for DynamoDB)
- Pydantic (data validation)
- Pytest and other dev tools

### 2.5 Verify Installation

```bash
# Check that the package is installed
pip show deepthought

# Verify key imports work
python -c "from deepthought.api.app import create_app; print('Installation successful!')"
```

---

## Step 3: Configure Environment Variables

### 3.1 Create the .env File

```bash
# Copy the example environment file
cp .env.example .env
```

### 3.2 Edit the .env File

Open `.env` in your preferred editor and configure the following:

```bash
# Application settings
APP_NAME=DeepThought
DEBUG=true
LOG_LEVEL=DEBUG

# AWS Configuration (use dummy values for local testing)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy

# DynamoDB Configuration
DYNAMODB_TABLE_NAME=deepthought-calculations
DYNAMODB_ENDPOINT_URL=http://localhost:8000

# LLM Provider Configuration (choose one)
# Option 1: Ollama (Recommended - free, local)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434

# Option 2: Anthropic (cloud-based, requires API key)
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-3-haiku-20240307
# ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000"]
```

### 3.3 Important Notes

- **LLM_PROVIDER**: Choose `ollama` for free local models or `anthropic` for cloud-based Claude models.
- **Ollama**: No API key required. Runs models locally. Recommended for testing and development.
- **Anthropic**: Requires a valid API key from [console.anthropic.com](https://console.anthropic.com/).
- **DYNAMODB_ENDPOINT_URL**: Must be `http://localhost:8000` to connect to the local DynamoDB instance.
- **AWS credentials**: Can be dummy values when using local DynamoDB.

---

## Step 4: Start Infrastructure (DynamoDB + Ollama)

### 4.1 Start All Services with Docker Compose

```bash
docker compose up -d
```

This starts:
- **DynamoDB Local**: Database on port 8000
- **Ollama**: LLM server on port 11434

### 4.2 Verify Services are Running

```bash
# Check container status
docker ps
```

Expected output:
```
CONTAINER ID   IMAGE                   PORTS                     NAMES
abc123...      amazon/dynamodb-local   0.0.0.0:8000->8000/tcp    deepthought-dynamodb
def456...      ollama/ollama:latest    0.0.0.0:11434->11434/tcp  deepthought-ollama
```

### 4.3 Test DynamoDB Connection

```bash
# Test that DynamoDB is responding
curl http://localhost:8000
```

You should see an error message like `{"__type":"com.amazon.coral.service#SerializationException"}` - this is expected and confirms DynamoDB is running.

### 4.4 Test Ollama Connection

```bash
# Test that Ollama is responding
curl http://localhost:11434/api/tags
```

You should see a JSON response with available models (may be empty if no models are pulled yet).

---

## Step 5: Set Up Ollama Models

If you're using Ollama as your LLM provider, you need to pull the required models.

### 5.1 Run the Setup Script

```bash
python scripts/setup_ollama.py
```

### 5.2 Expected Output

```
Checking Ollama availability at http://localhost:11434...
Ollama is available!
Pulling model: llama3.2...
Successfully pulled llama3.2
Pulling model: mistral...
Successfully pulled mistral
All models ready!
```

### 5.3 Verify Models are Available

```bash
curl http://localhost:11434/api/tags | python -m json.tool
```

You should see `llama3.2` and `mistral` in the list of models.

### 5.4 Manual Model Pull (Alternative)

If the script doesn't work, you can pull models manually:

```bash
# Using docker exec
docker exec deepthought-ollama ollama pull llama3.2
docker exec deepthought-ollama ollama pull mistral
```

### 5.5 Skip This Step If Using Anthropic

If you've configured `LLM_PROVIDER=anthropic` in your `.env` file, you can skip this step. The system will use the Anthropic API instead of local Ollama models.

---

## Step 6: Create Table and Seed Data

### 6.1 Run the Seed Script

```bash
python scripts/seed_data.py
```

### 6.2 Expected Output

```
Connecting to local DynamoDB at http://localhost:8000
Created table: deepthought-calculations
Seeded: CALC#test/ITEM#001
Seeded: CALC#test/ITEM#002
Seeded: CALC#user123/ITEM#calc001
Done!
```

### 6.3 Seeded Test Data Reference

The script creates the following test records:

| Partition Key | Sort Key | val1 | val2 | Expected Sum |
|--------------|----------|------|------|--------------|
| `CALC#test` | `ITEM#001` | 42 | 58 | 100 |
| `CALC#test` | `ITEM#002` | 100 | 200 | 300 |
| `CALC#user123` | `ITEM#calc001` | 15 | 25 | 40 |

---

## Step 7: Start the FastAPI Server

### 7.1 Start the Development Server

```bash
uvicorn src.deepthought.api.app:create_app --factory --reload --port 8080
```

**Flags explained:**
- `--factory`: Uses the `create_app()` factory function
- `--reload`: Auto-reloads on code changes (dev mode)
- `--port 8080`: Runs on port 8080 (avoids conflict with DynamoDB on 8000)

### 7.2 Expected Output

```
INFO:     Will watch for changes in these directories: ['/path/to/DeepThought']
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 7.3 Keep This Terminal Open

Leave this terminal running and open a **new terminal** for the following test commands. Remember to activate the virtual environment in the new terminal if needed.

---

## Step 8: Test Health Endpoint

### 8.1 Basic Health Check

```bash
curl http://localhost:8080/health
```

### 8.2 Expected Response

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-18T12:00:00.000000+00:00"
}
```

### 8.3 Pretty-Print Response

```bash
curl -s http://localhost:8080/health | python -m json.tool
```

### 8.4 Verify Response Fields

| Field | Expected Value | Description |
|-------|---------------|-------------|
| `status` | `"healthy"` | Service health status |
| `version` | `"0.1.0"` | Application version |
| `timestamp` | ISO 8601 datetime | Current server time |

---

## Step 9: Test Calculate Endpoint

The `/api/v1/tasks/calculate` endpoint executes the multi-agent pipeline:
1. **Orchestrator** creates a plan (uses LLM to decide operation)
2. **Execution** agent queries DynamoDB and performs the operation (add/multiply/divide)
3. **Verification** agent validates the result using verification tools
4. **Response** agent formats the output

### 9.1 Test Case 1: Basic Addition (42 + 58 = 100)

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "partition_key": "CALC#test",
    "sort_key": "ITEM#001"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "request_id": "uuid-string-here",
  "data": {
    "val1": 42,
    "val2": 58,
    "result": 100,
    "verification_status": "passed"
  },
  "execution_summary": {
    "request_id": "uuid-string-here",
    "plan_id": "uuid-string-here",
    "steps_executed": 2,
    "verification_confidence": 1.0,
    "verification_checks": 2
  },
  "errors": null
}
```

### 9.2 Test Case 2: Larger Numbers (100 + 200 = 300)

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "partition_key": "CALC#test",
    "sort_key": "ITEM#002"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "request_id": "...",
  "data": {
    "val1": 100,
    "val2": 200,
    "result": 300,
    "verification_status": "passed"
  },
  ...
}
```

### 9.3 Test Case 3: User Calculation (15 + 25 = 40)

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "partition_key": "CALC#user123",
    "sort_key": "ITEM#calc001"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "request_id": "...",
  "data": {
    "val1": 15,
    "val2": 25,
    "result": 40,
    "verification_status": "passed"
  },
  ...
}
```

### 9.4 Pretty-Print with jq (Optional)

If you have `jq` installed:
```bash
curl -s -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{"partition_key": "CALC#test", "sort_key": "ITEM#001"}' | jq .
```

---

## Step 10: Test All Operations (Add, Multiply, Divide)

The system supports three mathematical operations. The orchestrator agent uses the LLM to determine which operation to perform based on the request.

### 10.1 Test Addition with Operation Parameter

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "partition_key": "CALC#test",
    "sort_key": "ITEM#001",
    "operation": "add"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "val1": 42,
    "val2": 58,
    "result": 100,
    "operation": "add",
    "expression": "42 + 58 = 100",
    "verification_status": "passed"
  },
  ...
}
```

### 10.2 Test Multiplication

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "partition_key": "CALC#test",
    "sort_key": "ITEM#001",
    "operation": "multiply"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "val1": 42,
    "val2": 58,
    "result": 2436,
    "operation": "multiply",
    "expression": "42 * 58 = 2436",
    "verification_status": "passed"
  },
  ...
}
```

### 10.3 Test Division

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "partition_key": "CALC#test",
    "sort_key": "ITEM#002",
    "operation": "divide"
  }'
```

**Expected Response (100 / 200 = 0.5):**
```json
{
  "success": true,
  "data": {
    "val1": 100,
    "val2": 200,
    "result": 0.5,
    "operation": "divide",
    "expression": "100 / 200 = 0.5",
    "verification_status": "passed"
  },
  ...
}
```

### 10.4 Test Division by Zero Handling

First, you may need to seed a test record with val2=0. Alternatively, test the verification:

```bash
# The system should handle division by zero gracefully
# If you seed data with val2=0, the divide operation should return an error message
```

### 10.5 Verify Each Operation Uses Correct Tool

Check the server logs while running each operation. You should see:
- **add**: Uses `add_values` tool, verified with `verify_addition`
- **multiply**: Uses `multiply_values` tool, verified with `verify_multiplication`
- **divide**: Uses `divide_values` tool, verified with `verify_division`

---

## Step 11: Test Error Scenarios

### 11.1 Non-Existent Record

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "partition_key": "CALC#nonexistent",
    "sort_key": "ITEM#999"
  }'
```

**Expected:** The response should indicate the item was not found or the calculation failed.

### 11.2 Invalid Request Body

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "invalid_field": "value"
  }'
```

**Expected:** HTTP 422 Unprocessable Entity with validation error details.

### 11.3 Missing Content-Type Header

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -d '{"partition_key": "CALC#test", "sort_key": "ITEM#001"}'
```

**Expected:** HTTP 422 error indicating missing or invalid content type.

### 11.4 Empty Request Body

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected:** HTTP 422 with validation errors for missing required fields.

### 11.5 GET Request to POST Endpoint

```bash
curl http://localhost:8080/api/v1/tasks/calculate
```

**Expected:** HTTP 405 Method Not Allowed.

### 11.6 Invalid Operation

```bash
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "partition_key": "CALC#test",
    "sort_key": "ITEM#001",
    "operation": "invalid_operation"
  }'
```

**Expected:** The system should default to "add" or return an appropriate error.

---

## Step 12: Explore API Documentation

FastAPI automatically generates interactive API documentation.

### 12.1 Swagger UI

Open in your browser:
```
http://localhost:8080/docs
```

Features:
- Interactive API explorer
- Try out endpoints directly in the browser
- View request/response schemas
- See all available endpoints

### 12.2 ReDoc

Open in your browser:
```
http://localhost:8080/redoc
```

Features:
- Clean, readable documentation
- Detailed schema information
- Better for reading/sharing

### 12.3 OpenAPI JSON Schema

```bash
curl http://localhost:8080/openapi.json | python -m json.tool
```

This returns the raw OpenAPI 3.0 specification.

---

## Step 13: Run Automated Tests

### 13.1 Run All Unit Tests

```bash
pytest tests/unit/ -v
```

**Expected Output:**
```
tests/unit/test_math_ops.py::TestAddValuesInput::test_valid_integers PASSED
tests/unit/test_math_ops.py::TestAddValuesInput::test_valid_floats PASSED
tests/unit/test_tools.py::TestMultiplyValuesTool::test_multiply_positive_integers PASSED
tests/unit/test_tools.py::TestDivideValuesTool::test_divide_positive_integers PASSED
tests/unit/test_llm_provider.py::TestLLMProvider::test_ollama_value PASSED
...
============================== 105 passed in X.XXs ==============================
```

### 13.2 Run Tests with Coverage

```bash
pytest tests/unit/ --cov=src/deepthought --cov-report=term-missing
```

### 13.3 Run Specific Test File

```bash
# Test only math operations
pytest tests/unit/test_math_ops.py -v

# Test only models
pytest tests/unit/test_models.py -v

# Test only agent nodes
pytest tests/unit/test_nodes.py -v

# Test only tools (multiply, divide, verification, formatting)
pytest tests/unit/test_tools.py -v

# Test only LLM provider
pytest tests/unit/test_llm_provider.py -v
```

### 13.4 Run Tests Matching a Pattern

```bash
# Run all tests with "verification" in the name
pytest tests/unit/ -v -k "verification"

# Run all tests with "multiply" in the name
pytest tests/unit/ -v -k "multiply"

# Run all tests with "divide" in the name
pytest tests/unit/ -v -k "divide"
```

---

## Step 14: Cleanup

### 14.1 Stop the FastAPI Server

In the terminal running the server, press `Ctrl+C`.

### 14.2 Stop All Docker Services

```bash
docker compose down
```

This stops both DynamoDB and Ollama containers.

### 14.3 Remove All Data (Optional)

To completely remove all data volumes (DynamoDB data and Ollama models):
```bash
docker compose down -v
```

### 14.4 Deactivate Virtual Environment

```bash
deactivate
```

### 14.5 Full Cleanup (Optional)

To remove all generated files:
```bash
# Remove virtual environment
rm -rf .venv

# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Remove pytest cache
rm -rf .pytest_cache

# Remove coverage data
rm -rf .coverage htmlcov
```

---

## Troubleshooting

### DynamoDB Issues

#### Container Won't Start
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill the process using port 8000
kill -9 <PID>

# Restart DynamoDB
docker compose down && docker compose up -d
```

#### Cannot Connect to DynamoDB
```bash
# Verify container is running
docker ps | grep dynamodb

# Check container logs
docker logs deepthought-dynamodb

# Verify endpoint URL in .env
grep DYNAMODB_ENDPOINT_URL .env
```

#### Table Already Exists Error
```bash
# Remove and recreate the container with fresh data
docker compose down -v
docker compose up -d
python scripts/seed_data.py
```

### FastAPI Server Issues

#### Port 8080 Already in Use
```bash
# Check what's using port 8080
lsof -i :8080

# Use a different port
uvicorn src.deepthought.api.app:create_app --factory --reload --port 8081
```

#### Import Errors
```bash
# Ensure virtual environment is activated
which python  # Should show .venv/bin/python

# Reinstall the package
pip install -e ".[dev]"
```

#### Module Not Found Errors
```bash
# Verify installation
pip list | grep deepthought

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Ollama Issues

#### Ollama Container Won't Start
```bash
# Check if port 11434 is already in use
lsof -i :11434

# Kill the process using port 11434
kill -9 <PID>

# Restart services
docker compose down && docker compose up -d
```

#### Models Not Pulling
```bash
# Check Ollama logs
docker logs deepthought-ollama

# Manually pull a model
docker exec deepthought-ollama ollama pull llama3.2

# Check available models
curl http://localhost:11434/api/tags
```

#### LLM Responses Are Slow
This is expected with local Ollama models, especially on first request (model loading). Performance depends on your hardware:
- **CPU-only**: Responses may take 10-30+ seconds
- **GPU (NVIDIA/Apple Silicon)**: Much faster, 1-5 seconds

#### Ollama Out of Memory
```bash
# Try a smaller model
# Edit .env to use a smaller model:
LLM_MODEL=phi3  # Much smaller than llama3.2

# Pull the smaller model
docker exec deepthought-ollama ollama pull phi3
```

### Anthropic API Issues (If Using Anthropic)

#### API Key Not Set
```bash
# Verify the key is in .env
grep ANTHROPIC_API_KEY .env

# Ensure LLM_PROVIDER is set to anthropic
grep LLM_PROVIDER .env
```

#### Rate Limiting
If you see rate limit errors, wait a few minutes before retrying. The Anthropic API has usage limits.

#### Invalid API Key
```
Error: Invalid API key
```
Verify your API key at [console.anthropic.com](https://console.anthropic.com/).

### Test Failures

#### Tests Fail with Import Errors
```bash
# Ensure you're in the project root
pwd  # Should show /path/to/DeepThought

# Reinstall with dev dependencies
pip install -e ".[dev]"
```

#### Async Test Issues
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check pytest.ini configuration
cat pyproject.toml | grep asyncio
```

### General Tips

1. **Always activate the virtual environment** before running commands
2. **Check the server logs** in the terminal running Uvicorn for detailed error messages
3. **Use `docker logs`** to debug DynamoDB issues
4. **Verify your .env file** has no trailing whitespace or incorrect values
5. **Restart services** after making configuration changes

---

## Quick Reference

### Start Everything
```bash
# Terminal 1: Start all services (DynamoDB + Ollama)
docker compose up -d

# Terminal 1: Set up Ollama models (if using Ollama)
source .venv/bin/activate
python scripts/setup_ollama.py

# Terminal 1: Seed database
python scripts/seed_data.py

# Terminal 1: Start server
uvicorn src.deepthought.api.app:create_app --factory --reload --port 8080
```

### Quick Test Commands
```bash
# Health check
curl http://localhost:8080/health

# Add (default operation)
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{"partition_key": "CALC#test", "sort_key": "ITEM#001"}'

# Multiply
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{"partition_key": "CALC#test", "sort_key": "ITEM#001", "operation": "multiply"}'

# Divide
curl -X POST http://localhost:8080/api/v1/tasks/calculate \
  -H "Content-Type: application/json" \
  -d '{"partition_key": "CALC#test", "sort_key": "ITEM#002", "operation": "divide"}'

# Run tests
pytest tests/unit/ -v
```

### Check Service Status
```bash
# Check Docker containers
docker ps

# Check Ollama models
curl http://localhost:11434/api/tags

# Check DynamoDB
curl http://localhost:8000
```

### Stop Everything
```bash
# Ctrl+C to stop server
docker compose down
deactivate
```
