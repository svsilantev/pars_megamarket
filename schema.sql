BEGIN;

CREATE TABLE IF NOT EXISTS "categories" (
	"id"	SERIAL PRIMARY KEY,
	"user_name"	VARCHAR(255),
	"category_url"	VARCHAR(255),
	"category_name"	VARCHAR(255),
	"pages_loaded"	INTEGER,
	"load_time"	REAL,
	"load_date"	TIMESTAMP,
	"load_time_start"	TIMESTAMP,
	"load_time_end"	TIMESTAMP,
	"items_count"	INTEGER DEFAULT 0,
	"max_bonus_percent"	REAL
);

CREATE TABLE IF NOT EXISTS "products" (
	"id"	SERIAL PRIMARY KEY,
	"load_date"	TIMESTAMP,
	"category"	VARCHAR(255),
	"name"	VARCHAR(255),
	"merchant"	VARCHAR(255),
	"original_price"	REAL,
	"discounted_price"	REAL,
	"discount_percent"	REAL,
	"bonus_percent"	REAL,
	"bonus_amount"	REAL,
	"final_price"	REAL,
	"rating"	REAL,
	"reviews_count"	INTEGER,
	"product_link"	VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS "temp_products" (
	"load_date"	TIMESTAMP,
	"category"	VARCHAR(255),
	"name"	VARCHAR(255),
	"merchant"	VARCHAR(255),
	"original_price"	REAL,
	"discounted_price"	REAL,
	"discount_percent"	REAL,
	"bonus_percent"	REAL,
	"bonus_amount"	REAL,
	"final_price"	REAL,
	"rating"	REAL,
	"reviews_count"	INTEGER,
	"product_link"	VARCHAR(255)
);

COMMIT;
