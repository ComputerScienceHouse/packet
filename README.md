# Packet
A flask app that provides an API for CSH's web packet. This is a remake of [@TalCohen](https://github.com/talcohen)'s original [WebPacket](https://github.com/TalCohen/CSHWebPacket).

## Setup

```
$ git clone https://github.com/ComputerScienceHouse/packet.git && cd packet
$ cp config.sample.py config.py

# update any config variables, you will need to supply the database string for your
# development database

# postgres db example
$ createdb packet
$ psql packet
> create role packet_db with login password 'secret';
> grant all privileges on database packet to packet_db;
> \q

# config.py
SQLALCHEMY_DATABASE_URI = 'postgresql://packet_db:secret@localhost/packet'
```

Now that your database access string is setup, install requirements and run migrations. Check `.python-version` for the current version of python being used. Pyenv is a good tool to manage multiple python versions.

```
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ flask db upgrade
```

Run the development server:

```
$ export FLASK_APP=<?>
$ flask run
```

