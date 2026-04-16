FROM python:3.11-slim

WORKDIR /app

# ✅ INSTALL GIT (THIS WAS MISSING)
RUN apt-get update && apt-get install -y git

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "server.py"]
