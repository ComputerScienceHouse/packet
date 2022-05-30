FROM docker.io/python:3.9-slim-buster
MAINTAINER Devin Matte <matted@csh.rit.edu>

ENV DD_LOGS_INJECTION=true

RUN apt-get -yq update && \
    apt-get -yq --no-install-recommends install gcc curl libsasl2-dev libldap2-dev libssl-dev gnupg2 git && \
    apt-get -yq clean all

RUN mkdir /opt/packet

WORKDIR /opt/packet

COPY requirements.txt /opt/packet/

RUN pip install -r requirements.txt

COPY . /opt/packet

RUN curl -sL https://deb.nodesource.com/setup_10.x | grep -v 'sleep 20' | bash - && \
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list && \
    apt-get -yq update && \
    apt-get -yq --no-install-recommends install nodejs yarn && \
    yarn install && \
    npm install -g gulp && \
    gulp production && \
    rm -rf node_modules && \
    apt-get -yq remove nodejs npm yarn && \
    apt-get -yq autoremove && \
    apt-get -yq clean all

RUN ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime

# Set version for apm
RUN echo "export DD_VERSION=\"$(python3 packet/git.py)\"" >> /tmp/version

CMD ["/bin/bash", "-c", "source /tmp/version && ddtrace-run gunicorn packet:app --bind=0.0.0.0:8080 --access-logfile=- --timeout=600"]
