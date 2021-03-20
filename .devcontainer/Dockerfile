FROM mcr.microsoft.com/vscode/devcontainers/universal:1-linux

USER root

# Add LDAP and python dependency build deps
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && \
    apt-get -yq --no-install-recommends install gcc curl libsasl2-dev libldap2-dev libssl-dev python3-dev

USER codespace
