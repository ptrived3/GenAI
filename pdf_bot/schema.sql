DROP TABLE IF EXISTS order_items     CASCADE;
DROP TABLE IF EXISTS orders          CASCADE;
DROP TABLE IF EXISTS products        CASCADE;
DROP TABLE IF EXISTS document_chunks CASCADE;

-- schema.sql
CREATE TABLE products (
  product_id   SERIAL PRIMARY KEY,
  name         TEXT NOT NULL,
  price        NUMERIC(10,2) NOT NULL
);

CREATE TABLE orders (
  order_id     SERIAL PRIMARY KEY,
  customer     TEXT NOT NULL,
  order_date   DATE DEFAULT CURRENT_DATE
);

CREATE TABLE order_items (
  order_item_id SERIAL PRIMARY KEY,
  order_id      INT REFERENCES orders(order_id),
  product_id    INT REFERENCES products(product_id),
  quantity      INT NOT NULL
);

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
  id        SERIAL PRIMARY KEY,
  content   TEXT     NOT NULL,
  metadata  JSONB    NOT NULL,
  embedding VECTOR(1024) NOT NULL
);
