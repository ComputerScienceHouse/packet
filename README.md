# CSH Web Packet

[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Build Status](https://travis-ci.org/ComputerScienceHouse/packet.svg?branch=develop)](https://travis-ci.org/ComputerScienceHouse/packet)

Packet is used by CSH to facilitate the freshmen packet portion of our introductory member evaluation process. This is 
the second major iteration of packet on the web. The first was [Tal packet](https://github.com/TalCohen/CSHWebPacket).

## Setup
**Requires Python 3.6 or newer.**

To get the server working you'll just need the Python dependencies and some secrets. There will be some UI issues due 
to missing assets though. To solve that you'll want to set up the front end dependencies or download a copy of the 
current assets from prod.

Alternatively, you can set up a Docker container using `Dockerfile`. This is what's used in prod so it's the most 
reliable method.

### Python dependencies
Use `pip3 install -r requirements.txt` to install the required python dependencies. A 
[venv](https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments) is *highly* 
recommended. 

If 1 or more of the packages fail to install the likely issue is missing header files for the libraries with native C 
components. See the contents of `Dockerfile` for the Linux packages that you'll need. On windows it's a bit more of a 
pain. Try using [WSL](https://docs.microsoft.com/en-us/windows/wsl/about) or finding a pre-compiled wheel from a 
trustworthy source.

### Frontend dependencies
*Devin please help.*

### Secrets and configuration
Packet supports 2 primary configuration methods:
1. Environment variables - See `config.env.py` for the expected names and default values.
2. Pyfile config - Create a `config.py` file in the root directory of the project and set variables to override the 
values in `config.env.py`.

Both methods can be used at the same time, though Pyfile config will take priority over environment variables.

**Required configuration values:**
* `SQLALCHEMY_DATABASE_URI` - Must be set to a valid [SQLAlchemy DB URI](http://flask-sqlalchemy.pocoo.org/2.3/config/#connection-uri-format). 
A dev database for the project is hosted by CSH. Contact a current maintainer of packet for the details.
* `LDAP_BIND_DN` - Must point to a valid CSH account on LDAP. Use the form 
`uid={username},cn=users,cn=accounts,dc=csh,dc=rit,dc=edu`.
* `LDAP_BIND_PASS` - The password for that CSH account.
* `SECRET_KEY` - Use a sufficiently long random string here. The `flask create-secret` command can generate a good one 
for you.
* `OIDC_CLIENT_SECRET` - Required to use CSH auth. Contact a current maintainer of packet for the details.

To switch between OIDC realms you'll need to set the modify the following values:
* `OIDC_CLIENT_SECRET` - Unique to each realm. Again, contact a current maintainer of packet for the details.
* `OIDC_ISSUER` - The OIDC issuer URL.
* `REALM` - Set to `"csh"` or `"intro"` depending on the realm you want.

By default `OIDC_ISSUER` and `REALM` are configured for the CSH members realm.

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
