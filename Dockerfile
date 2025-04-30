FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wkhtmltopdf \
    xvfb \
    xfonts-75dpi \
    xfonts-base \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libgirepository1.0-dev \
    pkg-config \
    gir1.2-pango-1.0 \
    gir1.2-gtk-3.0 \
    python3-gi \
    python3-gi-cairo \
    python3-cairo \
    libcairo2-dev \
    libpango1.0-dev \
    libpangocairo-1.0-0 \
    libglib2.0-dev \
    gobject-introspection \
    libxml2-dev \
    libxslt1-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8501

# Expose the port
EXPOSE $PORT

# Start the application
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 