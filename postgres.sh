#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: ${0} [ip]"
    exit 1
fi

# postgresql
sudo apt-get install -y postgresql
sudo /etc/init.d/postgresql restart
sudo -u postgres bash -c "psql -c \"CREATE USER firmadyne WITH PASSWORD 'firmadyne';\""

# # postgresql DB for Full
# sudo -u postgres createdb -O firmadyne firmware_full
# sudo -u postgres psql -d firmware_full < FirmAE/database/schema

# postgresql DB for FirmAFL
sudo -u postgres createdb -O firmadyne firmware_firmafl
sudo -u postgres psql -d firmware_firmafl < FirmAE/database/schema

# # postgresql DB for EQUAFL
# sudo -u postgres createdb -O firmadyne firmware_equafl
# sudo -u postgres psql -d firmware_equafl < FirmAE/database/schema

# # postgresql DB for Full (NEW)
# sudo -u postgres createdb -O firmadyne firmware_new_full
# sudo -u postgres psql -d firmware_new_full < FirmAE/database/schema

# # postgresql DB for FirmAFL (NEW)
# sudo -u postgres createdb -O firmadyne firmware_new_firmafl
# sudo -u postgres psql -d firmware_new_firmafl < FirmAE/database/schema

# # postgresql DB for EQUAFL (NEW)
# sudo -u postgres createdb -O firmadyne firmware_new_equafl
# sudo -u postgres psql -d firmware_new_equafl < FirmAE/database/schema

echo "listen_addresses = '${1},127.0.0.1,localhost'" | sudo -u postgres tee --append /etc/postgresql/*/main/postgresql.conf
sudo sed -i "s/port = 5432/port = 6666/gi" /etc/postgresql/*/main/postgresql.conf
sudo sed -i "s/port = 5433/port = 6666/gi" /etc/postgresql/*/main/postgresql.conf
echo "host all all ${1}/24 trust" | sudo -u postgres tee --append /etc/postgresql/*/main/pg_hba.conf
