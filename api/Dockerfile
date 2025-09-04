FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# In docker-compose context must be as follow: "./api", so the requirements.txt file is at the root of that context
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy the api folder contents into /app (this puts main.py at /app/main.py)
COPY . /app

# Import shared helpers from mounted /opt/airflow/src
ENV PYTHONPATH=/opt/airflow

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]