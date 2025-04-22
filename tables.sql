/*
Kyle, Joel, Gnandeep, Tom
CS314 Spring 2025
BMart Schema
*/

-- CONSTRAINT CHECK reference: https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html

DROP TABLE IF EXISTS order_contents;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS reorders_in_shipments;
DROP TABLE IF EXISTS reorder_requests;
DROP TABLE IF EXISTS shipments;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS product_type_relationship;
DROP TABLE IF EXISTS product_type;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS vendors;
DROP TABLE IF EXISTS store_hours;
DROP TABLE IF EXISTS stores;
DROP TABLE IF EXISTS customers;

USE cs314;

-- Table: customers
CREATE TABLE customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(15) NOT NULL UNIQUE, -- enough for country code + area code + phone number
    country VARCHAR(3) NOT NULL, -- using the international standard of 3 letter country codes
    state CHAR(2), -- using 2 letter state codes, can be null as not all countries have states
    city VARCHAR(50) NOT NULL,
    zip_postal_code CHAR(10) NOT NULL, -- CHAR to preserve leading zeros
    street VARCHAR(100) NOT NULL,
    building_num VARCHAR(10) NOT NULL, -- CHAR to preserve leading zeros
    apartment_num VARCHAR(5),
    
    -- CONSTRAINT CHECK
    CONSTRAINT CHK_customer_email CHECK (email LIKE '%@%.%') -- Check that emails are valid meaning they contain <email_user>@<email_service>.<com/edu/etc>
);

-- Table: stores
CREATE TABLE stores (
    store_id INT PRIMARY KEY AUTO_INCREMENT,
    country CHAR(3) NOT NULL, -- using the international standard of 3 letter country codes
    state CHAR(2), -- using 2 letter state codes, can be null as not all countries have states
    city VARCHAR(50) NOT NULL,
    zip_postal_code CHAR(10) NOT NULL, -- CHAR to preserve leading zeros
    street VARCHAR(100) NOT NULL,
    building_num VARCHAR(10) NOT NULL, -- CHAR to preserve leading zeros
    phone_number VARCHAR(15) NOT NULL UNIQUE -- enough for country code + area code + phone number
);

