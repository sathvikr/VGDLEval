# LLM Interface Documentation

This document provides documentation for the LLM interface system that supports both local and API-based models with thinking/reasoning capabilities.

## Overview

The LLM interface system provides a unified API for interacting with various language models:

### Local Models (via HuggingFace and vLLM)
- **meta-llama/Llama-3.2-1B-Instruct**
- **meta-llama/Llama-3.2-3B-Instruct** 
- **deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B** (supports thinking with `<think>` tags)
- **Qwen/Qwen2-7B-Instruct**

### API Models
- **OpenAI**: gpt-5-mini-2025-08-07, gpt-4o-2024-11-20 (both support reasoning)
- **Anthropic**: claude-sonnet-4-20250514, claude-3-7-sonnet-20250219 (both support reasoning)
- **Google**: gemini-2.5-flash, gemini-2.5-pro (both support thinking)

## Installation

1. Install the conda environment:
```bash
conda env create -f environment.yaml
conda activate hierarchical_planning
```

2. Set up API keys (for API models):
```bash
export HF_TOKEN="your_huggingface_token"
export OPENAI_KEY="your_openai_api_key"
export ANTHROPIC_KEY="your_anthropic_api_key"
export GOOGLE_KEY="your_google_api_key"
```

## Usage

### Basic Usage

```bash
# HuggingFace local model
python run_llm.py --config configs/llm_interface/local/huggingface_config.yaml --backend hf --prompt "Write the first 5 prime numbers"

# vLLM local model
python run_llm.py --config configs/llm_interface/local/vllm_config.yaml --backend vllm --prompt "Write the first 5 prime numbers"

# OpenAI API
python run_llm.py --config configs/llm_interface/api/openai_config.yaml --backend openai --prompt "Write the first 5 prime numbers"
```

### With Accelerate (for multi-GPU)

```bash
accelerate launch --config_file accelerate_config.yaml run_llm.py --config configs/llm_interface/local/huggingface_config.yaml --backend hf --prompt "Write the first 5 prime numbers"
```

### Advanced Usage

```bash
# With custom parameters
python run_llm.py \
  --config configs/llm_interface/local/huggingface_config.yaml \
  --backend hf \
  --prompt "Write the first 5 prime numbers" \
  --temperature 0.8 \
  --max_tokens 256 \
  --enable_thinking

# Using specific model configuration
python run_llm.py \
  --config configs/llm_interface/example_config.yaml \
  --backend hf \
  --model_config deepseek_thinking \
  --prompt "Explain quantum computing"

# With system prompt
python run_llm.py \
  --config configs/llm_interface/api/openai_config.yaml \
  --backend openai \
  --prompt "Write the first 5 prime numbers" \
  --system_prompt "You are a helpful math tutor"
```

## Configuration Files

### Local Model Configurations

#### HuggingFace Configuration (`configs/llm_interface/local/huggingface_config.yaml`)
```yaml
model_name: "meta-llama/Llama-3.2-1B-Instruct"
device: "auto"
enable_thinking: false
load_in_8bit: false
load_in_4bit: false
torch_dtype: "float16"

generation:
  temperature: 0.7
  top_p: 0.9
  max_tokens: 512
```

#### vLLM Configuration (`configs/llm_interface/local/vllm_config.yaml`)
```yaml
model_name: "meta-llama/Llama-3.2-1B-Instruct"
enable_thinking: false
tensor_parallel_size: 1
gpu_memory_utilization: 0.9
enforce_eager: true

generation:
  temperature: 0.7
  top_p: 0.9
  max_tokens: 512
```

### API Model Configurations

#### OpenAI Configuration (`configs/llm_interface/api/openai_config.yaml`)
```yaml
model_name: "gpt-5-mini-2025-08-07"
enable_thinking: false

generation:
  temperature: 1.0
  top_p: 1.0
  max_tokens: 512
```

## Programming Interface

### Local Models

```python
from llm_interface import HuggingFaceInterface, vLLMInterface

# HuggingFace interface
hf_interface = HuggingFaceInterface(
    model_name="meta-llama/Llama-3.2-1B-Instruct",
    device="auto",
    enable_thinking=False
)

result = hf_interface.generate(
    prompt="Write the first 5 prime numbers",
    temperature=0.7,
    max_tokens=512
)

# vLLM interface
vllm_interface = vLLMInterface(
    model_name="meta-llama/Llama-3.2-1B-Instruct",
    tensor_parallel_size=1,
    enable_thinking=False
)

result = vllm_interface.generate(
    prompt="Write the first 5 prime numbers",
    temperature=0.7,
    max_tokens=512
)
```

