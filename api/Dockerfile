FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

WORKDIR /api

COPY requirements.txt ./

RUN apt-get update && \
    pip install -r requirements.txt

COPY . .

CMD ["./wait_for_it.sh", "db:3306", "--", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]