# LLM Interface Usage Guide

This guide provides comprehensive instructions for using the LLM interface system for both local and API-based language models, covering single-turn prompts and multi-turn conversations.

## Table of Contents

1. [Overview](#overview)
2. [Installation and Setup](#installation-and-setup)
3. [Configuration](#configuration)
4. [Local Models (HuggingFace & vLLM)](#local-models)
5. [API Models (OpenAI, Anthropic, Google)](#api-models)
6. [Multi-turn Conversations](#multi-turn-conversations)
7. [Web Application](#web-application)
8. [Advanced Usage](#advanced-usage)
9. [Troubleshooting](#troubleshooting)

## Overview

The LLM interface system supports:

- **Local Models**: HuggingFace Transformers and vLLM backends
- **API Models**: OpenAI, Anthropic Claude, and Google Gemini
- **Single-turn**: One-shot prompt and response
- **Multi-turn**: Interactive conversations with memory
- **Web Interface**: Browser-based chat application
- **Thinking Mode**: Support for reasoning models (DeepSeek-R1, Claude, etc.)

### Supported Models

**Local Models:**
- `meta-llama/Llama-3.2-1B-Instruct`
- `meta-llama/Llama-3.2-3B-Instruct`
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` (supports thinking)
- `Qwen/Qwen2-7B-Instruct`

**API Models:**
- **OpenAI**: `gpt-5-mini-2025-08-07`, `gpt-4o-2024-11-20`
- **Anthropic**: `claude-sonnet-4-20250514`, `claude-3-7-sonnet-20250219` (both support reasoning)
- **Google**: `gemini-2.5-flash`, `gemini-2.5-pro` (both support thinking)

## Installation and Setup

### Environment Setup

1. **Create conda environment:**
```bash
conda env create -f environment.yaml
conda activate hierarchical_planning
```

2. **Set API keys (for API models):**
```bash
export OPENAI_KEY="your_openai_key"
export ANTHROPIC_KEY="your_anthropic_key"
export GOOGLE_KEY="your_google_key"
export HF_TOKEN="your_huggingface_token"  # For local models
```

3. **For multi-GPU setups (optional):**
```bash
# Configure accelerate for HuggingFace models
accelerate config
```

## Configuration

Configuration files are located in `configs/llm_interface/`:

- `local/huggingface_config.yaml` - HuggingFace models
- `local/vllm_config.yaml` - vLLM models
- `api/openai_config.yaml` - OpenAI models
- `api/anthropic_config.yaml` - Anthropic models
- `api/google_config.yaml` - Google models
- `example_config.yaml` - Example configuration

### Example Configuration Structure

```yaml
model_name: "meta-llama/Llama-3.2-1B-Instruct"
enable_thinking: false
generation_params:
  temperature: 0.7
  top_p: 1.0
  top_k: null
  max_tokens: 512
```

## Local Models

### HuggingFace Backend

#### Single-turn Generation

```bash
# Basic usage
python run_llm.py \
  --config configs/llm_interface/local/huggingface_config.yaml \
  --backend hf \
  --prompt "What are the first 5 prime numbers?"

# With custom parameters
python run_llm.py \
  --config configs/llm_interface/local/huggingface_config.yaml \
  --backend hf \
  --prompt "Explain quantum computing" \
  --temperature 0.8 \
  --max_tokens 256

# With system prompt
python run_llm.py \
  --config configs/llm_interface/local/huggingface_config.yaml \
  --backend hf \
  --prompt "What is machine learning?" \
  --system_prompt "You are a helpful AI assistant specializing in computer science."

# Using accelerate for multi-GPU
accelerate launch run_llm.py \
  --config configs/llm_interface/local/huggingface_config.yaml \
  --backend hf \
  --prompt "Explain neural networks"
```

#### Multi-turn Conversation

```bash
# Interactive multi-turn chat
python run_llm.py \
  --config configs/llm_interface/local/huggingface_config.yaml \
  --backend hf \
  --multi_turn

# Multi-turn with system prompt
python run_llm.py \
  --config configs/llm_interface/local/huggingface_config.yaml \
  --backend hf \
  --multi_turn \
  --system_prompt "You are a helpful coding assistant."

# Multi-turn with accelerate
accelerate launch run_llm.py \
  --config configs/llm_interface/local/huggingface_config.yaml \
  --backend hf \
  --multi_turn
```

### vLLM Backend

The vLLM backend uses the [LLM.chat API](https://docs.vllm.ai/en/stable/api/vllm/index.html#vllm.LLM.chat) for multi-turn conversations and supports [automatic prefix caching](https://docs.vllm.ai/en/stable/features/automatic_prefix_caching.html) for improved performance.

#### Single-turn Generation

```bash
# Basic usage
python run_llm.py \
  --config configs/llm_interface/local/vllm_config.yaml \
  --backend vllm \
  --prompt "What are the first 5 prime numbers?"

# With custom parameters
python run_llm.py \
  --config configs/llm_interface/local/vllm_config.yaml \
  --backend vllm \
  --prompt "Explain quantum computing" \
  --temperature 0.8 \
  --max_tokens 256 \
  --top_p 0.9
```

#### Multi-turn Conversation

```bash
# Interactive multi-turn chat (uses vLLM.chat API)
python run_llm.py \
  --config configs/llm_interface/local/vllm_config.yaml \
  --backend vllm \
  --multi_turn

# Multi-turn with system prompt
python run_llm.py \
  --config configs/llm_interface/local/vllm_config.yaml \
  --backend vllm \
  --multi_turn \
  --system_prompt "You are a helpful coding assistant."
```

## API Models

### OpenAI

#### Single-turn Generation

```bash
# Basic usage
python run_llm.py \
  --config configs/llm_interface/api/openai_config.yaml \
  --backend openai \
  --prompt "What are the first 5 prime numbers?"

# With reasoning model
python run_llm.py \
  --config configs/llm_interface/api/openai_config.yaml \
  --backend openai \
  --prompt "Solve this step by step: What is 15% of 240?" \
  --enable_thinking true

# With custom parameters
python run_llm.py \
  --config configs/llm_interface/api/openai_config.yaml \
  --backend openai \
  --prompt "Write a Python function to calculate fibonacci numbers" \
  --temperature 0.3 \
  --max_tokens 500
```

#### Multi-turn Conversation

```bash
# Interactive multi-turn chat
python run_llm.py \
  --config configs/llm_interface/api/openai_config.yaml \
  --backend openai \
  --multi_turn

# Multi-turn with system prompt
python run_llm.py \
  --config configs/llm_interface/api/openai_config.yaml \
  --backend openai \
  --multi_turn \
  --system_prompt "You are a helpful coding assistant."
```

### Anthropic Claude

#### Single-turn Generation

```bash
# Basic usage
python run_llm.py \
  --config configs/llm_interface/api/anthropic_config.yaml \
  --backend anthropic \
  --prompt "What are the first 5 prime numbers?"

# With reasoning
python run_llm.py \
  --config configs/llm_interface/api/anthropic_config.yaml \
  --backend anthropic \
  --prompt "Analyze the pros and cons of renewable energy" \
  --enable_thinking true

# With system prompt
python run_llm.py \
  --config configs/llm_interface/api/anthropic_config.yaml \
  --backend anthropic \
  --prompt "Explain machine learning" \
  --system_prompt "You are Claude, an AI assistant created by Anthropic."
```

#### Multi-turn Conversation

```bash
# Interactive multi-turn chat
python run_llm.py \
  --config configs/llm_interface/api/anthropic_config.yaml \
  --backend anthropic \
  --multi_turn

# Multi-turn with reasoning
python run_llm.py \
  --config configs/llm_interface/api/anthropic_config.yaml \
  --backend anthropic \
  --multi_turn \
  --enable_thinking true
```

### Google Gemini

#### Single-turn Generation

```bash
# Basic usage
python run_llm.py \
  --config configs/llm_interface/api/google_config.yaml \
  --backend google \
  --prompt "What are the first 5 prime numbers?"

# With thinking (dynamic budget)
python run_llm.py \
  --config configs/llm_interface/api/google_config.yaml \
  --backend google \
  --prompt "Solve this complex problem step by step: optimize a supply chain" \
  --enable_thinking true

# With custom thinking budget
python run_llm.py \
  --config configs/llm_interface/api/google_config.yaml \
  --backend google \
  --prompt "Analyze this data and provide insights" \
  --enable_thinking true \
  --thinking_budget 4000
```

#### Multi-turn Conversation

```bash
# Interactive multi-turn chat
python run_llm.py \
  --config configs/llm_interface/api/google_config.yaml \
  --backend google \
  --multi_turn

# Multi-turn with thinking
python run_llm.py \
  --config configs/llm_interface/api/google_config.yaml \
  --backend google \
  --multi_turn \
  --enable_thinking true
```

## Multi-turn Conversations

### Conversation Management

The system uses proper conversation formats based on the [HuggingFace chat documentation](https://huggingface.co/docs/transformers/en/conversations):

- **Local Models**: Use HuggingFace messages format with chat templates
- **vLLM**: Uses [LLM.chat API](https://docs.vllm.ai/en/stable/api/vllm/index.html#vllm.LLM.chat) for optimal multi-turn performance
- **OpenAI**: Native messages format
- **Anthropic**: Separate system prompt handling
- **Google**: Formatted conversation context

### Interactive Commands

During multi-turn conversations, you can use:

- `quit` or `exit` - End the conversation
- `clear` - Clear conversation history
- Regular messages - Continue the conversation

### Example Multi-turn Session

```bash
python run_llm.py --config configs/llm_interface/example_config.yaml --backend hf --multi_turn

# Session example:
User: Hello, I'm learning Python. Can you help me?
Assistant: Of course! I'd be happy to help you learn Python...

User: What's the difference between lists and tuples?
Assistant: Great question! Lists and tuples are both sequence types in Python...

User: clear
# Conversation history cleared

User: quit
# Session ends
```

## Web Application

### Launching the Web Interface

```bash
# HuggingFace backend
python run_llm.py \
  --config configs/llm_interface/local/huggingface_config.yaml \
  --backend hf \
  --open_browser

# vLLM backend
python run_llm.py \
  --config configs/llm_interface/local/vllm_config.yaml \
  --backend vllm \
  --open_browser

# OpenAI backend
python run_llm.py \
  --config configs/llm_interface/api/openai_config.yaml \
  --backend openai \
  --open_browser

# Anthropic backend
python run_llm.py \
  --config configs/llm_interface/api/anthropic_config.yaml \
  --backend anthropic \
  --open_browser

# Google backend
python run_llm.py \
  --config configs/llm_interface/api/google_config.yaml \
  --backend google \
  --open_browser
```

### Web Interface Features

- **Real-time Chat**: Interactive conversation interface
- **Parameter Control**: Adjust temperature, max_tokens, etc. in real-time
- **Model Information**: Display current model and configuration
- **Conversation Management**: Clear history, persistent sessions
- **Multi-backend Support**: Works with all local and API backends

### Accessing the Web Interface

After launching, open your browser and navigate to:
```
http://localhost:5000
```

## Advanced Usage

### Custom Output Directory

```bash
python run_llm.py \
  --config configs/llm_interface/example_config.yaml \
  --backend hf \
  --prompt "Test prompt" \
  --output_dir ./my_results/
```

### Seed for Reproducibility

```bash
python run_llm.py \
  --config configs/llm_interface/example_config.yaml \
  --backend hf \
  --prompt "Generate a random story" \
  --seed 42
```

### Thinking Mode Examples

```bash
# DeepSeek-R1 with thinking
python run_llm.py \
  --config configs/llm_interface/local/deepseek_config.yaml \
  --backend hf \
  --prompt "Solve: If a train travels 60 mph for 2.5 hours, how far does it go?" \
  --enable_thinking true

# Claude with reasoning
python run_llm.py \
  --config configs/llm_interface/api/anthropic_config.yaml \
  --backend anthropic \
  --prompt "Analyze the economic impact of AI on employment" \
  --enable_thinking true

# Gemini with custom thinking budget
python run_llm.py \
  --config configs/llm_interface/api/google_config.yaml \
  --backend google \
  --prompt "Design a sustainable city planning strategy" \
  --enable_thinking true \
  --thinking_budget 8000
```

### Multi-GPU Usage

```bash
# Configure accelerate first
accelerate config

# Use with HuggingFace models
accelerate launch run_llm.py \
  --config configs/llm_interface/local/huggingface_config.yaml \
  --backend hf \
  --prompt "Large model inference test"

# vLLM automatically handles multi-GPU via tensor_parallel_size in config
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Install missing dependencies
   pip install vllm omegaconf flask
   ```

2. **CUDA Out of Memory**
   ```bash
   # Reduce model size or use quantization
   # Edit config file to set smaller max_model_len
   ```

3. **API Key Issues**
   ```bash
   # Verify environment variables
   echo $OPENAI_KEY
   echo $ANTHROPIC_KEY
   echo $GOOGLE_KEY
   echo $HF_TOKEN
   ```

4. **vLLM Initialization Issues**
   ```bash
   # Check GPU memory and reduce gpu_memory_utilization in config
   # Ensure CUDA is properly installed
   ```

5. **Web Application Not Loading**
   ```bash
   # Check if port 5000 is available
   # Try accessing http://127.0.0.1:5000 instead
   ```

### Performance Tips

1. **For Local Models**:
   - Use vLLM for better performance with multi-turn conversations
   - Enable tensor parallelism for large models
   - Use appropriate quantization for memory constraints

2. **For API Models**:
   - Set appropriate rate limits
   - Use thinking mode judiciously (costs more tokens)
   - Cache responses when possible

3. **For Multi-turn Conversations**:
   - vLLM automatically uses prefix caching for efficiency
   - HuggingFace models benefit from shorter context windows
   - Clear conversation history periodically for long sessions

### Debugging

Enable debug logging:
```bash
export PYTHONPATH=/path/to/project
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
python run_llm.py --config ... --backend ... --prompt "test"
```

## Configuration Reference

### Generation Parameters

- `temperature`: Controls randomness (0.0 = deterministic, 1.0 = very random)
- `top_p`: Nucleus sampling threshold (0.0 to 1.0)
- `top_k`: Top-k sampling (integer or null to disable)
- `max_tokens`: Maximum tokens to generate
- `seed`: Random seed for reproducibility

### Model-Specific Parameters

**vLLM**:
- `tensor_parallel_size`: Number of GPUs for tensor parallelism
- `gpu_memory_utilization`: Fraction of GPU memory to use (0.0 to 1.0)
- `max_model_len`: Maximum sequence length

**Google Gemini**:
- `thinking_budget`: Thinking tokens budget (-1 for dynamic, 0 to disable, positive integer for fixed)

### Backend Selection

- `hf`: HuggingFace Transformers
- `vllm`: vLLM engine
- `openai`: OpenAI API
- `anthropic`: Anthropic API
- `google`: Google Gemini API

## Examples Repository

All example commands and configurations are available in the project repository. Test your setup with:

```bash
# Quick test
python run_llm.py --config configs/llm_interface/example_config.yaml --backend hf --prompt "Hello, world!"

# Multi-turn test
python run_llm.py --config configs/llm_interface/example_config.yaml --backend hf --multi_turn

# Web interface test
python run_llm.py --config configs/llm_interface/example_config.yaml --backend hf --open_browser
```

For more examples and advanced usage patterns, refer to the test scripts and configuration files in the project repository.
