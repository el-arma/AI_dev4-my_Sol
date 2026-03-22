# Batch API in OpenAI
# NOT TESTED YET!

import json
from openai import OpenAI

client = OpenAI()

# ---------------------------------------
# 1. Create JSONL file with batch requests
# ---------------------------------------

requests = [
    {
        "custom_id": "req-1",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You summarize reports."},
                {"role": "user", "content": "Summarize the quarterly sales report."}
            ]
        }
    },
    {
        "custom_id": "req-2",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": "Explain reinforcement learning in simple terms."}
            ]
        }
    }
]

with open("batch_requests.jsonl", "w") as f:
    for r in requests:
        f.write(json.dumps(r) + "\n")

# ---------------------------------------
# 2. Upload batch file
# ---------------------------------------

batch_file = client.files.create(
    file=open("batch_requests.jsonl", "rb"),
    purpose="batch"
)

# ---------------------------------------
# 3. Create batch job
# ---------------------------------------

batch = client.batches.create(
    input_file_id=batch_file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

print("Batch ID:", batch.id)

# ---------------------------------------
# 4. Check batch status
# ---------------------------------------

batch_status = client.batches.retrieve(batch.id)
print("Status:", batch_status.status)

# ---------------------------------------
# 5. When completed → download results
# ---------------------------------------

if batch_status.status == "completed":
    output_file_id = batch_status.output_file_id

    result = client.files.content(output_file_id)

    with open("batch_results.jsonl", "wb") as f:
        f.write(result.content)

    print("Results saved to batch_results.jsonl")