### API Models

```python
from llm_interface import OpenAIInterface, AnthropicInterface, GoogleInterface

# OpenAI interface
openai_interface = OpenAIInterface(
    model_name="gpt-5-mini-2025-08-07",
    enable_thinking=True  # Enable reasoning
)

result = openai_interface.generate(
    prompt="Write the first 5 prime numbers",
    temperature=0.8,
    max_tokens=512
)

# Anthropic interface
anthropic_interface = AnthropicInterface(
    model_name="claude-sonnet-4-20250514",
    enable_thinking=True
)

# Google interface
google_interface = GoogleInterface(
    model_name="gemini-2.5-flash",
    enable_thinking=True
)
```

## Output Format

All interfaces return a standardized dictionary with the following structure:

```python
{
    'input_text': str,                    # Original prompt
    'system_prompt': str,                 # System prompt (if provided)
    'chat_template_applied': str,         # Template used
    'formatted_prompt': str,              # Final formatted prompt
    'output': str,                        # Generated text
    'model_config': dict,                 # Model configuration
    'generation_params': dict,            # Generation parameters used
    'token_usage': {                      # Token usage statistics
        'input_tokens': int,
        'output_tokens': int,
        'reasoning_tokens': int,          # If thinking/reasoning enabled
        'total_tokens': int
    },
    'generation_time_seconds': float,     # Generation time
    'tokens_per_second': float,           # Generation speed
    'timestamp': str,                     # ISO timestamp
    'reasoning': str                      # Reasoning text (if available)
}
```

## Thinking/Reasoning Support

### Models with Thinking Support

1. **DeepSeek-R1-Distill-Qwen-1.5B**: Uses `<think>` tags
2. **OpenAI GPT models**: Uses reasoning API
3. **Anthropic Claude models**: Built-in reasoning
4. **Google Gemini models**: Configurable thinking budget

### Enabling Thinking

```bash
# Command line
python run_llm.py --config config.yaml --backend hf --prompt "Solve this problem" --enable_thinking

# Programmatically
interface = HuggingFaceInterface(model_name="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B", enable_thinking=True)
```

## Multi-GPU Support

### Using Accelerate

1. Configure accelerate:
```bash
accelerate config  # Interactive configuration
# Or use the provided accelerate_config.yaml
```

2. Launch with accelerate:
```bash
accelerate launch --config_file accelerate_config.yaml run_llm.py --config config.yaml --backend hf --prompt "Your prompt"
```

### vLLM Multi-GPU

```yaml
# In vllm_config.yaml
tensor_parallel_size: 4  # Use 4 GPUs
gpu_memory_utilization: 0.8
```

## Output Storage

Results are automatically saved as pickle files in the specified output directory:

```bash
python run_llm.py --config config.yaml --backend hf --prompt "Test" --output_dir ./my_results/
```

Files are named: `{backend}_{model_name}_{timestamp}.pkl`

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**:
   - Reduce `gpu_memory_utilization` in vLLM config
   - Enable quantization (`load_in_4bit: true`) for HuggingFace
   - Use smaller models or fewer GPUs

2. **API Key Issues**:
   - Ensure environment variables are set correctly
   - Check API key permissions and quotas

3. **Model Loading Issues**:
   - Verify HuggingFace token has access to gated models
   - Check internet connection for model downloads
   - Ensure sufficient disk space

### Performance Tips

1. **For Local Models**:
   - Use vLLM for better throughput
   - Enable tensor parallelism for large models
   - Use mixed precision (fp16/bf16)

2. **For API Models**:
   - Implement rate limiting for high-volume usage
   - Cache responses when appropriate
   - Use batch processing when available

## Examples

### Test with Prime Numbers

```bash
python run_llm.py --config configs/llm_interface/local/huggingface_config.yaml --backend hf --prompt "Write the first 5 prime numbers"
```

Expected output:
```
The first 5 prime numbers are:
1. 2
2. 3
3. 5
4. 7
5. 11
```

### Test with Thinking

```bash
python run_llm.py --config configs/llm_interface/local/huggingface_config.yaml --backend hf --model_config deepseek_thinking --prompt "Explain why 17 is prime"
```

This will show both the reasoning process and the final answer.
