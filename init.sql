/* SELECT * FROM pg_extension; */
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS sessions (
  session_id CHAR(128) UNIQUE NOT NULL,
  atime TIMESTAMP NOT NULL default current_timestamp,
  data TEXT
);

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS tmp_id;

CREATE TABLE users (
  id UUID DEFAULT gen_random_uuid(),
  username VARCHAR(255),
  salt CHAR(34) DEFAULT gen_salt('md5'),
  password VARCHAR(255) NULL,
  photo TEXT NULL,
  CONSTRAINT users_pk PRIMARY KEY(id),
  CONSTRAINT users_name UNIQUE (username)
);

INSERT INTO users (username) VALUES ('bob');
WITH x AS (
  SELECT username, salt FROM users WHERE username='bob')
UPDATE users set PASSWORD = crypt('pass', x.salt) from x where users.username = x.username;

/* UPDATE ... SET pswhash = crypt('new password', gen_salt('md5')); */
/* with x as (select username, salt from users where username='bob') update users set password = crypt('pass', x.salt) from x where users.username = x.username; */
/* with x as (select username, salt, password from users where username = 'bob') select username from x where crypt('pass', salt) = password; */

DROP TABLE IF EXISTS courses;

CREATE TABLE courses (
  id BIGSERIAL,
  user_id UUID,
  user_username VARCHAR(255),
  created_date TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
  title VARCHAR(255),
  slug VARCHAR(255),
  tags VARCHAR(255) DEFAULT '',
  short_description VARCHAR(255) DEFAULT '',
  description TEXT NULL,
  photo_url VARCHAR(255) DEFAULT '',
  course_status SMALLINT DEFAULT 1,
  source SMALLINT DEFAULT 6,
  target SMALLINT DEFAULT 2,
  target_breadcrumb VARCHAR(255) DEFAULT '',
  CONSTRAINT courses_pk PRIMARY KEY(id)
);

CREATE TEMP TABLE tmp_id AS SELECT id FROM users WHERE username = 'bob';
INSERT INTO courses (title, slug, user_id, user_username, target, target_breadcrumb) VALUES
('example!', 'example', (SELECT id FROM tmp_id LIMIT 1), 'bob', 4, '569.578.879.4');

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
