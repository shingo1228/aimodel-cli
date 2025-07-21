# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-20

### Added

#### Core Features
- **Model Search**: Search CivitAI with advanced filters (type, base model, sort, period)
- **Model Download**: Download models by ID, version, or URL with resume support
- **Model Information**: Display detailed model information from CivitAI or local files
- **Configuration Management**: Comprehensive CLI configuration with interactive setup
- **Metadata Management**: Automatic metadata and preview image handling

#### Advanced Features
- **SHA256-based Model Identification**: Identify existing models using hash comparison
- **Metadata Completion**: Complete missing metadata for existing model files
- **Model-Type-Specific Organization**: Automatic folder organization (Checkpoint → Stable-diffusion, LORA → Lora, etc.)
- **Update Checking**: Check for model updates with version comparison
- **Markdown Reports**: Generate detailed update reports with preview images and CivitAI links
- **API Key Support**: Support for personal CivitAI API keys for restricted downloads

#### Technical Features
- **HTTP Downloads**: Optimized HTTP downloads with resume support (no external dependencies)
- **Rich Console Output**: Beautiful CLI interface with progress bars and tables
- **Cross-Platform**: Windows, Linux, and macOS support
- **Configuration System**: JSON-based configuration with per-model-type paths
- **Error Handling**: Comprehensive error handling with helpful messages
- **Windows Compatibility**: Proper Unicode handling for Windows console

#### CLI Commands
- `aimodel search` - Search for models with filters
- `aimodel download` - Download models by ID or version
- `aimodel download-url` - Download models from CivitAI URLs
- `aimodel info` - Show model information
- `aimodel metadata complete` - Complete missing metadata
- `aimodel metadata hash` - Calculate SHA256 hashes
- `aimodel update check` - Check for model updates
- `aimodel update download` - Download specific model updates
- `aimodel config` - Manage configuration settings
- `aimodel setup` - Interactive setup wizard

#### Configuration Options
- Model-type-specific download paths
- Default recursive behavior for metadata commands
- API key management
- NSFW content filtering
- Timeout and proxy settings
- Metadata and preview saving options

### Architecture Changes

#### From SD-WebUI Extension to Standalone CLI
- **Removed Dependencies**: Eliminated SD-WebUI and Gradio dependencies
- **Framework Migration**: Migrated from Gradio web interface to Click CLI framework
- **Download System**: Replaced aria2 with optimized HTTP-only downloads
- **User Interface**: Complete redesign from web UI to command-line interface
- **Installation**: Changed from extension installation to pip package

#### Technical Improvements
- **Performance**: Faster startup and operations without SD-WebUI overhead
- **Memory Usage**: Reduced memory footprint
- **Portability**: No external binary dependencies
- **Scriptability**: Full automation and scripting support
- **Modularity**: Clean modular architecture for easy extension

### Inspired By

This project was inspired by [sd-civitai-browser-plus](https://github.com/BlafKing/sd-civitai-browser-plus) by BlafKing. While taking a completely different approach (standalone CLI vs SD-WebUI extension), we appreciate the original project's contribution to the AI model management community.

### Migration Notes

#### For sd-civitai-browser-plus Users
- Configuration migration: Manual copy from `~/.civitai-cli/` to `~/.aimodel-cli/`
- Installation method: Changed from SD-WebUI extension to pip package
- Interface: Command-line instead of web browser
- Dependencies: No longer requires SD-WebUI installation

#### Breaking Changes from Conceptual Predecessor
- Complete architecture change from extension to standalone tool
- Different installation and usage patterns
- CLI-based instead of GUI-based workflow
- Different configuration file locations and formats

### Licensing
- **License**: MIT License (more permissive than original AGPL v3)
- **Independence**: Completely independent codebase
- **Attribution**: Proper acknowledgment of inspiration source

---

**Note**: This is the initial release of AI Model CLI as a standalone project. Future versions will maintain backward compatibility within the 1.x series.