#!/bin/bash
MODEL_PATH="$1"

if [ -z "$MODEL_PATH" ]; then
    echo "Usage: validate.sh <model_path>"
    exit 1
fi

if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model file not found: $MODEL_PATH"
    exit 1
fi

MAGIC=$(head -c 4 "$MODEL_PATH")
if [ "$MAGIC" = "NCML" ]; then
    echo "Valid NCML format"
else
    echo "Invalid format"
    exit 1
fi

echo "Model validation passed: $MODEL_PATH"
exit 0
