FROM python:3.12-slim

WORKDIR /app

# install git for GitHub dependency
RUN apt-get update && apt-get install -y git

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "server.py"]
