FROM ubuntu:latest
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential libpq-dev
COPY . /app
WORKDIR /app
#RUN pip install -r requirements.txt
RUN pip install --no-index --find-links="./pypackages" -r requirements.txt
ENTRYPOINT ["python"]
CMD ["app.py"]