FROM python:3.11.9
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
