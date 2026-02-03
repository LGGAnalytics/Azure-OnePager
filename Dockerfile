# Multi-stage build for Azure OnePager Streamlit Application
# Optimized for production deployment with Azure services integration

# ============================================================
# Stage 1: Base image with system dependencies
# ============================================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for the application
# - libgomp1: Required for OpenCV
# - tesseract-ocr: OCR engine for unstructured document processing
# - poppler-utils: PDF utilities for document processing
# - libgl1: OpenGL libraries for OpenCV
# - libglib2.0-0: Required for OpenCV
# - curl: Health checks and debugging
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /home/appuser/app && \
    chown -R appuser:appuser /home/appuser

WORKDIR /home/appuser/app

# ============================================================
# Stage 2: Dependencies installation
# ============================================================
FROM base as dependencies

# Copy requirements file
COPY --chown=appuser:appuser requirements.txt .

# Install Python dependencies
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# Stage 3: Application
# ============================================================
FROM base as application

# Copy installed Python packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Switch to non-root user
USER appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories for Streamlit
RUN mkdir -p /home/appuser/.streamlit

# Configure Streamlit for production
RUN echo '\
[server]\n\
headless = true\n\
address = "0.0.0.0"\n\
port = 8501\n\
enableCORS = false\n\
enableXsrfProtection = true\n\
maxUploadSize = 200\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
\n\
[theme]\n\
primaryColor = "#F63366"\n\
backgroundColor = "#FFFFFF"\n\
secondaryBackgroundColor = "#F0F2F6"\n\
textColor = "#262730"\n\
font = "sans serif"\n\
' > /home/appuser/.streamlit/config.toml

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Set the entrypoint to run the Streamlit application
# Use the main_page.py file in UI/streamlit directory
ENTRYPOINT ["streamlit", "run", "UI/streamlit/main_page.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true"]
