FROM docker.io/python:3.9-slim-trixie

RUN ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime
RUN apt-get -yq update && \
    apt-get -yq --no-install-recommends install gcc curl libsasl2-dev libldap2-dev libssl-dev gnupg2 git && \
    apt-get -yq clean all \
    curl -sL https://deb.nodesource.com/setup_20.x | bash - && \
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | gpg --dearmor -o /usr/share/keyrings/yarn-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/yarn-archive-keyring.gpg] https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list && \
    apt-get -yq update && \
    apt-get -yq --no-install-recommends install nodejs yarn

RUN mkdir /opt/packet
WORKDIR /opt/packet

COPY requirements.txt /opt/packet/
RUN pip install uv && uv pip install -r requirements.txt --system

COPY package.json /opt/packet/
COPY yarn.lock /opt/packet/

RUN yarn install && \
    yarn global add gulp

COPY . /opt/packet
RUN gulp production && \
    rm -rf node_modules && \
    apt-get -yq remove nodejs npm yarn && \
    apt-get -yq autoremove && \
    apt-get -yq clean all

# Set version for apm
RUN echo "export DD_VERSION=\"$(python3 packet/git.py)\"" >> /tmp/version

RUN groupadd -r packet && useradd --no-log-init -r -g packet packet && \
    chown -R packet:packet /opt/packet

USER packet

CMD ["/bin/bash", "-c", "source /tmp/version && ddtrace-run gunicorn packet:app --bind=0.0.0.0:8080 --access-logfile=- --timeout=600"]
