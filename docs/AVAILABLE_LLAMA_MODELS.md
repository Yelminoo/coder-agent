# Available Llama Models for Ollama

## Currently Installed
You have **2 models** installed:
1. **llama3.2:latest** (2.0 GB) - Active chat model
2. **nomic-embed-text:latest** (274 MB) - Embedding model (not for chat)

## Popular Llama Models You Can Download

### Llama 3.2 Series (Meta)
- **llama3.2:1b** (~1.3 GB) - Fastest, smallest, good for testing
- **llama3.2:3b** (~2.0 GB) - **Currently installed** - Balanced speed/quality
- **llama3.2:latest** (~2.0 GB) - Alias for 3b version

### Llama 3.1 Series (Meta)
- **llama3.1:8b** (~4.7 GB) - High quality, larger model
- **llama3.1:70b** (~40 GB) - Very high quality, requires powerful GPU
- **llama3.1:405b** (~231 GB) - SOTA quality, enterprise-level

### Llama 3 Series (Meta)
- **llama3:8b** (~4.7 GB) - Previous generation 8B
- **llama3:70b** (~40 GB) - Previous generation 70B

### Specialized Variants

#### Code-Focused
- **codellama:7b** (~3.8 GB) - Optimized for code generation
- **codellama:13b** (~7.4 GB) - Better code quality
- **codellama:34b** (~19 GB) - Professional code generation

#### Uncensored/Creative
- **llama2-uncensored:7b** (~3.8 GB) - Less restricted responses
- **llama3-groq-tool-use:8b** (~4.7 GB) - Function calling support

#### Multilingual
- **llama3:8b-instruct-q8_0** (~8.5 GB) - Better multilingual support

## How to Download Models

### Method 1: Command Line (Recommended)
```bash
# Download a specific model
ollama pull llama3.1:8b

# Download latest version
ollama pull llama3.2

# Download Code Llama
ollama pull codellama:7b
```

### Method 2: Via Chat Interface
Just switch to the model in the dropdown (if not downloaded, Ollama will auto-pull it on first use).

## Model Comparison

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| llama3.2:1b | 1.3GB | ⚡⚡⚡⚡⚡ | ⭐⭐ | Testing, low-resource |
| llama3.2:3b | 2.0GB | ⚡⚡⚡⚡ | ⭐⭐⭐ | General use, current |
| llama3.1:8b | 4.7GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | Better responses |
| codellama:7b | 3.8GB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Code generation |
| llama3.1:70b | 40GB | ⚡ | ⭐⭐⭐⭐⭐ | Best quality |

## System Requirements

### Minimum
- **1B-3B models**: 8GB RAM, No GPU required
- **7B-8B models**: 16GB RAM, GPU recommended

### Recommended
- **8B models**: 16GB RAM + 6GB VRAM
- **13B models**: 32GB RAM + 8GB VRAM
- **70B models**: 64GB RAM + 24GB VRAM

## Quick Commands

```bash
# List installed models
ollama list

# Remove a model
ollama rm llama3:8b

# View model info
ollama show llama3.2

# Run model directly (CLI)
ollama run llama3.2
```

## Recommendations

### For Your Current Setup
Based on your 2GB model working well:
1. Try **llama3.1:8b** (4.7GB) - Better quality, still fast
2. Try **codellama:7b** (3.8GB) - If you do lots of coding

### Best Balanced Model
- **llama3.1:8b** - Best balance of speed, quality, and size

### For Speed
- Stick with **llama3.2:3b** (current) - Fastest response times

### For Code
- **codellama:7b** - Specifically trained on code

## Model Switching

Your new dropdown lets you switch models instantly without restarting:
1. Select model from dropdown next to "UI Mode"
2. Model switches immediately
3. Next chat uses new model

**Note**: First use of a new model will auto-download it (may take a few minutes).
