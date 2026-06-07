FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ /app/src
COPY scripts /app/scripts

RUN chmod +x /app/scripts/start/app.sh

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
