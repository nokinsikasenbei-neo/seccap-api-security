FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

WORKDIR /api
COPY . .

RUN pip install -r requirements.txt

CMD ["./wait_for_it.sh", "db:3306", "--", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]