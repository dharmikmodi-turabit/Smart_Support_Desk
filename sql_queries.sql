create database smart_support_desk;
use smart_support_desk;

-- create Table team_leader(
-- 	team_leader_id int auto_increment primary key,
--     team_leader_name varchar(30),
--     team_leader_email varchar(40) unique key,
--     team_leader_mobile_number varchar(10) unique key,
--     team_leader_password varchar(20)
-- );
-- drop table team_leader;
-- create table agent(
-- 	agent_id int auto_increment primary key,
--     agent_name varchar(30),
--     agent_email varchar(40) unique key,
--     agent_mobile_number varchar(10) unique key,
--     agent_password varchar(20),
--     agent_ticket_count int,
--     agent_rating int
-- );
-- drop table agent;
-- create table service_person(
-- 	service_person_id int auto_increment primary key,
--     service_person_name varchar(30),
--     service_person_email varchar(40) unique key,
--     service_person_mobile_number varchar(10) unique key,
--     service_person_password varchar(20),
--     service_person_type varchar(20),
--     service_person_rating int,
--     service_person_city varchar(30),
--     service_person_state varchar(30),
-- 	service_person_country varchar(30),
-- 	service_person_address varchar(100)
-- );
-- drop table service_person;




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

-- create table ticket(
-- 	ticket_id int auto_increment primary key,
--     issue_title varchar(30),
--     issue_type varchar(20),
--     issue_description varchar(100),
--     priority enum("High","Medium","Low"),
--     reason varchar(50),
--     generate_datetime datetime,
--     solve_datetime datetime,
--     ticket_status enum("Open","In_Progress","Close"),
--     agent_id int,
--     customer_id int,
--     service_person_id int,
--     foreign key (agent_id) references agent(agent_id),
--     foreign key (customer_id) references customer(customer_id),
--     foreign key (service_person_id) references service_person(service_person_id)
-- );
-- alter table ticket modify column ticket_status enum("Open","In_Progress","Close");
-- drop table ticket;

drop table ticket_log;

create table employee_type(
	employee_type_id int auto_increment primary key,
    type_name varchar(20)
    );

create table employee(
	employee_id int auto_increment primary key,
    employee_name varchar(30),
    employee_email varchar(40) unique key,
    employee_mobile_number varchar(10) unique key,
    employee_password varchar(20),
    employee_type int,
    foreign key (employee_type) references employee_type(employee_type_id)
	);
drop table employee;


create table ticket(
	ticket_id int auto_increment primary key,
    issue_title varchar(30),
    issue_type varchar(20),
    issue_description varchar(100),
    priority enum("High","Medium","Low"),
    reason varchar(50),
    generate_datetime datetime,
    solve_datetime datetime,
    ticket_status enum("Open","In_Progress","Close"),
    service_person_emp_id int,
    creater_emp_id int,
    customer_id int,
    foreign key (customer_id) references customer(customer_id),
    foreign key (service_person_emp_id) references employee(employee_id),
    foreign key (creater_emp_id) references employee(employee_id)
);
drop table ticket;

CREATE TABLE ticket_log (
    ticket_log_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    old_ticket_status ENUM('Open','In_Progress','Close') NOT NULL,
    new_ticket_status ENUM('Open','In_Progress','Close') NOT NULL,
    old_priority enum("High","Medium","Low"),
    new_priority enum("High","Medium","Low"),
    ticket_log_datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
    employee_id INT NOT NULL,

    FOREIGN KEY (ticket_id) REFERENCES ticket(ticket_id),
    FOREIGN KEY (employee_id) REFERENCES employee(employee_id)
);

drop table ticket_log;

insert into employee_type(employee_type_id,type_name) values (1,"Admin"),(2,"Agent"),(3,"Service Person");


DELIMITER $$

CREATE TRIGGER ticket_before_update
BEFORE UPDATE ON ticket
FOR EACH ROW
BEGIN
    -- Only log if something important changed

        INSERT INTO ticket_log (
            ticket_id,
            new_ticket_status,
            old_ticket_status,
            new_priority,
            old_priority,
            employee_id
        )
        VALUES (
            NEW.ticket_id,
            NEW.ticket_status,
            OLD.ticket_status,
            NEW.priority,
            OLD.priority,
            NEW.service_person_emp_id
        );


    -- Auto set solve_datetime when ticket is closed
    IF NEW.ticket_status = 'Close' AND OLD.ticket_status <> 'Close' THEN
        SET NEW.solve_datetime = NOW();
    END IF;

END$$

DELIMITER ;

drop trigger ticket_before_update;

-- create procedure
-- create trigger ticket_create_trigger
-- after insert on ticket
-- for each row 
-- begin
-- end;