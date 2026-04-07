/* SELECT * FROM pg_extension; */
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE sessions (
  session_id char(128) UNIQUE NOT NULL,
  atime timestamp NOT NULL default current_timestamp,
  data text
);
CREATE TABLE users (
  id UUID DEFAULT gen_random_uuid(),
  username varchar(255),
  salt char(34) DEFAULT gen_salt('md5'),
  password varchar(255) NULL,
  photo text NULL,
  CONSTRAINT pk PRIMARY KEY(id),
  CONSTRAINT firstkey UNIQUE (username)
);

INSERT INTO users (username) VALUES ('bob');
WITH x AS (
  SELECT username, salt FROM users WHERE username='bob')
UPDATE users set PASSWORD = crypt('pass', x.salt) from x where users.username = x.username;

/* UPDATE ... SET pswhash = crypt('new password', gen_salt('md5')); */
/* with x as (select username, salt from users where username='bob') update users set password = crypt('pass', x.salt) from x where users.username = x.username; */
/* with x as (select username, salt, password from users where username = 'bob') select username from x where crypt('pass', salt) = password; */

/*
CREATE FUNCTION add_salt_fct()
RETURNS trigger AS $$
BEGIN
  IF NEW.salt IS NULL OR NEW.salt = '' THEN
    NEW.salt := gen_salt('md5');
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER add_salt_trigger
  BEFORE INSERT ON users
  FOR EACH ROW
  EXECUTE PROCEDURE add_salt_fct();
*/
