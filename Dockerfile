FROM python:3.6-stretch
MAINTAINER Devin Matte <matted@csh.rit.edu>

RUN mkdir /opt/packet

ADD requirements.txt /opt/packet

WORKDIR /opt/packet

RUN apt-get -yq update && \
    apt-get -yq install libsasl2-dev libldap2-dev libssl-dev xmlsec1 && \
    pip install -r requirements.txt && \
    apt-get -yq clean all

ADD . /opt/packet

CMD ["gunicorn", "packet:app", "--bind=0.0.0.0:8080", "--access-logfile=-"]
