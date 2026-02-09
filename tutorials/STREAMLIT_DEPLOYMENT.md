# Streamlit Cloud Deployment Guide

This guide covers deploying Azure OnePager to Streamlit Cloud.

## Prerequisites

- GitHub account with this repository
- Streamlit Cloud account ([Sign up free](https://streamlit.io/cloud))
- Azure services configured (OpenAI, Search, Blob Storage, etc.)

## Deployment Steps

### 1. Prepare Your Repository

Ensure these files are in your repository:
- ✅ `requirements.txt` - Python dependencies
- ✅ `UI/streamlit/main_page.py` - Main application file
- ✅ `.env.example` - Environment variable template (for documentation)
- ❌ `.env` - Should be in `.gitignore` (NEVER commit this!)

### 2. Push to GitHub

```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### 3. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your repository: `Azure-OnePager`
4. Set main file path: `UI/streamlit/main_page.py`
5. Select branch: `main` (or your preferred branch)
6. Click "Advanced settings"

### 4. Configure Environment Variables

In the "Advanced settings" section, add all your secrets:

```toml
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = "https://teneoproject2.openai.azure.com/"
AZURE_OPENAI_API_KEY = "your_azure_openai_api_key"
AZURE_OPENAI_DEPLOYMENT = "gpt-5"
AZURE_OPENAI_API_VERSION = "2024-12-01-preview"

# OpenAI Configuration
OPENAI_API_KEY = "your_openai_api_key"
FELIPE_OPENAI_API_KEY = "your_felipe_openai_key"

# Azure Cognitive Search
AZURE_SEARCH_SERVICE_ENDPOINT = "https://teneosearchpaid.search.windows.net"
AZURE_SEARCH_ADMIN_KEY = "your_search_admin_key"
AZURE_SEARCH_INDEX_NAME = "rag-finaltest"

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING = "your_connection_string"
AZURE_STORAGE_ACCOUNT_NAME = "aiprojectteneo"
AZURE_STORAGE_ACCOUNT_KEY = "your_storage_key"
AZURE_STORAGE_CONTAINER = "tryout"

# Azure Data Factory
AZURE_SUBSCRIPTION_ID = "your_subscription_id"
AZURE_RESOURCE_GROUP = "AI-proj"
AZURE_DATA_FACTORY_NAME = "Teneo-AI"

# Additional API Keys
GROQ_API_KEY = "your_groq_api_key"
LANGSMITH_API_KEY = "your_langsmith_api_key"
LANGFUSE_SECRET_KEY = "your_langfuse_secret_key"
LANGFUSE_PUBLIC_KEY = "your_langfuse_public_key"
LANGFUSE_HOST = "https://cloud.langfuse.com"

# Companies House API
COMPANIES_HOUSE_API_KEY = "your_companies_house_api_key"

# Supabase (if used)
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_key"
```

### 5. Deploy

Click "Deploy" and wait for the app to build and launch!

## Important Notes for Streamlit Cloud

### Resource Limitations

Streamlit Cloud has resource constraints:
- **Memory**: 1 GB RAM on free tier, 8 GB on paid
- **CPU**: Shared CPU resources
- **Timeout**: 5-minute execution timeout per script run
- **File Storage**: Ephemeral (files reset on restart)

⚠️ **Critical Issue**: Your app does long-running operations (11-25 min profile generation) which **exceed Streamlit Cloud's timeout limits**.

### Recommended Solutions

**Option A: Upgrade to Streamlit Cloud Teams/Enterprise**
- Higher resource limits
- Extended timeouts
- Better for production workloads
- [Pricing details](https://streamlit.io/cloud)

**Option B: Use Async Processing with Azure Functions**
- Trigger profile generation as Azure Function
- Poll for completion status
- Display results when ready
- Keeps Streamlit app responsive

**Option C: Deploy to Azure Container Apps**
- No timeout limits
- Full control over resources
- Use the provided Dockerfile
- More suitable for long-running operations

## Package-Specific Notes

### `unstructured[all-docs]`

This package is **very large** and may cause issues on Streamlit Cloud. If you encounter deployment issues:

**Option 1**: Use lightweight version
```txt
# Replace in requirements.txt:
unstructured  # instead of unstructured[all-docs]
```

**Option 2**: Install specific extras only
```txt
unstructured[pdf,docx]  # Only what you need
```

### `chromadb`

ChromaDB requires persistent storage. On Streamlit Cloud:
- Data is ephemeral (resets on restart)
- Consider using Azure Cognitive Search exclusively
- Or use a hosted ChromaDB service

### System Dependencies

Streamlit Cloud comes with common system packages. If `tesseract-ocr` or `poppler-utils` are needed, add a `packages.txt` file:

```bash
# Create packages.txt in root directory
tesseract-ocr
poppler-utils
```

## Troubleshooting

### Issue: App crashes during startup

**Solution**: Check dependencies
```bash
# Test locally first
pip install -r requirements.txt
streamlit run UI/streamlit/main_page.py
```

### Issue: "Module not found" errors

**Solution**: Verify all imports are in `requirements.txt`

### Issue: Timeout errors during profile generation

**Solution**: This is expected - your 11-25 min operations exceed limits. Consider async processing or Azure deployment.

### Issue: Azure connection failures

**Solution**:
- Verify all environment variables are set in Streamlit Cloud
- Check Azure firewall rules allow Streamlit Cloud IPs
- Test API keys are valid and have required permissions

### Issue: Memory errors

**Solution**:
- Upgrade to Streamlit Cloud paid tier
- Optimize document processing (process in chunks)
- Clear Streamlit cache regularly: `st.cache_data.clear()`

## Local Development with Docker

For local testing, you can use Docker:

```bash
# Build and run
docker-compose up

# Access at http://localhost:8501
```

This provides a production-like environment for testing before deploying to Streamlit Cloud.

## Monitoring Your App

1. **Streamlit Cloud Dashboard**: View logs and metrics
2. **Azure Application Insights**: Monitor Azure service calls
3. **LangSmith**: Track LLM calls and performance
4. **LangFuse**: Observability for LangChain operations

## Updating Your Deployment

Streamlit Cloud auto-deploys on git push:

```bash
git add .
git commit -m "Update application"
git push origin main
```

Your app will automatically rebuild and redeploy!

## Security Best Practices

1. ✅ Use Streamlit Cloud secrets (not .env in git)
2. ✅ Keep `.env` in `.gitignore`
3. ✅ Rotate API keys regularly
4. ✅ Use Azure managed identities when possible
5. ✅ Enable Azure firewall rules to restrict access
6. ✅ Monitor API usage and set spending limits

## Cost Considerations

Your app uses several paid Azure services:
- **Azure OpenAI (GPT-5)**: ~$2-10 per profile generation
- **Azure Cognitive Search**: Pay-per-query
- **Azure Blob Storage**: Storage + bandwidth costs
- **Streamlit Cloud**: Free tier has limits

Monitor usage in Azure Portal to avoid unexpected charges.

## Need More Power?

If Streamlit Cloud doesn't meet your needs due to timeouts or resource limits, consider deploying to:

1. **Azure Container Apps** (Recommended)
   - Use provided Dockerfile
   - Auto-scaling
   - No timeouts
   - See `DOCKER_DEPLOYMENT.md`

2. **Azure App Service**
   - Managed platform
   - Good for Python apps
   - Integrated with Azure services

3. **Azure Kubernetes Service (AKS)**
   - Enterprise-grade
   - Full orchestration
   - Complex but powerful
