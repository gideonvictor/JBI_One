-- =========================================================
-- JBI DATABASE SETUP - V2 NORMALIZED SCHEMA
-- =========================================================

DROP DATABASE IF EXISTS db_jbi;
CREATE DATABASE db_jbi;
USE db_jbi;

-- =========================================================
-- LOOKUP / MASTER TABLES
-- =========================================================

CREATE TABLE engineer (
    engineer_id INT AUTO_INCREMENT PRIMARY KEY,
    engineer_name VARCHAR(255) NOT NULL,
    engineer_contact VARCHAR(255) NULL,
    engineer_phone VARCHAR(255) NULL,
    UNIQUE KEY uq_engineer_name (engineer_name)
);

CREATE TABLE accounts (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    account_name VARCHAR(255) NOT NULL,
    account_contact VARCHAR(255) NULL,
    account_phone VARCHAR(255) NULL,
    UNIQUE KEY uq_account_name (account_name)
);

CREATE TABLE contractor (
    contractor_id INT AUTO_INCREMENT PRIMARY KEY,
    contractor_name VARCHAR(255) NOT NULL,
    contractor_contact VARCHAR(255) NULL,
    contractor_phone VARCHAR(255) NULL,
    UNIQUE KEY uq_contractor_name (contractor_name)
);

CREATE TABLE sales (
    sales_id INT AUTO_INCREMENT PRIMARY KEY,
    sales_name VARCHAR(255) NOT NULL,
    sales_contact VARCHAR(255) NULL,
    sales_phone VARCHAR(255) NULL,
    UNIQUE KEY uq_sales_name (sales_name)
);

CREATE TABLE job_status (
    status_id INT AUTO_INCREMENT PRIMARY KEY,
    status_name VARCHAR(100) NOT NULL,
    UNIQUE KEY uq_status_name (status_name)
);

-- Optional if you want to normalize market too:
-- CREATE TABLE market (
--     market_id INT AUTO_INCREMENT PRIMARY KEY,
--     market_name VARCHAR(255) NOT NULL,
--     UNIQUE KEY uq_market_name (market_name)
-- );

-- =========================================================
-- MAIN JOB TABLE
-- =========================================================

