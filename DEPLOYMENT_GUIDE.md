# 🚀 Gmail MCP Agent — Deployment Guide

This guide will help you deploy the Gmail MCP Agent to run 24/7 using an MCP (Model Context Protocol) server.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │◄──►│   MCP Server     │◄──►│  Lead Nurturer  │
│  (Control)      │    │  (24/7 Service)  │    │  (Automation)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Gmail API      │
                       │  (Email System)  │
                       └──────────────────┘
```

## 📋 Prerequisites

- **Docker** and **Docker Compose** installed
- **Gmail API credentials** (`credentials.json`)
- **Contact list** (`contacts.csv`)
- **Email templates** (`templates/` and `body.txt`)
- **Configuration** (`nurturing_config.json`)

## 🚀 Quick Deployment

### Option 1: Docker Deployment (Recommended)

1. **Clone/Download** your project files
2. **Run the deployment script**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

That's it! Your system is now running 24/7.

### Option 2: Manual Docker Setup

1. **Build the image**:
   ```bash
   docker-compose build
   ```

2. **Start the service**:
   ```bash
   docker-compose up -d
   ```

3. **Check status**:
   ```bash
   docker-compose ps
   ```

## 🎮 Controlling Your System

### Using the MCP Client

```bash
# Start nurturing system (every 4 hours)
python mcp_client.py start 4

# Check system status
python mcp_client.py status

# Run single cycle immediately
python mcp_client.py cycle

# Get lead report
python mcp_client.py report

# Send test email
python mcp_client.py test your-email@example.com

# View recent logs
python mcp_client.py logs 100

# Stop the system
python mcp_client.py stop
```

### Using Docker Commands

```bash
# View logs
docker-compose logs -f

# Restart service
docker-compose restart

# Stop service
docker-compose down

# Update and restart
docker-compose pull && docker-compose up -d
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file for configuration:

```env
# Gmail API Configuration
CREDENTIALS_FILE=credentials.json
TOKEN_FILE=token.json

# Nurturing Settings
PER_MINUTE=12
RESUME=false
LOG_FILE=send_log.csv

# MCP Server Settings
MCP_SERVER_PORT=8000
LOG_LEVEL=INFO
```

### Nurturing Configuration

Edit `nurturing_config.json`:

```json
{
  "sender_email": "",
  "sender_name": "Your Name",
  "company_name": "Your Company",
  "follow_up_schedule": {
    "followup_1_days": 3,
    "followup_2_days": 7
  },
  "automation": {
    "check_responses_interval_hours": 4,
    "auto_respond_to_interest": true
  }
}
```

See the [configuration reference in the README](README.md#️-configuration-reference)
for the full schema.

## 📊 Monitoring & Maintenance

### Health Checks

The system includes built-in health checks:

```bash
# Check if service is healthy
docker-compose ps

# View health check logs
docker-compose logs lead-nurturing
```

### Log Management

Logs are automatically rotated and stored in:
- `mcp_server.log` - MCP server logs
- `send_log.csv` - Email sending logs
- `lead_tracking.json` - Lead data

### Backup Strategy

Important files to backup:
- `lead_tracking.json` - Lead progress data
- `nurturing_config.json` - Configuration
- `templates/` - Your email copy
- `credentials.json` - Gmail API credentials
- `contacts.csv` - Your lead list

## 🔒 Security Considerations

### File Permissions

```bash
# Secure sensitive files
chmod 600 credentials.json
chmod 600 nurturing_config.json
```

### Network Security

- The MCP server runs locally (no external ports exposed)
- Gmail API uses OAuth2 authentication
- All data is stored locally

### Data Privacy

- No data is sent to external services
- All lead data remains on your server
- Gmail API only accesses your Gmail account

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start**:
   ```bash
   docker-compose logs
   # Check for missing files or permission issues
   ```

2. **Gmail API errors**:
   ```bash
   # Verify credentials.json is valid
   python -c "import json; json.load(open('credentials.json'))"
   ```

3. **No emails being sent**:
   ```bash
   # Check Gmail API quotas and permissions
   python mcp_client.py test your-email@example.com
   ```

4. **High memory usage**:
   ```bash
   # Restart the service
   docker-compose restart
   ```

### Debug Mode

Enable debug logging:

```bash
# Edit docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG

# Restart service
docker-compose up -d
```

## 📈 Performance Optimization

### Resource Limits

The Docker setup includes resource limits:
- **Memory**: 512MB limit, 256MB reserved
- **CPU**: 0.5 cores limit, 0.25 cores reserved

### Scaling

For high-volume campaigns:

1. **Increase resources** in `docker-compose.yml`
2. **Adjust rate limits** in `nurturing_config.json`
3. **Use multiple instances** (advanced)

## 🔄 Updates & Maintenance

### Regular Maintenance

1. **Weekly**: Check system status and logs
2. **Monthly**: Review lead reports and optimize
3. **Quarterly**: Update dependencies and security

### Updating the System

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

## 📞 Support

### Logs Location

- **Application logs**: `docker-compose logs -f`
- **System logs**: `/var/log/syslog` (Linux)
- **Docker logs**: `docker logs lead-nurturing-server`

### Getting Help

1. Check the logs first
2. Verify all required files exist
3. Test with a single cycle
4. Check Gmail API quotas

## 🎯 What to expect

With proper setup you get:

- Continuous operation with Docker restart policies
- Automated follow-ups on your configured schedule
- Reply detection and lead scoring every cycle
- 24/7 monitoring via the MCP server

Actual response and conversion rates depend entirely on your audience, offer,
and message quality — tune your templates and keywords accordingly.

> Always email responsibly: only contact people who have opted in, honor
> unsubscribe requests, respect Gmail's sending limits, and follow applicable
> anti-spam laws.

---

**Your Gmail MCP Agent is now ready for 24/7 operation.** 🚀

Run `./deploy.sh` to get started, then use `python mcp_client.py status` to monitor it.
