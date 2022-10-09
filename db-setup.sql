alter user postgres passsword 'postgres';
create database sspdim;
\c sspdim;
drop table userinfo;
drop table servers;

create table userinfo(username varchar primary key, password varchar(256));
create table servers(ip_address varchar primary key, domain_name varchar, status varchar);
create table tokens(token varchar primary key, username varchar);
create table pending_friend_requests(from_username varchar, to_username varchar, primary key (from_username, to_username));
create table pending_messages(from_username varchar, to_username varchar, message_content varchar, message_id varchar, primary key (from_username, to_username, message_id));

insert into servers values('35.209.49.77', 'none', 'active');