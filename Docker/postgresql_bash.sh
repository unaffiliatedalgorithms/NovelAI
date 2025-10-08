#!/bin/bash

dbdir=/book/database
# replace with your wifi subnet
subnet=192.168.1.0/24
# or the internet unsafe version
# subnet=0.0.0.0/0

mkdir -p $dbdir && chown -R postgres:postgres $dbdir
sudo -u postgres /usr/lib/postgresql/*/bin/initdb -D $dbdir
config_file=$(find /etc /var /usr -name "postgresql.conf" 2>/dev/null | head -n 1)
hba_file=$(find /etc /var /usr -name "pg_hba.conf" 2>/dev/null | head -n 1)
echo $config_file
sed -i "s|data_directory = .*|data_directory = '$dbdir'|" "$config_file"
sed -i "s/^#listen_addresses = 'localhost'/listen_addresses = '*'/" "$config_file"
echo "host all all $subnet trust" >> "$hba_file"

# Start the PostgreSQL service in the background
service postgresql start

# Wait for PostgreSQL to initialize
until pg_isready -q; do
  echo "Waiting for PostgreSQL to start..."
  sleep 2
done
sudo -u postgres psql -c "CREATE ROLE root WITH SUPERUSER CREATEDB CREATEROLE LOGIN;"
echo "PostgreSQL service started. Launching bash session..."

# Start an interactive bash shell
exec bash
