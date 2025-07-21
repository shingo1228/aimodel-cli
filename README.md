# AI Model CLI

A standalone command-line interface for downloading and managing AI models from CivitAI.

## Features

- 🔍 **Search Models**: Search CivitAI with filters for content type, base model, and more
- 📥 **Fast Downloads**: High-speed HTTP downloads with resume support
- 📋 **Model Information**: View detailed model information and metadata
- ⚙️ **Configuration**: Easy configuration management with interactive setup
- 🏷️ **Metadata Management**: Automatic model metadata and preview image saving
- 🔄 **Metadata Completion**: Complete missing metadata for existing model files using SHA256 hash identification
- 📂 **Smart Organization**: Model-type-specific download paths (Stable-diffusion, Lora, embeddings, etc.)
- 🔐 **API Key Support**: Support for personal API keys to download restricted models
- 🆕 **Update Checking**: Check for model updates with version comparison
- 📊 **Markdown Reports**: Generate detailed reports with preview images and CivitAI links

## Installation

### From GitHub

```bash
git clone https://github.com/shingo1228/aimodel-cli.git
cd aimodel-cli
pip install -e .
```

### From PyPI (Coming Soon)

```bash
pip install aimodel-cli
```

### Requirements

- Python 3.8+
- Internet connection
- Optional: Personal CivitAI API key for restricted downloads

## Quick Start

1. **Initial Setup**
   ```bash
   aimodel setup
   ```

2. **Search for Models**
   ```bash
   aimodel search "realistic portrait"
   aimodel search --type LORA --base-model "SD 1.5"
   ```

3. **Download a Model**
   ```bash
   aimodel download 123456
   aimodel download 123456 --version 234567
   ```

4. **View Model Information**
   ```bash
   aimodel info 123456
   aimodel info ./model.safetensors --local
   ```

5. **Complete Missing Metadata**
   ```bash
   aimodel metadata complete /path/to/models --recursive
   aimodel metadata complete --model-type LORA
   ```

6. **Check for Updates**
   ```bash
   aimodel update check --model-type LORA --report updates.md
   ```

## Commands

### Search

Search for models on CivitAI:

```bash
aimodel search [QUERY] [OPTIONS]
```

**Options:**
- `--type`: Filter by content type (Checkpoint, LORA, etc.)
- `--base-model`: Filter by base model (SD 1.5, SDXL, etc.)
- `--sort`: Sort order (Most Downloaded, Newest, etc.)
- `--period`: Time period (All Time, Month, Week, Day)
- `--nsfw`: Include NSFW content
- `--limit`: Number of results (default: 20)
- `--page`: Page number

**Examples:**
```bash
aimodel search "anime style"
aimodel search --type LORA --sort "Most Liked" --limit 10
aimodel search --base-model "SDXL 1.0" --nsfw
```

### Download

Download models from CivitAI:

```bash
aimodel download MODEL_ID [OPTIONS]
```

**Options:**
- `--version`: Specific version ID to download
- `--file`: Specific file ID to download
- `--path`: Custom download directory
- `--show-versions`: Show available versions
- `--show-files`: Show available files

**Examples:**
```bash
aimodel download 123456
aimodel download 123456 --version 234567
aimodel download 123456 --path ./my-models
aimodel download 123456 --show-versions
```

You can also download from URLs:
```bash
aimodel download-url "https://civitai.com/models/123456"
```

### Model Information

View detailed information about models:

```bash
aimodel info TARGET [OPTIONS]
```

**Options:**
- `--local`: Treat target as local file path

**Examples:**
```bash
aimodel info 123456
aimodel info "https://civitai.com/models/123456"
aimodel info ./model.safetensors --local
```

### Metadata Management

Complete missing metadata and preview files for existing models:

```bash
aimodel metadata complete [PATH] [OPTIONS]
```

**Options:**
- `--model-type, -t`: Process specific model type path (Checkpoint, LORA, etc.)
- `--recursive, -r / --no-recursive`: Process files recursively
- `--force, -f`: Overwrite existing metadata files
- `--metadata-only`: Only download metadata, skip preview images
- `--preview-only`: Only download preview images, skip metadata

**Examples:**
```bash
# Process all TextualInversion models
aimodel metadata complete --model-type TextualInversion

# Process specific directory recursively
aimodel metadata complete /path/to/models --recursive

# Only update missing metadata files
aimodel metadata complete /path/to/models --metadata-only

# Force update all files
aimodel metadata complete --model-type LORA --force
```

**Calculate SHA256 hash:**
```bash
aimodel metadata hash /path/to/model.safetensors
```

### Update Checking

Check for model updates and generate reports:

```bash
aimodel update check [PATH] [OPTIONS]
```

**Options:**
- `--model-type, -t`: Check specific model type path (Checkpoint, LORA, etc.)
- `--recursive, -r / --no-recursive`: Process files recursively
- `--download, -d`: Automatically download available updates
- `--show-all`: Show all models, including those without updates
- `--report PATH`: Generate Markdown report file with preview images
- `--report-include-current`: Include up-to-date models in report

**Examples:**
```bash
# Check LORA models for updates
aimodel update check --model-type LORA

# Check with automatic download
aimodel update check --model-type Checkpoint --download

# Generate detailed report
aimodel update check --model-type LORA --report lora_updates.md --show-all

# Check specific directory
aimodel update check /path/to/models --recursive --report updates.md
```

**Download specific updates:**
```bash
aimodel update download /path/to/model.safetensors --version latest
```

### Configuration

Manage CLI configuration:

```bash
aimodel config COMMAND [OPTIONS]
```

