# openprocurement.buildout
Development Buildout of OpenProcurement

Follow the instructions:
  1. Copy `buildout.cfg.example` to `buildout.cfg` including all required items. For example:
  `buildout.cfg` for **development**:
  ```
  [buildout]
  extends =
      profiles/development.cfg

  [openprocurement.api.ini]
  couchdb_db = test
  ```

  2. Bootstrap the buildout with Python 2.7:

     ```
     $ python bootstrap.py
     ```

  3. Build the buildout:

      ```
      $ bin/buildout -N
      ```

System requirements (fedora 22):

    dnf install gcc file git libevent-devel python-devel sqlite-devel zeromq-devel libffi-devel openssl-devel systemd-python

Local development environment also requires additional dependencies:

    dnf install couchdb

To start environment services:

    bin/circusd --daemon

To to run openprocurement.api instance:

    bin/pserve etc/openprocurement.api.ini
