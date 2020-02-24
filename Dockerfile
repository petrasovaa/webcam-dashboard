#docker build -t dash2 .

FROM ubuntu:xenial

RUN apt-get update && \
    apt-get install -y software-properties-common build-essential python3-pip  nano && \
    apt-get clean

RUN pip3 install --upgrade pip

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .



EXPOSE 8050

CMD gunicorn -w 10 -b 0.0.0.0:8050 -t 100000 --max-requests 20 app:server


#CMD ["python3", "app.py"]

#docker run --rm -v "/media/HealthMattersShare/HealthMatters/Image analysis/All_Processed_Labels/export.csv":/export.csv -it --name dashtest -p 8050:8050 dash2
