#!/bin/sh
# Sourced by the official Postgres entry point only on a fresh data volume.
set -eu

role_password="$(cat /credentials/tracking/password)"
psql --username "$POSTGRES_USER" --dbname postgres --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_tracking --set database_name=gymarena_tracking --set role_password="$role_password" <<'SQL'
CREATE ROLE :"role_name" LOGIN PASSWORD :'role_password';
CREATE DATABASE :"database_name" OWNER :"role_name";
REVOKE ALL ON DATABASE :"database_name" FROM PUBLIC;
SQL
psql --username "$POSTGRES_USER" --dbname gymarena_tracking --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_tracking <<'SQL'
REVOKE ALL ON SCHEMA public FROM PUBLIC;
ALTER SCHEMA public OWNER TO :"role_name";
SET ROLE :"role_name";
\i /schemas/tracking.sql
SQL

role_password="$(cat /credentials/membership/password)"
psql --username "$POSTGRES_USER" --dbname postgres --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_membership --set database_name=gymarena_membership --set role_password="$role_password" <<'SQL'
CREATE ROLE :"role_name" LOGIN PASSWORD :'role_password';
CREATE DATABASE :"database_name" OWNER :"role_name";
REVOKE ALL ON DATABASE :"database_name" FROM PUBLIC;
SQL
psql --username "$POSTGRES_USER" --dbname gymarena_membership --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_membership <<'SQL'
REVOKE ALL ON SCHEMA public FROM PUBLIC;
ALTER SCHEMA public OWNER TO :"role_name";
SET ROLE :"role_name";
\i /schemas/membership.sql
SQL

role_password="$(cat /credentials/session/password)"
psql --username "$POSTGRES_USER" --dbname postgres --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_session --set database_name=gymarena_session --set role_password="$role_password" <<'SQL'
CREATE ROLE :"role_name" LOGIN PASSWORD :'role_password';
CREATE DATABASE :"database_name" OWNER :"role_name";
REVOKE ALL ON DATABASE :"database_name" FROM PUBLIC;
SQL
psql --username "$POSTGRES_USER" --dbname gymarena_session --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_session <<'SQL'
REVOKE ALL ON SCHEMA public FROM PUBLIC;
ALTER SCHEMA public OWNER TO :"role_name";
SET ROLE :"role_name";
\i /schemas/session.sql
SQL

role_password="$(cat /credentials/notification/password)"
psql --username "$POSTGRES_USER" --dbname postgres --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_notification --set database_name=gymarena_notification --set role_password="$role_password" <<'SQL'
CREATE ROLE :"role_name" LOGIN PASSWORD :'role_password';
CREATE DATABASE :"database_name" OWNER :"role_name";
REVOKE ALL ON DATABASE :"database_name" FROM PUBLIC;
SQL
psql --username "$POSTGRES_USER" --dbname gymarena_notification --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_notification <<'SQL'
REVOKE ALL ON SCHEMA public FROM PUBLIC;
ALTER SCHEMA public OWNER TO :"role_name";
SET ROLE :"role_name";
\i /schemas/notification.sql
SQL

role_password="$(cat /credentials/member/password)"
psql --username "$POSTGRES_USER" --dbname postgres --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_member --set database_name=gymarena_member --set role_password="$role_password" <<'SQL'
CREATE ROLE :"role_name" LOGIN PASSWORD :'role_password';
CREATE DATABASE :"database_name" OWNER :"role_name";
REVOKE ALL ON DATABASE :"database_name" FROM PUBLIC;
SQL
psql --username "$POSTGRES_USER" --dbname gymarena_member --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_member <<'SQL'
REVOKE ALL ON SCHEMA public FROM PUBLIC;
ALTER SCHEMA public OWNER TO :"role_name";
SET ROLE :"role_name";
\i /schemas/member.sql
SQL

role_password="$(cat /credentials/recognition/password)"
psql --username "$POSTGRES_USER" --dbname postgres --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_recognition --set database_name=gymarena_recognition --set role_password="$role_password" <<'SQL'
CREATE ROLE :"role_name" LOGIN PASSWORD :'role_password';
CREATE DATABASE :"database_name" OWNER :"role_name";
REVOKE ALL ON DATABASE :"database_name" FROM PUBLIC;
SQL
psql --username "$POSTGRES_USER" --dbname gymarena_recognition --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_recognition <<'SQL'
REVOKE ALL ON SCHEMA public FROM PUBLIC;
ALTER SCHEMA public OWNER TO :"role_name";
SET ROLE :"role_name";
\i /schemas/recognition.sql
SQL

role_password="$(cat /credentials/challenge/password)"
psql --username "$POSTGRES_USER" --dbname postgres --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_challenge --set database_name=gymarena_challenge --set role_password="$role_password" <<'SQL'
CREATE ROLE :"role_name" LOGIN PASSWORD :'role_password';
CREATE DATABASE :"database_name" OWNER :"role_name";
REVOKE ALL ON DATABASE :"database_name" FROM PUBLIC;
SQL
psql --username "$POSTGRES_USER" --dbname gymarena_challenge --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_challenge <<'SQL'
REVOKE ALL ON SCHEMA public FROM PUBLIC;
ALTER SCHEMA public OWNER TO :"role_name";
SET ROLE :"role_name";
\i /schemas/challenge.sql
SQL

role_password="$(cat /credentials/scoring/password)"
psql --username "$POSTGRES_USER" --dbname postgres --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_scoring --set database_name=gymarena_scoring --set role_password="$role_password" <<'SQL'
CREATE ROLE :"role_name" LOGIN PASSWORD :'role_password';
CREATE DATABASE :"database_name" OWNER :"role_name";
REVOKE ALL ON DATABASE :"database_name" FROM PUBLIC;
SQL
psql --username "$POSTGRES_USER" --dbname gymarena_scoring --set ON_ERROR_STOP=1 \
  --set role_name=gymarena_scoring <<'SQL'
REVOKE ALL ON SCHEMA public FROM PUBLIC;
ALTER SCHEMA public OWNER TO :"role_name";
SET ROLE :"role_name";
\i /schemas/scoring.sql
SQL

unset role_password
