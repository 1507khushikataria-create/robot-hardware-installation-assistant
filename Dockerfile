FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip

# Install CPU-only PyTorch
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch torchvision torchaudio

# Install the remaining packages
RUN pip install --no-cache-dir --retries 10 -r requirements.txt

COPY . .

CMD ["python","-m","uvicorn","backend:app","--host","0.0.0.0","--port","8000"]