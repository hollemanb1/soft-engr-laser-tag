#!/bin/bash

echo "Updating package lists..."
sudo apt update

# Install a specific package (e.g., htop)
echo "Installing python packages"
sudo apt install python python3 python3-pyqt5 python3-pyqt5.qtquick python3-pyqt5.qtsvg python3-psycopg2 \
postgresql python3-pil

echo "Starting PostgreSQL..."
sudo systemctl enable --now postgresql
until sudo -u postgres pg_isready -q; do sleep 1; done

echo "Setting up database (idempotent)..."
sudo -u postgres psql -v ON_ERROR_STOP=1 <<'SQL'
DO $$BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='student') THEN
    CREATE ROLE student LOGIN PASSWORD 'student';
  END IF;
END$$;
DO $$BEGIN
  IF NOT EXISTS (SELECT FROM pg_database WHERE datname='photon') THEN
    CREATE DATABASE photon OWNER student;
  END IF;
END$$;
SQL

sudo -u postgres psql -v ON_ERROR_STOP=1 -d photon <<'SQL'
CREATE TABLE IF NOT EXISTS players (
  id       INTEGER PRIMARY KEY,
  codename VARCHAR(255) NOT NULL
);
SQL


echo "Packages installed. Opening application..."
python3 main.py
