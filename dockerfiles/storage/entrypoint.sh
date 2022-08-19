#!/bin/bash 

/storage --hal.endpoint 10.5.0.12:8099 --kasse.endpoint https://10.5.0.11:8443 --db.host 10.5.0.20 --db.port 5432 --db.user wash --db.name wash --db.pass adm-pass-test --goose.dir /migration