CREATE TABLE jobs (
    job_id INT AUTO_INCREMENT PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    account_id INT NULL,
    primary_engineer_id INT NULL,
    reference_contact VARCHAR(255) NULL,
    phone_number VARCHAR(255) NULL,
    equipment_description VARCHAR(255) NULL,
    jbi_number VARCHAR(255) NULL,
    market VARCHAR(255) NULL,
    status_id INT NULL,
    contractor_id INT NULL,
    order_date DATE NULL,
    ship_date DATE NULL,
    complete VARCHAR(255) NULL,
    judy_task TEXT NULL,

    CONSTRAINT uq_jobs_jbi_number UNIQUE (jbi_number),

    CONSTRAINT fk_jobs_account
        FOREIGN KEY (account_id) REFERENCES accounts(account_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT fk_jobs_primary_engineer
        FOREIGN KEY (primary_engineer_id) REFERENCES engineer(engineer_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT fk_jobs_status
        FOREIGN KEY (status_id) REFERENCES job_status(status_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT fk_jobs_contractor
        FOREIGN KEY (contractor_id) REFERENCES contractor(contractor_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    KEY idx_jobs_account_id (account_id),
    KEY idx_jobs_primary_engineer_id (primary_engineer_id),
    KEY idx_jobs_status_id (status_id),
    KEY idx_jobs_contractor_id (contractor_id),
    KEY idx_jobs_order_date (order_date),
    KEY idx_jobs_ship_date (ship_date),
    KEY idx_jobs_project_name (project_name),
    KEY idx_jobs_market (market)
);

-- =========================================================
-- MANY-TO-MANY TABLES
-- =========================================================

CREATE TABLE job_engineer (
    auto_id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    engineer_id INT NOT NULL,

    CONSTRAINT fk_job_engineer_job
        FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_job_engineer_engineer
        FOREIGN KEY (engineer_id) REFERENCES engineer(engineer_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT uq_job_engineer UNIQUE (job_id, engineer_id),
    KEY idx_job_engineer_engineer_id (engineer_id)
);

CREATE TABLE jobs_sales (
    auto_id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    sales_id INT NOT NULL,
    job_percentage DECIMAL(18,9) NULL,

    CONSTRAINT fk_jobs_sales_job
        FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_jobs_sales_sales
        FOREIGN KEY (sales_id) REFERENCES sales(sales_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT uq_jobs_sales UNIQUE (job_id, sales_id),
    KEY idx_jobs_sales_sales_id (sales_id)
);

-- =========================================================
-- COMMISSION TABLES
-- =========================================================

CREATE TABLE jobs_commission (
    commission_id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    purchase_amount DECIMAL(18,9) NULL,
    commission_at_sale DECIMAL(18,9) NULL,
    commission_due_pct DECIMAL(18,9) NULL,
    commission_adjust DECIMAL(18,9) NULL,
    cause_of_adjustment VARCHAR(255) NULL,
    commission_net_due DECIMAL(18,9) NULL,
    notes TEXT NULL,
    final_commission DECIMAL(18,9) NULL,
    final_due DECIMAL(18,9) NULL,
    commission_due_1 DECIMAL(18,9) NULL,
    du1_date DATE NULL,

    CONSTRAINT fk_jobs_commission_job
        FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    KEY idx_jobs_commission_job_id (job_id)
);

CREATE TABLE jobs_commission_line (
    commission_line_id INT AUTO_INCREMENT PRIMARY KEY,
    commission_id INT NOT NULL,
    commission_amount DECIMAL(18,9) NULL,
    date_commission DATE NULL,

    CONSTRAINT fk_jobs_commission_line_commission
        FOREIGN KEY (commission_id) REFERENCES jobs_commission(commission_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    KEY idx_jobs_commission_line_commission_id (commission_id),
    KEY idx_jobs_commission_line_date_commission (date_commission)
);

-- =========================================================
-- OTHER JOB DETAIL TABLES
-- =========================================================

CREATE TABLE judy_task_line (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    flag_complete TINYINT NULL,
    task TEXT NULL,
    start_date DATE NULL,
    date DATE NULL,

    CONSTRAINT fk_judy_task_line_job
        FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    KEY idx_judy_task_line_job_id (job_id),
    KEY idx_judy_task_line_flag_complete (flag_complete),
    KEY idx_judy_task_line_start_date (start_date)
);

CREATE TABLE jobs_start_up (
    auto_id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    sales_id INT NOT NULL,
    job_start_up DECIMAL(18,9) NULL,
    job_start_up_date DATE NULL,

    CONSTRAINT fk_jobs_start_up_job
        FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_jobs_start_up_sales
        FOREIGN KEY (sales_id) REFERENCES sales(sales_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    KEY idx_jobs_start_up_job_id (job_id),
    KEY idx_jobs_start_up_sales_id (sales_id),
    KEY idx_jobs_start_up_date (job_start_up_date)
);

-- =========================================================
-- SEED DATA
-- =========================================================

INSERT INTO contractor (contractor_name)
VALUES ('Frito Lay');

INSERT INTO sales (sales_name)
VALUES ('Tarn Victor'),
       ('Jonathan Sanchez');

INSERT INTO job_status (status_name)
VALUES ('Open'),
       ('Shipped'),
       ('Complete'),
       ('Cancelled');

-- =========================================================
-- VIEWS
-- =========================================================

CREATE OR REPLACE VIEW commission_detail AS
SELECT
    j.job_id,
    j.project_name,
    j.jbi_number,
    jc.commission_id,
    jc.purchase_amount,
    jc.commission_at_sale,
    jc.commission_due_pct,
    jc.commission_adjust,
    jc.cause_of_adjustment,
    jc.commission_net_due,
    jc.notes,
    jc.final_commission,
    jc.final_due,
    jc.commission_due_1,
    jc.du1_date
FROM jobs j
JOIN jobs_commission jc
    ON j.job_id = jc.job_id;

CREATE OR REPLACE VIEW commission_detail_line AS
SELECT
    j.job_id,
    j.project_name,
    jc.commission_id,
    jcl.commission_line_id,
    jcl.commission_amount,
    jcl.date_commission
FROM jobs j
JOIN jobs_commission jc
    ON j.job_id = jc.job_id
JOIN jobs_commission_line jcl
    ON jc.commission_id = jcl.commission_id;

CREATE OR REPLACE VIEW jobs_detail AS
SELECT
    j.job_id,
    j.project_name,
    j.jbi_number,
    a.account_id,
    a.account_name,
    pe.engineer_id AS primary_engineer_id,
    pe.engineer_name AS primary_engineer_name,
    j.reference_contact,
    j.phone_number,
    j.equipment_description,
    j.market,
    js.status_id,
    js.status_name,
    c.contractor_id,
    c.contractor_name,
    j.order_date,
    j.ship_date,
    j.complete,
    j.judy_task
FROM jobs j
LEFT JOIN accounts a
    ON j.account_id = a.account_id
LEFT JOIN engineer pe
    ON j.primary_engineer_id = pe.engineer_id
LEFT JOIN job_status js
    ON j.status_id = js.status_id
LEFT JOIN contractor c
    ON j.contractor_id = c.contractor_id;

CREATE OR REPLACE VIEW engineer_detail AS
SELECT
    je.auto_id,
    j.job_id,
    j.project_name,
    e.engineer_id,
    e.engineer_name,
    e.engineer_contact,
    e.engineer_phone
FROM job_engineer je
JOIN jobs j
    ON je.job_id = j.job_id
JOIN engineer e
    ON je.engineer_id = e.engineer_id;

CREATE OR REPLACE VIEW sales_detail AS
SELECT
    js.auto_id,
    js.job_id,
    j.project_name,
    js.sales_id,
    s.sales_name,
    js.job_percentage,
    s.sales_contact,
    s.sales_phone
FROM jobs_sales js
JOIN jobs j
    ON js.job_id = j.job_id
JOIN sales s
    ON js.sales_id = s.sales_id;

CREATE OR REPLACE VIEW jobs_index AS
SELECT
    j.job_id,
    j.project_name,
    j.jbi_number,
    a.account_name AS account,
    j.market,
    c.contractor_name AS contractor,
    st.status_name AS status,
    COALESCE(jc.purchase_amount, 0.00000) AS purchase_amount,
    COALESCE(jc.commission_at_sale, 0.00000) AS commission_at_sale,
    ROUND(
        COALESCE(jc.commission_at_sale, 0.00000)
        - COALESCE(SUM(jcl.commission_amount), 0.00000),
        2
    ) AS commission_net_due,
    COALESCE(SUM(
        CASE
            WHEN jsu.job_start_up_date IS NOT NULL THEN jsu.job_start_up
            ELSE 0
        END
    ), 0.00000) AS start_up
FROM jobs j
LEFT JOIN accounts a
    ON j.account_id = a.account_id
LEFT JOIN contractor c
    ON j.contractor_id = c.contractor_id
LEFT JOIN job_status st
    ON j.status_id = st.status_id
LEFT JOIN jobs_commission jc
    ON j.job_id = jc.job_id
LEFT JOIN jobs_commission_line jcl
    ON jc.commission_id = jcl.commission_id
LEFT JOIN jobs_start_up jsu
    ON j.job_id = jsu.job_id
GROUP BY
    j.job_id,
    j.project_name,
    j.jbi_number,
    a.account_name,
    j.market,
    c.contractor_name,
    st.status_name,
    jc.purchase_amount,
    jc.commission_at_sale;

CREATE OR REPLACE VIEW job_summary_header AS
SELECT
    ROUND(COALESCE(SUM(purchase_amount), 0), 2) AS total_purchase_amount,
    ROUND(COALESCE(SUM(commission_at_sale), 0), 2) AS total_commission_at_sale,
    ROUND(COALESCE(SUM(commission_net_due), 0), 2) AS total_commission_net_due,
    ROUND(COALESCE(SUM(start_up), 0), 2) AS total_start_up
FROM jobs_index;