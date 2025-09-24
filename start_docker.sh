#!/bin/bash

# Default path value
LLM_PATH="$HOME""/LLMs"
CODE_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)""/code"
BOOK_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)""/books"

echo $LLM_PATH
echo $CODE_PATH
echo $BOOK_PATH

# Use the provided argument if available; otherwise, fall back to the default value
LLM_PATH=${1:-$LLM_PATH}

# Example usage in a Docker bind mount
docker run -it --device /dev/kfd --device /dev/dri --security-opt seccomp=unconfined\
 --mount type=bind,src="$LLM_PATH",target=/llm\
 --mount type=bind,src="$CODE_PATH",target=/code,ro\
 --mount type=bind,src="$BOOK_PATH",target=/book\
 -e POSTGRES_USER=root \
 -p 5432:5432 \
 rocm_ml_suite