**Commands:**
- `list`: Show all configuration settings
- `get KEY`: Get specific setting value
- `set KEY VALUE`: Set configuration value
- `reset`: Reset to defaults
- `path`: Show configuration file location
- `api-key [KEY]`: Set or show API key
- `download-path [PATH]`: Set or show default download path
- `model-paths`: List model-type-specific download paths
- `model-path TYPE [PATH]`: Set or show path for specific model type
- `metadata-recursive [true|false]`: Set default recursive behavior for metadata commands

**Examples:**
```bash
aimodel config list
aimodel config api-key
aimodel config set timeout 120
aimodel config download-path ./models

# Model-type-specific paths
aimodel config model-paths
aimodel config model-path LORA /path/to/lora/models
aimodel config model-path Checkpoint  # Show current path

# Metadata command defaults
aimodel config metadata-recursive true  # Enable recursive by default
```

## Model-Type-Specific Organization

The CLI automatically organizes downloads into folders based on model type:

- **Checkpoint** → `Stable-diffusion/` folder
- **LORA** → `Lora/` folder
- **TextualInversion** → `embeddings/` folder
- **Upscaler** → `ESRGAN/` folder
- **Controlnet** → `ControlNet/` folder
- Other types use their original names

You can customize these paths:
```bash
aimodel config model-path LORA /custom/lora/path
aimodel config model-path Checkpoint /custom/checkpoint/path
```

## Configuration

The CLI stores configuration in `~/.aimodel-cli/config.json`. Key settings include:

- `api_key`: Your CivitAI API key
- `default_download_path`: Default directory for downloads
- `model_paths`: Model-type-specific download paths
- `metadata_recursive_default`: Default recursive behavior for metadata commands
- `timeout`: Request timeout in seconds
- `show_nsfw`: Include NSFW content by default
- `save_metadata`: Save model metadata to JSON files
- `save_preview`: Save preview images

## API Key

To download some models (especially early access or restricted content), you need a personal CivitAI API key:

1. Go to https://civitai.com/user/account
2. Generate an API key
3. Configure it with: `aimodel config api-key YOUR_KEY`

## Download Behavior

- Models are automatically saved to model-type-specific folders
- Metadata is saved in JSON files alongside model files
- Preview images are automatically downloaded
- SHA256 hashes are calculated and stored
- Downloads can be resumed if interrupted
- HTTP downloads with optimized performance

## Metadata Completion

The CLI can analyze existing model files and fetch missing metadata from CivitAI:

1. **By Model Type**: Process all models of a specific type
   ```bash
   aimodel metadata complete --model-type LORA
   ```

2. **By Directory**: Process all models in a directory
   ```bash
   aimodel metadata complete /path/to/models --recursive
   ```

3. **Individual Files**: Process a single model file
   ```bash
   aimodel metadata complete /path/to/model.safetensors
   ```

The tool uses SHA256 hashes to identify models on CivitAI and downloads:
- Model metadata (name, description, tags, etc.)
- Preview images
- Version information

## Update Checking

The CLI can check for model updates by comparing your local models with the latest versions on CivitAI:

- **Version Detection**: Uses SHA256 hashes to identify your local models
- **Update Detection**: Compares local version with latest available version
- **Batch Processing**: Can check entire directories or specific model types
- **Rich Reports**: Generate Markdown reports with preview images and direct CivitAI links
- **Automatic Downloads**: Optionally download updates automatically

## Markdown Reports

Generated reports include:
- **Model Information**: Name, ID, current/latest versions
- **Preview Images**: Resized images (256px width) for better readability
- **Direct Links**: Clickable links to CivitAI model pages and specific versions
- **Technical Details**: File sizes, formats, download counts
- **Summary Statistics**: Total checked, updates available, up-to-date models

## File Structure

Downloaded models create these files:
- `model.safetensors` - The model file
- `model.json` - Metadata (tags, description, etc.)
- `model.preview.png` - Preview image

## Troubleshooting

### Download Issues
- Check your internet connection
- Verify API key if downloading restricted content
- Try again later if CivitAI servers are busy

### Metadata Completion Issues
- Ensure model files are valid (not corrupted)
- Check if the model exists on CivitAI
- Verify SHA256 hash calculation is working

### Update Check Issues
- Ensure models have metadata files (run `metadata complete` first)
- Check internet connection to CivitAI API
- Verify models exist on CivitAI platform

### Permission Errors
- Ensure download directory is writable
- Run with appropriate permissions

### Configuration Issues
- Check configuration with: `aimodel config list`
- Reset if needed: `aimodel config reset`
- View config location: `aimodel config path`

## Migration from civitai-cli

If you previously used `civitai-cli`, you can manually copy your configuration:

```bash
# Copy old config to new location (if needed)
cp -r ~/.civitai-cli/* ~/.aimodel-cli/
```

Then update any custom paths:
```bash
aimodel config list
aimodel config download-path /your/custom/path
```

## Acknowledgments

This project was inspired by [sd-civitai-browser-plus](https://github.com/BlafKing/sd-civitai-browser-plus) by BlafKing. While this CLI tool takes a completely different approach (standalone CLI vs SD-WebUI extension), we appreciate the original project's contribution to the AI model management community.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Setup

```bash
git clone https://github.com/shingo1228/aimodel-cli.git
cd aimodel-cli
pip install -r requirements-dev.txt
pip install -e .
```

### Running Tests

```bash
# Coming soon
pytest
```

## Disclaimer

This is an unofficial tool and is not affiliated with CivitAI. Please respect CivitAI's terms of service and rate limits when using this tool.