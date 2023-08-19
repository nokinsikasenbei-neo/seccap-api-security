FROM python:3.8-slim

WORKDIR /frontend

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

ENV FLASK_APP=main.py
ENV FLASK_ENV=development