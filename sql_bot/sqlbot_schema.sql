-- sqlbot_schema.sql

-- Products table
CREATE TABLE IF NOT EXISTS products (
  id    SERIAL      PRIMARY KEY,
  name  TEXT        NOT NULL,
  price NUMERIC(10,2) NOT NULL
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
  id         SERIAL   PRIMARY KEY,
  product_id INT      NOT NULL
    REFERENCES products(id)
    ON DELETE CASCADE,
  quantity   INT      NOT NULL,
  order_date DATE     NOT NULL
);
