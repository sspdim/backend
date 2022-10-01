alter user postgres passsword 'postgres';
create database sspdim;
\c sspdim;
drop table userinfo;
drop table servers;
create table userinfo(username varchar primary key, password varchar(256));
create table servers(ip_address varchar primary key, domain_name varchar, status active);
insert into servers values('35.209.49.77', 'none', 'active');