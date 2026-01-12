# Docker Deployment Guide for Azure OnePager

This guide covers how to build and deploy the Azure OnePager application using Docker.

## Prerequisites

- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))
- Docker Compose (included with Docker Desktop)
- Git
- Azure account with required services configured

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Azure-OnePager
```

### 2. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual credentials
nano .env  # or use your preferred editor
```

### 3. Build and Run with Docker Compose

```bash
# Build the Docker image
docker-compose build

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access the Application

Open your browser and navigate to:
```
http://localhost:8501
```

## Manual Docker Commands

### Build the Image

```bash
docker build -t azure-onepager:latest .
```

### Run the Container

```bash
docker run -d \
  --name azure-onepager \
  -p 8501:8501 \
  --env-file .env \
  azure-onepager:latest
```

### View Logs

```bash
docker logs -f azure-onepager
```

### Stop the Container

```bash
docker stop azure-onepager
docker rm azure-onepager
```

## Deployment to Azure

### Option 1: Azure Container Instances (ACI)

```bash
# Login to Azure
az login

# Create a resource group (if needed)
az group create --name azure-onepager-rg --location eastus

# Create Azure Container Registry
az acr create --resource-group azure-onepager-rg \
  --name <your-acr-name> --sku Basic

# Login to ACR
az acr login --name <your-acr-name>

# Tag your image
docker tag azure-onepager:latest <your-acr-name>.azurecr.io/azure-onepager:latest

# Push to ACR
docker push <your-acr-name>.azurecr.io/azure-onepager:latest

# Deploy to ACI
az container create \
  --resource-group azure-onepager-rg \
  --name azure-onepager-app \
  --image <your-acr-name>.azurecr.io/azure-onepager:latest \
  --cpu 2 --memory 4 \
  --ports 8501 \
  --dns-name-label azure-onepager-app \
  --environment-variables \
    AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
    AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
  # ... add all other environment variables
```

### Option 2: Azure Container Apps (Recommended for Production)

Azure Container Apps provides better scaling, managed certificates, and integrated monitoring.

```bash
# Install Azure Container Apps extension
az extension add --name containerapp --upgrade

# Create Container Apps environment
az containerapp env create \
  --name azure-onepager-env \
  --resource-group azure-onepager-rg \
  --location eastus

# Deploy the app
az containerapp create \
  --name azure-onepager \
  --resource-group azure-onepager-rg \
  --environment azure-onepager-env \
  --image <your-acr-name>.azurecr.io/azure-onepager:latest \
  --target-port 8501 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 2 --memory 4Gi
```

### Option 3: Azure Web App for Containers

```bash
# Create App Service Plan
az appservice plan create \
  --name azure-onepager-plan \
  --resource-group azure-onepager-rg \
  --is-linux --sku B2

# Create Web App
az webapp create \
  --resource-group azure-onepager-rg \
  --plan azure-onepager-plan \
  --name <your-unique-app-name> \
  --deployment-container-image-name <your-acr-name>.azurecr.io/azure-onepager:latest

# Configure app settings (environment variables)
az webapp config appsettings set \
  --resource-group azure-onepager-rg \
  --name <your-unique-app-name> \
  --settings \
    AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
    AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY"
  # ... add all other variables
```

## Using Azure Key Vault for Secrets

Instead of environment variables, use Azure Key Vault for secure secret management:

```bash
# Create Key Vault
az keyvault create \
  --name <your-keyvault-name> \
  --resource-group azure-onepager-rg \
  --location eastus

# Add secrets
az keyvault secret set \
  --vault-name <your-keyvault-name> \
  --name "AZURE-OPENAI-API-KEY" \
  --value "your_secret_value"

# Grant Container App access to Key Vault
# Enable managed identity on your container app
az containerapp identity assign \
  --name azure-onepager \
  --resource-group azure-onepager-rg \
  --system-assigned

# Set access policy
az keyvault set-policy \
  --name <your-keyvault-name> \
  --object-id <managed-identity-principal-id> \
  --secret-permissions get list
```

## Monitoring and Debugging

### Check Health Status

```bash
# Health check endpoint
curl http://localhost:8501/_stcore/health
```

### View Container Logs

```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f azure-onepager

# Azure Container Instances
az container logs --resource-group azure-onepager-rg --name azure-onepager-app --follow

# Azure Container Apps
az containerapp logs show \
  --name azure-onepager \
  --resource-group azure-onepager-rg \
  --follow
```

### SSH into Running Container (for debugging)

```bash
docker exec -it azure-onepager /bin/bash
```

## Performance Tuning

### Resource Allocation

Adjust CPU and memory in [docker-compose.yml](docker-compose.yml):

```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # Increase for better performance
      memory: 8G     # Increase for large document processing
```

### Scaling with Docker Compose

```bash
# Run multiple replicas
docker-compose up -d --scale azure-onepager=3
```

## Troubleshooting

### Common Issues

**Issue: Container exits immediately**
- Check logs: `docker-compose logs`
- Verify all required environment variables are set in `.env`

**Issue: Cannot connect to Azure services**
- Verify network connectivity
- Check firewall rules in Azure
- Ensure API keys are valid

**Issue: Out of memory errors**
- Increase memory limits in docker-compose.yml
- Monitor resource usage: `docker stats`

**Issue: Slow document processing**
- Increase CPU allocation
- Check Azure Search and OpenAI quotas
- Monitor network latency to Azure services

## Security Best Practices

1. **Never commit `.env` files** - Always use `.env.example` as a template
2. **Use Azure Key Vault** for production secrets
3. **Enable managed identities** instead of API keys when possible
4. **Regularly update base images**: `docker pull python:3.11-slim`
5. **Scan images for vulnerabilities**: `docker scan azure-onepager:latest`
6. **Use least-privilege access** for Azure service principals

## CI/CD Integration

See [.github/workflows/docker-build.yml](.github/workflows/docker-build.yml) for automated builds and deployments.

## Additional Resources

- [Streamlit Docker Deployment](https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker)
- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure Container Registry](https://learn.microsoft.com/en-us/azure/container-registry/)
