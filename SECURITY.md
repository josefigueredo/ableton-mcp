# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. Email your findings to: <josefigueredo@gmail.com>
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact
   - Any suggested fixes (optional)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Assessment**: We will assess the vulnerability and determine its severity within 7 days
- **Updates**: We will keep you informed about the progress of addressing the issue
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days
- **Credit**: We will credit you in our release notes (unless you prefer to remain anonymous)

### Scope

This security policy applies to:

- The main `ableton-mcp` package
- All officially maintained plugins and extensions
- Documentation that could lead to security issues if followed incorrectly

### Out of Scope

The following are generally considered out of scope:

- Vulnerabilities in third-party dependencies (please report to the respective maintainers)
- Issues that require physical access to a user's device
- Social engineering attacks
- Denial of service attacks that don't exploit a specific vulnerability

## Security Best Practices

When using Ableton Live MCP Server:

1. **Network Security**: Only expose OSC ports on trusted networks
2. **Access Control**: Limit which applications can connect to the MCP server
3. **Updates**: Keep the package and its dependencies up to date
4. **Environment Variables**: Never commit sensitive configuration to version control

## Disclosure Policy

We follow a coordinated disclosure process:

1. Reporter submits vulnerability privately
2. We acknowledge and assess the report
3. We develop and test a fix
4. We release the fix and publish a security advisory
5. After 90 days (or sooner if the fix is released), the vulnerability may be publicly disclosed

Thank you for helping keep Ableton Live MCP Server and its users safe!
