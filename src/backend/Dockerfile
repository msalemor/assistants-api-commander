FROM python:3.10

#
WORKDIR /code

#
COPY . .

#
RUN mkdir data \
    && pip install --no-cache-dir --upgrade -r requirements.txt

#
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]