-- Run as a PostgreSQL superuser after updating credentials in backend/.env
-- Example:
--   psql -U postgres -f scripts/init_database.sql

CREATE DATABASE mib_rag_chatbot;

\connect mib_rag_chatbot

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
