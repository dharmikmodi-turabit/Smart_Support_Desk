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




CREATE TABLE customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(30) NOT NULL,
    customer_email VARCHAR(40) UNIQUE NOT NULL,
    customer_mobile_number VARCHAR(10) UNIQUE NOT NULL,
    customer_company_name VARCHAR(30),
    customer_city VARCHAR(30),
    customer_state VARCHAR(30),
    customer_country VARCHAR(30),
    customer_address VARCHAR(100)
);
INSERT INTO customer (
    customer_name,
    customer_email,
    customer_mobile_number,
    customer_company_name,
    customer_city,
    customer_state,
    customer_country,
    customer_address
)
VALUES
('Rahul Sharma', 'rahul@gmail.com', '8888888881', 'TechSoft', 'Ahmedabad', 'Gujarat', 'India', 'CG Road'),
('Neha Patel', 'neha@gmail.com', '8888888882', 'FinCorp', 'Surat', 'Gujarat', 'India', 'Ring Road'),
('Amit Verma', 'amit@gmail.com', '8888888883', 'CloudNet', 'Mumbai', 'Maharashtra', 'India', 'Andheri East');

drop table customer;
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

CREATE TABLE employee (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_name VARCHAR(30) NOT NULL,
    employee_email VARCHAR(40) UNIQUE NOT NULL,
    employee_mobile_number VARCHAR(10) UNIQUE NOT NULL,
    employee_password VARCHAR(255) NOT NULL,
    employee_type INT NOT NULL,
    FOREIGN KEY (employee_type) REFERENCES employee_type(employee_type_id)
);
INSERT INTO employee (
    employee_name,
    employee_email,
    employee_mobile_number,
    employee_password,
    employee_type
)
VALUES
('Admin User', 'admin@gmail.com', '9999999991', 'admin123', 1),
('Agent One', 'agent1@gmail.com', '9999999992', 'agent123', 2),
('Agent Two', 'agent2@gmail.com', '9999999993', 'agent123', 2),
('Service Person A', 'service1@gmail.com', '9999999994', 'service123', 3),
('Service Person B', 'service2@gmail.com', '9999999995', 'service123', 3);
drop table employee;


CREATE TABLE ticket (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    issue_title VARCHAR(50) NOT NULL,
    issue_type VARCHAR(20) NOT NULL,
    issue_description VARCHAR(255),
    priority ENUM('High','Medium','Low') DEFAULT 'Medium',
    reason VARCHAR(50),
    generate_datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
    solve_datetime DATETIME,
    ticket_status ENUM('Open','In_Progress','Close') DEFAULT 'Open',

    service_person_emp_id INT,
    creater_emp_id INT NOT NULL,
    customer_id INT NOT NULL,

    FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    FOREIGN KEY (service_person_emp_id) REFERENCES employee(employee_id),
    FOREIGN KEY (creater_emp_id) REFERENCES employee(employee_id)
);
INSERT INTO ticket (
    issue_title,
    issue_type,
    issue_description,
    priority,
    reason,
    ticket_status,
    service_person_emp_id,
    creater_emp_id,
    customer_id
)
VALUES
(
    'Login not working',
    'Authentication',
    'User unable to login into system',
    'High',
    'Credentials error',
    'Open',
    4,   -- Service Person A
    2,   -- Agent One
    1
),
(
    'UI issue on dashboard',
    'Frontend',
    'Dashboard UI not loading properly',
    'Medium',
    'CSS issue',
    'In_Progress',
    5,   -- Service Person B
    3,   -- Agent Two
    2
),
(
    'Report download failed',
    'Backend',
    'PDF report download throwing error',
    'Low',
    'API timeout',
    'Close',
    4,
    2,
    3
);
INSERT INTO ticket (
    issue_title,
    issue_type,
    issue_description,
    priority,
    reason,
    ticket_status,
    service_person_emp_id,
    creater_emp_id,
    customer_id
)
VALUES
(
    'Email notifications not received',
    'Backend',
    'Customer not receiving ticket update emails',
    'Medium',
    'SMTP issue',
    'Open',
    4,
    2,
    1
),
(
    'Application crash on submit',
    'Backend',
    'App crashes when submitting support form',
    'High',
    'Null pointer exception',
    'In_Progress',
    5,
    3,
    2
),
(
    'Slow page loading',
    'Performance',
    'Dashboard takes too long to load',
    'Medium',
    'Heavy SQL query',
    'Open',
    4,
    2,
    3
),
(
    'Wrong data in report',
    'Data',
    'Generated report contains incorrect values',
    'High',
    'Data mapping issue',
    'In_Progress',
    5,
    3,
    1
),
(
    'Password reset email invalid',
    'Authentication',
    'Reset link expired immediately',
    'Low',
    'Token expiry issue',
    'Open',
    4,
    2,
    2
),
(
    'UI alignment issue',
    'Frontend',
    'Buttons overlap on mobile view',
    'Low',
    'CSS responsive issue',
    'Close',
    5,
    3,
    3
),
(
    'API returns 500 error',
    'Backend',
    'Internal server error on ticket creation',
    'High',
    'Unhandled exception',
    'In_Progress',
    4,
    2,
    1
),
(
    'Search not working',
    'Frontend',
    'Search bar returns no results',
    'Medium',
    'Index missing',
    'Open',
    5,
    3,
    2
),
(
    'File upload failed',
    'Backend',
    'Attachments not uploading',
    'High',
    'File size limit exceeded',
    'Open',
    4,
    2,
    3
),
(
    'Logout not clearing session',
    'Authentication',
    'User remains logged in after logout',
    'Medium',
    'Token not invalidated',
    'Close',
    5,
    3,
    1
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

CREATE TABLE ticket_message (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    sender_role ENUM('Customer','Agent','System') NOT NULL,
    sender_id INT NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES ticket(ticket_id)
);

