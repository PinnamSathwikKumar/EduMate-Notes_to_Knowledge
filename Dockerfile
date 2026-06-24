# ==============================
# Edumate - Offline Production Docker
# ==============================

FROM pytorch/pytorch:2.2.2-cuda12.1-cudnn8-runtime

WORKDIR /app

ENV TRANSFORMERS_OFFLINE=1
ENV HF_HOME=/app/models
ENV PYTHONUNBUFFERED=1

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY app.py .
COPY templates/ templates/
COPY static/ static/
COPY models/ models/
COPY nltk_data/ nltk_data/

RUN mkdir -p uploads

EXPOSE 5000

CMD ["python", "app.py"]