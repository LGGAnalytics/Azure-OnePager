# Azure OnePager

An AI-powered financial analysis platform for generating comprehensive one-pager profiles of companies in financial distress. Built with Streamlit, LangChain, and Azure AI services.

## 🚀 Features

- **Multi-Source Research**: Aggregates data from Companies House filings, web search, and PDF documents
- **AI-Powered Analysis**: Uses GPT-5 via Azure OpenAI for intelligent content generation
- **Hybrid RAG System**: Combines semantic search, vector embeddings, and BM25 retrieval
- **Multi-Modal Processing**: Extracts insights from text, tables, and images in documents
- **Real-Time Web Search**: Integrates live web search for up-to-date information
- **Azure Integration**: Leverages Azure Cognitive Search, Blob Storage, and Data Factory

## 📋 Quick Start

**New to this project?** Start here: [QUICK_START.md](QUICK_START.md)

### For Streamlit Cloud Deployment (Recommended for you)

1. **Prepare your repository**:
   ```bash
   # Ensure .env is NOT committed (it's in .gitignore)
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy to Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Set main file: `UI/streamlit/main_page.py`
   - Add environment variables in "Advanced settings" (see `.env.example`)
   - Click "Deploy"!

3. **Important Notes**:
   - ⚠️ Streamlit Cloud has a 5-minute timeout limit
   - Your app performs long operations (11-25 min profile generation) which will timeout
   - Consider upgrading to Streamlit Teams/Enterprise or using Azure Container Apps

📖 **Full guide**: [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md)

### For Local Development with Docker

```bash
# 1. Copy and configure environment variables
cp .env.example .env
# Edit .env with your credentials

# 2. Verify your setup
python verify_setup.py

# 3. Build and run with Docker
docker-compose up -d

# 4. Access the app
open http://localhost:8501

# 5. View logs
docker-compose logs -f
```

## 📦 What's Included

After scanning your entire repository, I've created:

### Deployment Files
- ✅ **[Dockerfile](Dockerfile)** - Multi-stage optimized Docker image
- ✅ **[docker-compose.yml](docker-compose.yml)** - Local development orchestration
- ✅ **[.dockerignore](.dockerignore)** - Excludes unnecessary files from Docker builds
- ✅ **[packages.txt](packages.txt)** - System dependencies for Streamlit Cloud
- ✅ **[.gitignore](.gitignore)** - Prevents committing secrets and cache files

### Configuration Templates
- ✅ **[.env.example](.env.example)** - Environment variable template with all required keys

### Documentation
- ✅ **[QUICK_START.md](QUICK_START.md)** - Choose your deployment method
- ✅ **[STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md)** - Streamlit Cloud deployment guide
- ✅ **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** - Docker & Azure deployment guide

### Utilities
- ✅ **[verify_setup.py](verify_setup.py)** - Validates your environment configuration

## 🏗️ Architecture

```
Azure OnePager
├── UI/streamlit/          # Streamlit web interface
│   ├── main_page.py       # Main application (784 lines)
│   └── main_page_theme.py # Custom theming
├── models/
│   ├── agents/            # LangGraph agents
│   │   ├── agent_pdf.py   # PDF analysis with multi-modal RAG
│   │   ├── agent_web.py   # Web search agent
│   │   └── async_profile_agent.py  # Async profile generation
│   ├── engines/           # RAG engines
│   │   ├── hybrid_engine.py  # Multi-modal document processing
│   │   └── hybrid_engine_prompt.py  # System prompts
│   ├── rags/              # Retrieval systems
│   │   └── hybrid_rag.py  # Azure Search + OpenAI integration
│   └── tools/             # Agent tools and functions
├── utils/
│   ├── azure/             # Azure service integrations
│   │   ├── blob_functions.py
│   │   ├── search_functions.py
│   │   └── adf_functions.py
│   └── formatting_tools.py
├── scripts/               # Prompts and formatting
│   ├── default_prompts.py
│   ├── section_prompts.py
│   └── section_formatting.py
└── apis/
    └── companies_house/   # UK Companies House API integration
