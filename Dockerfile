FROM python:3.11-slim

# Evita que o Python escreva arquivos .pyc no disco
ENV PYTHONDONTWRITEBYTECODE=1

# Evita o buffering de logs do Python, útil para logs de containers
ENV PYTHONUNBUFFERED=1

WORKDIR /code

# Instala dependências do sistema necessárias para o psycopg2 se compilar se preciso, embora psycopg2-binary resolva
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
