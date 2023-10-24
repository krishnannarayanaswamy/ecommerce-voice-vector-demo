USE ecommerce;

DROP TABLE IF EXISTS inventory_data;

CREATE TABLE IF NOT EXISTS inventory_data (
    item_code TEXT,
    item_name TEXT,
    full_description TEXT,
    price TEXT,
    stock TEXT,
    embedding_inventory vector<float, 1536>,
    PRIMARY KEY (item_code)
);


CREATE CUSTOM INDEX IF NOT EXISTS item_name_index ON inventory_data(item_name) USING 'org.apache.cassandra.index.sai.StorageAttachedIndex' WITH OPTIONS = { 
'index_analyzer': '{
	"tokenizer" : {"name" : "standard"},
	"filters" : [{"name" : "porterstem"}]
}'};

CREATE CUSTOM INDEX IF NOT EXISTS embedding_inventory_index ON inventory_data(embedding_inventory)
            USING 'org.apache.cassandra.index.sai.StorageAttachedIndex' WITH OPTIONS = { 'similarity_function': 'dot_product' };
