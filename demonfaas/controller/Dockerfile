FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY routing_controller.py .

CMD ["python", "routing_controller.py"]