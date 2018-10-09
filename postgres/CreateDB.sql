CREATE TABLE web_origins (
    client_id character varying(36) NOT NULL,
    value character varying(255)
);

CREATE TABLE customer(
    id BIGINT PRIMARY KEY     NOT NULL,
    firstname VARCHAR(20),
    lastname VARCHAR(20)
);

INSERT INTO customer (id, firstname, lastname) VALUES (100,'ziquan','miao');
INSERT INTO customer (id, firstname, lastname) VALUES (1111,'johnny','appleseed');
INSERT INTO customer (id, firstname, lastname) VALUES (101251510,'ten','elevent');
INSERT INTO customer (id, firstname, lastname) VALUES (1012312310,'12','13');

INSERT INTO web_origins (client_id, value) VALUES (1,'z@datadoghq.com');
INSERT INTO web_origins (client_id, value) VALUES (3,'ziquan.miao@datadoghq.com');

create user datadog with password 'datadog';
grant SELECT ON pg_stat_database to datadog;

create user flask with password 'flask';
GRANT ALL PRIVILEGES ON TABLE web_origins TO flask;

create user springboot with password 'springboot';
GRANT ALL PRIVILEGES ON TABLE customer TO springboot;