# Docker MCP Setup for EchoVault

This guide explains how to run EchoVault as a Docker-based MCP (Model Context Protocol) server, following Docker's official MCP implementation standards.

## Overview

The Docker MCP implementation provides:
- ✅ **Official MCP SDK** compliance
- ✅ **Containerized deployment** for consistency
- ✅ **Enterprise-grade** semantic memory capabilities
- ✅ **Cloud-native** architecture with free-tier services
- ✅ **Production-ready** observability and monitoring

## Prerequisites

### Required Software
- Docker Engine 20.10+
- Docker Compose 1.28+
- Git

### Required Services
- **Neon PostgreSQL** (free tier available)
- **Qdrant Cloud** (free tier available) 
- **Cloudflare R2** (free tier available)

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/bjorndavidhansen/mcp-memory-service.git
cd mcp-memory-service

# Switch to the Docker MCP branch
git checkout feature/docker-mcp-integration
```

### 2. Environment Configuration

Create a `.env` file with your cloud service credentials:

```bash
# Copy the example file
cp .env.example .env

# Edit with your actual credentials
nano .env
```

Required environment variables:
```env
# Database Configuration
NEON_DSN=postgresql://username:password@host.neon.tech/dbname?sslmode=require

# Vector Search Configuration
QDRANT_URL=https://your-cluster.qdrant.cloud:6333
QDRANT_API_KEY=your_qdrant_api_key

# Blob Storage Configuration
R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET=echovault-events

# Optional: Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
JWT_SECRET=your_jwt_secret_here
```

### 3. Build and Run

```bash
# Build the MCP container
docker-compose -f docker-compose.mcp.yml build

# Start the MCP server
docker-compose -f docker-compose.mcp.yml up -d

# Check logs
docker-compose -f docker-compose.mcp.yml logs -f
```

## MCP Client Integration

### Claude Desktop Configuration

Add the following to your Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "echovault-memory": {
      "command": "docker",
      "args": [
        "exec",
        "echovault-mcp-server", 
        "python",
        "-m",
        "src.mcp_memory_service"
      ],
      "env": {
        "USE_ECHOVAULT": "true"
      }
    }
  }
}
```

### Alternative: Direct Python Module

If you prefer running without Docker:

```json
{
  "mcpServers": {
    "echovault-memory": {
      "command": "python",
      "args": ["-m", "src.mcp_memory_service"],
      "cwd": "/path/to/mcp-memory-service",
      "env": {
        "USE_ECHOVAULT": "true",
        "NEON_DSN": "your_database_url",
        "QDRANT_URL": "your_qdrant_url",
        "QDRANT_API_KEY": "your_api_key"
      }
    }
  }
}
```

## Available MCP Tools

The EchoVault MCP server exposes these tools:

### 1. `store_memory`
Store content with semantic embeddings and tags.

**Parameters:**
- `content` (required): The content to store
- `tags` (optional): Array of tags for categorization
- `importance` (optional): Importance score 0.0-1.0

**Example:**
```json
{
  "content": "Project deadline is May 15th for the new website launch",
  "tags": ["project", "deadline", "website"],
  "importance": 0.8
}
```

### 2. `search_memories` 
Search using semantic similarity.

**Parameters:**
- `query` (required): Search query
- `limit` (optional): Max results (default: 10)
- `similarity_threshold` (optional): Min similarity score (default: 0.3)

**Example:**
```json
{
  "query": "website deadline",
  "limit": 5,
  "similarity_threshold": 0.4
}
```

### 3. `search_by_tag`
Find memories by tag.

**Parameters:**
- `tag` (required): Tag to search for
- `limit` (optional): Max results (default: 10)

### 4. `get_memory_stats`
Get storage statistics and health information.

### 5. `delete_memory`
Delete a specific memory by ID.

**Parameters:**
- `memory_id` (required): ID of memory to delete

## Testing the MCP Server

