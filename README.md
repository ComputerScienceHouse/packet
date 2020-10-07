# CSH Web Packet

[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Build Status](https://travis-ci.com/ComputerScienceHouse/packet.svg?branch=develop)](https://travis-ci.com/ComputerScienceHouse/packet)

Packet is used by CSH to facilitate the freshmen packet portion of our introductory member evaluation process. This is 
the second major iteration of packet on the web. The first version was 
[Tal packet](https://github.com/TalCohen/CSHWebPacket).

## Setup
**Requires Python 3.7 or newer.**

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
To build any of the frontend dependencies you're going to need [node](https://nodejs.org/), 
[npm](https://www.npmjs.com/get-npm), and [yarn](https://yarnpkg.com/).

Make sure your system is also capable of building with [Sass](https://sass-lang.com/). To download all node 
dependencies run.
```bash
yarn install
```

Following the install, you should be able to run `gulp`
```bash
gulp production
```

If it doesn't work for some reason, you may have to globally install gulp through npm
```bash
npm install -g gulp
```

### Local Development
* PostgreSQL
You'll need a postgres instance to use as a development DB.
You can use an existing database, like the instance used for the dev branch, use a database on another server, or spin up a container using docker or podman. 
To get setup using docker, run
```bash
docker run --name packet-postgres -e POSTGRES_PASSWORD=mysecretpassword -d -p 5432:5432 postgres
```
After the container starts up, you should be able to connect with the connection string `postgresql://postgres:mysecretpassword@localhost:5432/postgres`, which is the default connection string in `config.env.py`.
Once the container is up, run the following to set up the database tables.
```bash
flask db upgrade
```

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

## Usage
To run packet using the flask dev server use this command:
```bash
python3 wsgi.py
```
The Flask debug mode flag can be set using via the config system explained above.

Alternative you can run it through [gunicorn](https://gunicorn.org/) using this command:
```bash
gunicorn -b :8000 packet:app --access-logfile -
```

### CLI
Packet makes use of the Flask CLI for exposing functionality to devs and admins. This is primarily designed to be used 
locally with the target DB set via the server's config values.

To use the CLI just set the project up as normal and then run the `flask` command in the project's root directory. 
It'll automatically load up the app and show you a list of available commands. For more details on a particular command 
use the help flag like this:
```bash
flask {command} --help
```

**WARNING:** Be sure to double check which DB you're pointed at when using one of the admin or DB commands.

All DB commands are from the `Flask-Migrate` library and are used to configure DB migrations through Alembic. See their 
docs [here](https://flask-migrate.readthedocs.io/en/latest/) for details. 

## Code standards
This project is configured to use Pylint. Commits will be pylinted by Travis CI and if the score drops your build will 
fail blocking you from merging. To make your life easier just run it before making a PR.

To run pylint use this command:
```bash
pylint --load-plugins  pylint_quotes packet/routes packet
```

All python files should have a top-level docstring explaining the contents of the file and complex functions should 
have docstrings explaining any non-obvious portions.
