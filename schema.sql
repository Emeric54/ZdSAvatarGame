drop table if exists round;

create table round (
  id integer primary key autoincrement,
  pseudo text not null,
  score int not null,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