### 1. Using MCP Inspector

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Test the server
npx @modelcontextprotocol/inspector python -m src.mcp_memory_service
```

### 2. Manual Testing

```bash
# Test basic functionality
docker exec echovault-mcp-server python -c "
import asyncio
from src.mcp_memory_service.mcp_server import EchoVaultMCPServer

async def test():
    server = EchoVaultMCPServer()
    await server.initialize_storage()
    print('✅ Server initialized successfully')

asyncio.run(test())
"
```

## Development Workflow

### Local Development

```bash
# Install dependencies
pip install -r requirements-mcp.txt

# Run server locally
python -m src.mcp_memory_service

# Test with MCP Inspector
npx @modelcontextprotocol/inspector python -m src.mcp_memory_service
```

### Docker Development

```bash
# Rebuild after changes
docker-compose -f docker-compose.mcp.yml build --no-cache

# View logs
docker-compose -f docker-compose.mcp.yml logs -f echovault-mcp

# Debug shell
docker exec -it echovault-mcp-server bash
```

## Monitoring and Observability

### Health Checks

```bash
# Check container health
docker-compose -f docker-compose.mcp.yml ps

# Detailed health info  
docker inspect echovault-mcp-server --format='{{.State.Health.Status}}'
```

### Logs

```bash
# Application logs
docker-compose -f docker-compose.mcp.yml logs echovault-mcp

# Follow logs
docker-compose -f docker-compose.mcp.yml logs -f echovault-mcp
```

### Metrics

If Prometheus is configured:
- Memory operation counts
- Response latencies
- Error rates
- Storage health metrics

## Troubleshooting

### Common Issues

1. **MCP SDK Import Error**
   ```bash
   # Install MCP SDK
   pip install mcp
   ```

2. **Database Connection Failed**
   - Verify `NEON_DSN` in `.env`
   - Check network connectivity
   - Ensure database exists

3. **Qdrant Authentication Failed**
   - Verify `QDRANT_API_KEY` 
   - Check API key permissions
   - Server will fall back to pgvector

4. **Container Won't Start**
   ```bash
   # Check Docker logs
   docker-compose -f docker-compose.mcp.yml logs echovault-mcp
   
   # Verify environment variables
   docker exec echovault-mcp-server env | grep -E "(NEON|QDRANT|R2)"
   ```

### Debug Mode

Enable debug logging:

```bash
# Add to .env file
LOG_LEVEL=DEBUG

# Restart container
docker-compose -f docker-compose.mcp.yml restart
```

## Security Considerations

### Environment Variables
- Never commit `.env` files
- Use Docker secrets in production
- Rotate credentials regularly

### Network Security
- MCP servers typically use stdio (no network exposure)
- Container network isolation
- TLS for all cloud service connections

### Access Control
- JWT authentication available
- Role-based permissions
- Audit logging

## Production Deployment

### Docker Swarm

```yaml
# docker-stack.yml
version: '3.8'
services:
  echovault-mcp:
    image: echovault/mcp-server:latest
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
    secrets:
      - neon_dsn
      - qdrant_api_key
    networks:
      - overlay-network
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echovault-mcp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: echovault-mcp
  template:
    metadata:
      labels:
        app: echovault-mcp
    spec:
      containers:
      - name: echovault-mcp
        image: echovault/mcp-server:latest
        env:
        - name: USE_ECHOVAULT
          value: "true"
        envFrom:
        - secretRef:
            name: echovault-secrets
```

## Performance Tuning

### Memory Configuration

```env
# Increase for large deployments
NEON_POOL_SIZE=10
BLOB_THRESHOLD=65536
```

### Resource Limits

```yaml
# docker-compose.mcp.yml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
```

## Conclusion

The Docker MCP implementation provides a robust, scalable way to deploy EchoVault's semantic memory capabilities. It follows MCP standards for maximum compatibility while leveraging enterprise-grade cloud services for durability and performance.

For additional support, see:
- [MCP Documentation](https://modelcontextprotocol.io/)
- [EchoVault Architecture](ECHOVAULT_ARCHITECTURE.md)
- [Troubleshooting Guide](../guides/troubleshooting.md) 