```

## 🛠️ Technology Stack

### Core Framework
- **Streamlit** - Web UI framework
- **LangChain** - LLM orchestration
- **LangGraph** - Agentic workflows with state graphs

### AI/ML
- **Azure OpenAI (GPT-5)** - Primary LLM
- **OpenAI API** - Fallback/alternative
- **Unstructured** - Document OCR and parsing
- **ChromaDB** - Vector embeddings
- **BM25** - Sparse retrieval

### Azure Services
- **Azure Cognitive Search** - Hybrid semantic/vector search
- **Azure Blob Storage** - Document storage
- **Azure Data Factory** - ETL pipelines
- **Azure Functions** - Serverless triggers

### Observability
- **LangSmith** - LLM call tracing
- **LangFuse** - Agent observability
- **DeepEval** - Quality evaluation

## 🔧 Configuration

### Required Environment Variables

See [.env.example](.env.example) for a complete list. Minimum required:

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_DEPLOYMENT=gpt-5

# OpenAI (fallback)
OPENAI_API_KEY=your_key

# Azure Cognitive Search
AZURE_SEARCH_SERVICE_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_ADMIN_KEY=your_key

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
```

### Verify Your Setup

Before deploying, run the verification script:

```bash
python verify_setup.py
```

This checks:
- ✓ Python version
- ✓ Required files exist
- ✓ Environment variables are set
- ✓ Docker is available (for Docker deployments)
- ✓ Azure connectivity (optional)

## 🚀 Deployment Options

| Method | Best For | Pros | Cons | Setup Time |
|--------|----------|------|------|------------|
| **Streamlit Cloud** | Quick demos, testing | Easy, free tier | 5-min timeout ❌ | 5 minutes |
| **Docker Local** | Development | Full control, no timeouts | Manual setup | 10 minutes |
| **Azure Container Apps** | Production | No timeouts, auto-scaling | Costs ~$30-100/mo | 20 minutes |

⚠️ **Important**: Your app performs long-running operations (11-25 minutes) which **exceed Streamlit Cloud's timeout**. For production, use Azure Container Apps.

## 📊 Performance Considerations

- **Profile Generation**: 11-25+ minutes per company
- **Document Processing**: OCR and vectorization can be slow
- **API Costs**: GPT-5 calls can be $2-10 per profile
- **Memory Requirements**: 2-4 GB recommended for document processing

## 🔒 Security Best Practices

1. ✅ **Never commit `.env`** - It's in `.gitignore`
2. ✅ **Use `.env.example`** as template only
3. ✅ **Rotate API keys** regularly
4. ✅ **Use Azure Key Vault** for production secrets
5. ✅ **Enable Azure firewall rules** to restrict access
6. ✅ **Monitor API usage** to control costs

## 📖 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Choose your deployment path
- **[STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md)** - Deploy to Streamlit Cloud
- **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** - Docker and Azure Container Apps
- **[.env.example](.env.example)** - Environment variable reference

## 🆘 Troubleshooting

### Common Issues

**"Module not found" errors**:
```bash
pip install -r requirements.txt
```

**Azure connection failures**:
- Verify all environment variables in `.env`
- Check API keys are valid
- Ensure Azure firewall allows your IP

**Timeout on Streamlit Cloud**:
- Expected for long operations (11-25 min)
- Upgrade to Streamlit Teams or use Azure Container Apps

**Out of memory**:
- Increase Docker memory limits in `docker-compose.yml`
- Use Azure Container Apps with more resources

### Getting Help

1. Run `python verify_setup.py` to diagnose issues
2. Check logs: `docker-compose logs -f`
3. Review deployment guides in the `docs/` directory
4. Check Azure Portal for service health

## 🧪 Testing

The repository includes test files for quality evaluation:

```bash
# Run tests (requires deepeval)
pytest tests/
```

Tests cover:
- Citation accuracy
- Faithfulness to RAG sources
- Faithfulness in synthesis
- Agent behavior evaluation

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/)
- [LangChain](https://python.langchain.com/)
- [Azure AI Services](https://azure.microsoft.com/en-us/products/ai-services)
- [OpenAI](https://openai.com/)

---

**Ready to deploy?** Start with [QUICK_START.md](QUICK_START.md)
