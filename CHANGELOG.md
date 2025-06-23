# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2024-12-23

### Added
- Intelligent tool naming system that generates meaningful names from OpenAPI metadata
- Automatic transformation of hash-like operationIds to human-readable tool names
- Tool name generation from operation summaries, tags, and paths

### Fixed
- Tool discovery issues caused by cryptic operationIds in OpenAPI specifications

## [1.0.0] - 2024-12-23

### Added
- Initial release of insly.ai OpenAPI MCP Server
- Full OpenAPI 3.0+ support
- Swagger 2.0 automatic conversion to OpenAPI 3.0
- Streamable HTTP transport as the default transport
- Multiple authentication methods (API Key, Bearer Token, Basic Auth, AWS Cognito)
- Intelligent caching system
- Comprehensive error handling
- Production-ready configuration options
- Docker support
- MCP Inspector compatibility

### Changed
- Rebranded from AWS Labs to insly.ai
- Changed license from Apache 2.0 to MIT
- Updated all imports and package structure
- Streamable HTTP is now the only transport (removed stdio)

### Security
- Enhanced authentication handling
- Secure credential management through environment variables

---

Made with ❤️ by [insly.ai](https://insly.ai)