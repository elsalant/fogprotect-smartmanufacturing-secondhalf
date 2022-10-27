FROM python:3.8-slim
WORKDIR /app
RUN apt-get update && apt-get -y upgrade
#RUN pip install pyyaml
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY module module
COPY kafkaToS3.py kafkaToS3.py
#ENTRYPOINT ["python3"]
ENV PYTHONUNBUFFERED=1
CMD ["python3", "./kafkaToS3.py"]

