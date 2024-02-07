FROM python:3.10

#
WORKDIR /code

# RUN mkdir data
# RUN mkdir wwwroot

COPY . .
COPY data data
COPY wwwroot wwwroot

RUN pip install --no-cache-dir --upgrade -r requirements.txt

#
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--workers","4"]