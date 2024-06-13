#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE USER dev WITH SUPERUSER PASSWORD 'dev';
	CREATE DATABASE vm;
	ALTER DATABASE courses OWNER TO dev;
	GRANT ALL PRIVILEGES ON DATABASE courses TO dev;

	CREATE TABLE IF NOT EXISTS vm(
    uid uuid PRIMARY KEY NOT NULL,
    ram integer NOT NULL,
    cpu integer NOT NULL,
    token Character(8) NOT NULL
	);

	CREATE TABLE IF NOT EXISTS harddisk(
	  uid uuid PRIMARY KEY NOT NULL,
	  hard_disk_memory integer NOT NULL,
	  vm uuid REFERENCES vm (uid)
	)
EOSQL