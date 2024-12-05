CREATE TABLE IF NOT EXISTS read_heavy
(
    read_name varchar(50) not null
);

CREATE TABLE IF NOT EXISTS write_heavy
(
    write_id   int not null,
    write_name varchar(50) not null
);