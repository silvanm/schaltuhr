FROM python:3.7

WORKDIR /code

ADD /code /code

RUN pip install -r requirements.txt

CMD ["python","scheduler.py"]

