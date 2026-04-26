FROM python:3.12-slim

WORKDIR /

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --parents app/ app/
COPY run.py /

EXPOSE 5000

CMD ["python", "run.py"]
#CMD ["ls", "-l", "/app"]