CREATE TABLE store_hours (
    store_id INT,
    day_of_week CHAR(3),
    open_time TIME,
    close_time TIME,
    PRIMARY KEY (store_id, day_of_week),
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    
    -- CONSTRAINT CHECK
    CONSTRAINT CHK_store_hours CHECK (open_time < close_time), -- Check that times are valid (open time is before close time)
    CONSTRAINT CHK_day_of_week CHECK (day_of_week IN ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')) -- Check that day is a valid day in the week
);

-- Table: vendors
CREATE TABLE vendors (
    vendor_name VARCHAR(60),
    brand_name VARCHAR(60),
    PRIMARY KEY (vendor_name, brand_name)
);

-- Table: products
CREATE TABLE products (
    product_UPC CHAR(12) PRIMARY KEY,
    product_name VARCHAR(30) NOT NULL,
    brand_name VARCHAR(60) NOT NULL,
    vendor_name VARCHAR(60) NOT NULL,
    source_nation VARCHAR(3) NOT NULL,
    standard_price DECIMAL(6,2) NOT NULL,
    FOREIGN KEY (vendor_name, brand_name) REFERENCES vendors(vendor_name, brand_name)
);

-- Table: product_type
CREATE TABLE product_type (
    type_id INT PRIMARY KEY AUTO_INCREMENT,
    type_name VARCHAR(40) NOT NULL UNIQUE
);

-- Table: product_type_relationship
-- Table to link products to product type since products can be of multiple types
CREATE TABLE product_type_relationship (
    product_UPC CHAR(12),
    type_id INT,
    PRIMARY KEY (product_UPC, type_id),
    FOREIGN KEY (product_UPC) REFERENCES products(product_UPC), -- link 'product_UPC' to the 'products' table
    FOREIGN KEY (type_id) REFERENCES product_type(type_id) -- link 'type_id' to the 'product_type' table
);

-- Table: inventory
CREATE TABLE inventory (
    product_price DECIMAL(6,2) NOT NULL, -- allows for product price of xxxx.xx
    max_inventory INT NOT NULL,
    current_inventory INT NOT NULL,
    product_UPC CHAR(12),
    store_id INT,
    PRIMARY KEY (product_UPC, store_id), -- Create a primary key using foreign keys to get the inventory of a specific product for a specific store
    FOREIGN KEY (product_UPC) REFERENCES products(product_UPC),
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    
    CONSTRAINT chk_inventory_size_within_max CHECK (
		current_inventory <= max_inventory -- Make sure we don't allow there to be a case where we hold more than we can for a product.
    )
);

-- Table: shipments
CREATE TABLE shipments (
    shipment_id INT PRIMARY KEY AUTO_INCREMENT,
    expected_delivery DATETIME NOT NULL,
    received_delivery DATETIME, -- can be null if hasn't been recieved yet
    expected_num_items SMALLINT NOT NULL,
    num_shipped_items SMALLINT, -- can be null if not shipped yet
    delivered BOOLEAN NOT NULL,
    store_id INT NOT NULL,
    vendor_name VARCHAR(60) NOT NULL,
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (vendor_name) REFERENCES vendors(vendor_name),
    
    -- CONSTRAINT CHECK
    CONSTRAINT chk_received_matches_delivered CHECK (
       (received_delivery IS NOT NULL AND delivered = TRUE) OR -- If there is a date for received_delivery then delivered = TRUE
       (received_delivery IS NULL AND delivered = FALSE) -- If there is no date for received_delivery then delivered = FALSE
    )
);

-- Table: reorder_requests
CREATE TABLE reorder_requests (
    reorder_id INT PRIMARY KEY AUTO_INCREMENT,
    quantity_of_product TINYINT UNSIGNED NULL,
    order_date DATETIME NOT NULL,
    confirmed BOOLEAN NOT NULL, -- track if a vendor has confirmed they have seen the order
    completed BOOLEAN NOT NULL, -- check if a reorder is still in progress or has been completed
    store_id INT NOT NULL,
    vendor_name VARCHAR(60) NOT NULL,
    product_ordered CHAR(12) NOT NULL,
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (vendor_name) REFERENCES vendors(vendor_name),
    FOREIGN KEY (product_ordered) REFERENCES products(product_UPC),
    
    -- CHECK CONSTRAINT
    CONSTRAINT CHK_quantity CHECK (quantity_of_product > 0) -- Make sure each reorder contains some products (can't reorder 0 products)
);

CREATE TABLE reorders_in_shipments (
    reorder_id INT,
    shipment_id INT,
    PRIMARY KEY (reorder_id, shipment_id),
    FOREIGN KEY (reorder_id) REFERENCES reorder_requests(reorder_id),
    FOREIGN KEY (shipment_id) REFERENCES  shipments(shipment_id)
);

-- Table: orders
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    order_datetime DATETIME NOT NULL,
    in_person_order BOOLEAN NOT NULL,
    online_order BOOLEAN NOT NULL,
    completed BOOLEAN NOT NULL,
    store_id INT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    
    -- CHECK CONSTRAINT
    CONSTRAINT CHK_online_or_inperson CHECK ((online_order = TRUE AND in_person_order = FALSE) OR (online_order = FALSE AND in_person_order = TRUE)), -- Ensure order is either online or in person, but not both
    CONSTRAINT CHK_inperson_completed CHECK ((in_person_order = TRUE and completed = TRUE) OR online_order = TRUE) -- If an order is in person, thn completed must be true
);

-- Table: order_contents
CREATE TABLE order_contents (
    order_id INT NOT NULL,
    product_ordered CHAR(12) NOT NULL,
    quantity_ordered INT NOT NULL,
    PRIMARY KEY (order_id, product_ordered),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_ordered) REFERENCES products(product_UPC),
    
    -- CONSTRAINT CHECK
    CONSTRAINT CHK_quantity_ordered CHECK (quantity_ordered > 0) -- Can't have an order with 0 quantity of product ordered
);
