CSH Web Packet
==============

[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Build Status](https://travis-ci.org/ComputerScienceHouse/packet.svg?branch=develop)](https://travis-ci.org/ComputerScienceHouse/packet)

Web Packet is used by CSH to facilitate the evaluations of our members and keep track of packet signatures on the web

Authorization
-------------

Authentication happens via pyOIDC with CSH SSO, authenticating as the user who is viewing the page.
We have two different realms, and the site changes depending which realm is in use.

The server uses heavy caching via lru_cache to speed up the results as much as possible

Setup
------

For local development setup follow these steps:

1. ```pip install -r requirements.txt```
2. `Create config.py` or set environment variables
    - Several of these variables require keys and information, please reach out to an RTP for testing information
3. Run `wsgi.py`


Commands
--------

The flask CLI provides all the methods needed to setup a packet and a packet season

```
  create-packets  Creates a new packet season for each of the freshmen in the given CSV.
  create-secret   Generates a securely random token.
  db              Perform database migrations.
  ldap-sync       Updates the upper and misc sigs in the DB to match ldap.
  sync-freshmen   Updates the freshmen entries in the DB to match the given CSV.
  fetch-results   Fetches and prints the results from a given packet season.
```

Code Standards
------------

Use Pylint to ensure your code follows standards. Commits will be pylinted by Travis CI, if your
build fails you must fix whatever it tells you is wrong before it will be merged.

To check locally, run ```pylint packet```
