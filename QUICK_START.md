# Quick Start Guide - Azure OnePager

## 🚀 Deployment Options

Choose your deployment method:

### Option 1: Streamlit Cloud (Easiest) ⭐ RECOMMENDED FOR YOU

**Best for**: Quick deployment, no infrastructure management

**Steps**:
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Set main file: `UI/streamlit/main_page.py`
5. Add environment variables in "Advanced settings"
6. Deploy!

📖 **Full guide**: [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md)

⚠️ **Important**: Streamlit Cloud has a 5-minute timeout. Your profile generation (11-25 min) will timeout. Consider:
- Upgrading to Streamlit Teams/Enterprise
- Using Docker deployment for production

---

### Option 2: Docker Local (For Development)

**Best for**: Local testing, consistent environment

**Steps**:
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your credentials
nano .env

# 3. Build and run
docker-compose up -d

# 4. Access app
open http://localhost:8501

# 5. View logs
docker-compose logs -f

# 6. Stop
docker-compose down
```

---

### Option 3: Azure Container Apps (Production)

**Best for**: Production deployments, long-running operations, auto-scaling

**Why use this**:
- ✅ No timeout limits (perfect for 11-25 min operations)
- ✅ Auto-scaling
- ✅ Integrated with Azure services
- ✅ Managed HTTPS
- ✅ Better performance

**Quick deploy**:
```bash
# Build and push to Azure Container Registry
az acr build --registry <your-acr> --image azure-onepager:latest .

# Deploy to Container Apps
az containerapp create \
  --name azure-onepager \
  --resource-group <your-rg> \
  --image <your-acr>.azurecr.io/azure-onepager:latest \
  --target-port 8501 \
  --ingress external \
  --cpu 2 --memory 4Gi
```

📖 **Full guide**: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

---

## 📋 Prerequisites Checklist

Before deploying, ensure you have:

### Azure Services
- [ ] Azure OpenAI with GPT-5 deployment
- [ ] Azure Cognitive Search with index configured
- [ ] Azure Blob Storage with container
- [ ] Azure Data Factory (optional, for ingestion)

### API Keys
- [ ] OpenAI API key(s)
- [ ] Azure Search admin key
- [ ] Azure Storage connection string
- [ ] Companies House API key
- [ ] LangSmith key (optional)
- [ ] LangFuse keys (optional)

### Development Tools
- [ ] Python 3.11+
- [ ] Docker Desktop (for Docker deployment)
- [ ] Git
- [ ] Azure CLI (for Azure deployment)

---

## 🔧 Configuration

### Required Environment Variables

```bash
# Minimum required for app to run
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_DEPLOYMENT=gpt-5
OPENAI_API_KEY=your_openai_key
AZURE_SEARCH_SERVICE_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_ADMIN_KEY=your_search_key
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
```

See `.env.example` for complete list.

---

## 🎯 Which Deployment Should You Choose?

| Feature | Streamlit Cloud | Docker Local | Azure Container Apps |
|---------|----------------|--------------|---------------------|
| **Setup Time** | 5 minutes | 10 minutes | 20 minutes |
| **Cost** | Free tier available | Free (local) | ~$30-100/month |
| **Timeout Limits** | 5 minutes ❌ | None ✅ | None ✅ |
| **Scaling** | Auto | Manual | Auto ✅ |
| **Long Operations** | ❌ Timeouts | ✅ Works | ✅ Works |
| **Best For** | Demos, quick tests | Development | Production |

**For your use case (11-25 min operations)**: Use **Docker Local** for development, **Azure Container Apps** for production.

---

## 🆘 Common Issues

### "Module not found" error
```bash
pip install -r requirements.txt
```

### Azure connection fails
- Check environment variables are set correctly
- Verify API keys are valid
- Check Azure firewall allows your IP

### Timeout on Streamlit Cloud
- Expected for long operations
- Upgrade to Teams tier or use Azure Container Apps

### Out of memory
- Increase Docker memory limit
- Upgrade Streamlit Cloud tier
- Use Azure Container Apps with more resources

---

## 📚 Documentation

- **Streamlit Cloud**: [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md)
- **Docker**: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- **Environment Variables**: [.env.example](.env.example)

---

## 🔒 Security Reminders

- ⚠️ **NEVER commit `.env` file to Git**
- ✅ Use `.env.example` as template only
- ✅ Rotate API keys regularly
- ✅ Use Azure Key Vault for production
- ✅ Enable Azure firewall rules

---

## 🎉 You're Ready!

Choose your deployment method above and follow the corresponding guide. Need help? Check the troubleshooting sections in each deployment guide.
