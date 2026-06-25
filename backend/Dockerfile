FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# CPU-only torch — keeps the final image around 600-800MB instead of 2+GB.
# Use a very generous pip timeout because the 195 MB wheel can stall on
# slow links and trip the default 15s socket read timeout.
ENV PIP_DEFAULT_TIMEOUT=600
RUN pip install --no-cache-dir --timeout 600 --retries 5 \
    --index-url https://download.pytorch.org/whl/cpu torch==2.4.1
RUN pip install --no-cache-dir --timeout 600 --retries 5 -r requirements.txt

ENV HF_HOME=/opt/hf-cache
ENV MODEL_NAME=distilbert-base-uncased-finetuned-sst-2-english

# Bake the model weights into the image at BUILD time (not runtime)
RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
AutoTokenizer.from_pretrained('${MODEL_NAME}'); \
AutoModelForSequenceClassification.from_pretrained('${MODEL_NAME}')"

COPY app ./app

# Fail loudly instead of silently downloading if weights are ever missing
ENV TRANSFORMERS_OFFLINE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]