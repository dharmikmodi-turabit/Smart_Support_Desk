create database smart_support_desk;
use smart_support_desk;

create Table team_leader(
	team_leader_id int auto_increment primary key,
    team_leader_name varchar(30),
    team_leader_email varchar(40) unique key,
    team_leader_mobile_number varchar(10) unique key,
    team_leader_password varchar(20)
);

create table agent(
	agent_id int auto_increment primary key,
    agent_name varchar(30),
    agent_email varchar(40) unique key,
    agent_mobile_number varchar(10) unique key,
    agent_password varchar(20),
    agent_ticket_count int,
    agent_rating int
);

create table service_person(
	service_person_id int auto_increment primary key,
    service_person_name varchar(30),
    service_person_email varchar(40) unique key,
    service_person_mobile_number varchar(10) unique key,
    service_person_password varchar(20),
    service_person_type varchar(20),
    service_person_rating int,
    service_person_city varchar(30),
    service_person_state varchar(30),
	service_person_country varchar(30),
	service_person_address varchar(100)
);

create Table customer(
	customer_id int auto_increment primary key,
    customer_name varchar(30),
    customer_email varchar(40) unique key,
    customer_mobile_number varchar(10) unique key,
    customer_company_name varchar(30),
    customer_city varchar(30),
    customer_state varchar(30),
    customer_country varchar(30),
    customer_address varchar(100)
);

create table ticket(
	ticket_id int auto_increment primary key,
    issue_title varchar(30),
    issue_type varchar(20),
    issue_description varchar(100),
    priority enum("High","Medium","Low"),
    reason varchar(50),
    generate_datetime datetime,
    solve_datetime datetime,
    agent_id int,
    customer_id int,
    service_person_id int,
    foreign key (agent_id) references agent(agent_id),
    foreign key (customer_id) references customer(customer_id),
    foreign key (service_person_id) references service_person(service_person_id)
);
alter table ticket modify column ticket_status enum("Open","In_Progress","Close");

create table ticket_log(
	ticket_log_id int auto_increment primary key,
    ticket_id int,
    ticket_status enum("Open","In Progress","Close"),
    ticket_log_datetime datetime,
    update_person_type varchar(20),
    update_person_id int,
    foreign key (ticket_id) references ticket(ticket_id)
);
alter table ticket_log modify column ticket_status enum("Open","In_Progress","Close");

-- create procedure
-- create trigger ticket_create_trigger
-- after insert on ticket
-- for each row 
-- begin
-- end;