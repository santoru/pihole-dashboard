# Changelog

All notable changes to the Pi-hole Dashboard project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-06-14

### Added
- Compatibility with Pi-hole v6.x
- New authentication method using session-based approach for Pi-hole v6
- Dedicated section in README explaining Pi-hole v6 compatibility
- Error handling for new API endpoints
- Enhanced `pihole-dashboard-draw` with verbose mode showing configuration and API endpoints
- Added version flag to `pihole-dashboard-draw`
- Command-line argument parsing for diagnostic options
- Advanced diagnostics with `--test` flag to isolate and troubleshoot API connection issues
- Debug mode with `--debug` flag for detailed API responses
- Comprehensive error reporting for 401 Unauthorized errors
- Step-by-step API connection testing to pinpoint authentication problems
- Expanded troubleshooting documentation with common issues and solutions
- Support for CSRF token authentication in Pi-hole v6
- Cookie-based session handling for enhanced compatibility
- Session caching mechanism to reuse existing Pi-hole sessions between executions, reducing authentication requests

### Changed
- Replaced API token-based authentication with password-based authentication
- Updated API endpoints to use Pi-hole v6 RESTful API
- Improved error handling with more descriptive error messages
- Configuration now accepts password instead of API token
- Updated README to reflect new authentication method
- Expanded troubleshooting section with new diagnostic options
- Enhanced command-line interface with standardized arguments
- Improved API session handling to work with Pi-hole v6's security requirements
- Updated connection test to properly handle Pi-hole v6's 403 responses for the root URL

### Fixed
- Dashboard now works with Pi-hole v6's new API structure
- More robust error handling during API calls
- Clearer installation instructions for v6 compatibility
- Better diagnostic information for authentication failures
- Fixed authentication to handle Pi-hole v6's nested session data structure
- Resolved issue with session ID not being properly extracted from authentication response
- Fixed API access by implementing multiple authentication methods (header, cookie, CSRF)
- Solved session validation issues with Pi-hole v6 API
- Updated `/api/dns/status` endpoint to `/api/dns/blocking` for Pi-hole v6 compatibility
- Added support for the new Pi-hole v6 API response format for client statistics (`clients.active` instead of `unique_clients`)
- Added support for the new Pi-hole v6 API response format for blocked ads statistics (`queries.blocked` instead of `ads_blocked_today`)
- Improved error handling for different API response formats to support both v5 and v6 versions

## [1.0.3] - 2023-05-12

### Fixed
- Fixed display of network interface IP when using alternative interfaces
- Improved error reporting when API token is invalid
- Fixed screen rotation issues with certain display configurations

## [1.0.2] - 2022-11-20

### Added
- Support for Waveshare 2.13" V3 E-Ink display

### Changed
- Improved error handling when Pi-hole API is unreachable
- Updated installation documentation

## [1.0.1] - 2022-07-05

### Fixed
- Fixed cronjob installation path
- Improved compatibility with different Python versions

## [1.0.0] - 2021-11-10

### Added
- Initial release
- Support for Waveshare 2.13" V2 E-Ink display
- Pi-hole statistics display including:
  - IP address of the Raspberry Pi
  - Pi-hole status (enabled/disabled)
  - Connected clients count
  - Blocked ads count
- Auto-refresh functionality via cron job
- Screen rotation option
- Full installation documentation 