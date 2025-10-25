# Usar imagen base arm64 con Python
FROM python:3.10-slim-bullseye

# Instalar dependencias de sistema necesarias para OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Crear carpeta de trabajo
WORKDIR /app

# Copiar requirements y código
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Comando por defecto (modificar según tu script principal)
CMD ["python", "test_model.py"]
