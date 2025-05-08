 -- Create database
CREATE DATABASE piscineds;

-- Connect to the database
\c piscineds

-- Create user with specified password
CREATE USER jaehwkim WITH PASSWORD 'mysecretpassword';

-- Grant all privileges on the database to the user
GRANT ALL PRIVILEGES ON DATABASE piscineds TO jaehwkim;