CREATE TABLE web_origins (
    client_id character varying(36) NOT NULL,
    value character varying(255)
);
INSERT INTO web_origins (client_id, value) VALUES (1,'z@datadoghq.com');
INSERT INTO web_origins (client_id, value) VALUES (3,'ziquan.miao@datadoghq.com');

create user datadog with password 'datadog';
grant SELECT ON pg_stat_database to datadog;

create user flask with password 'flask';
GRANT ALL PRIVILEGES ON TABLE web_origins TO flask;