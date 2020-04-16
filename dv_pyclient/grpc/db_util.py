# Contains a small set of functions to help translate types returned by db

postgres_type_code = {21: ['SMALLINT', 'Number'], 23: ['INTEGER', 'Number'], 20: ['BIGINT', 'Number'],
                      1700: ['DECIMAL', 'Number'], 700: ['REAL', 'Number'], 701: ['FLOAT', 'Number'],
                      16: ['BOOLEAN', 'Number'], 1042: ['CHAR', 'String'], 1043: ['VARCHAR', 'String'],
                      1082: ['DATE', 'Date'], 1114: ['TIMESTAMP', 'Date'], 1184: ['TIMESTAMPTZ', 'Date'],
                      25: ['TEXT', 'String']}
snowflake_type_code = {21: ['SMALLINT', 'Number'], 23: ['INTEGER', 'Number'], 20: ['BIGINT', 'Number'],
                       1700: ['DECIMAL', 'Number'], 700: ['REAL', 'Number'], 701: ['FLOAT', 'Number'],
                       16: ['BOOLEAN', 'Number'], 1042: ['CHAR', 'String'], 1043: ['VARCHAR', 'String'],
                       1082: ['DATE', 'Date'], 1114: ['TIMESTAMP', 'Date'], 1184: ['TIMESTAMPTZ', 'Date'],
                       25: ['TEXT', 'String']}


##
# Code to generate meta types to assist new database support,
# calling get_type_code_map(conn) print the type codes.
# statically we support postgres and snowflake. Master list generated
# from types supported by redshift.
#
##
supported_types = ["SMALLINT", "INTEGER", "BIGINT", "DECIMAL", "REAL", "FLOAT8", 'FLOAT', "BOOLEAN", "CHAR",
                   "VARCHAR", "DATE", "TIMESTAMP", "TIMESTAMPTZ", "TEXT"]
datavore_types = ["Number", "Number", "Number", "Number", "Number", "Number", "Number", "Number", "String",
                  "String", "Date", "Date", "Date", "String"]


def __create_type_table(namespace):
    ns = f'"{namespace}".' if namespace else ''
    return f'''CREATE TABLE {ns}"type_code_test"(
           c1 SMALLINT,
           c2 INTEGER,	
           c3 BIGINT,	
           c4 DECIMAL,	
           c5 REAL	,
           c6 FLOAT8,
           c7 FLOAT,
           c8 BOOLEAN,
           c9 CHAR,
           c10 VARCHAR,
           c11 DATE,
           c12 TIMESTAMP,
           c13 TIMESTAMPTZ,
           c14 TEXT
    )'''


def __drop_type_table(namespace):
    ns = f'"{namespace}".' if namespace else ''
    return f'''DROP TABLE {ns}"type_code_test"'''


def __type_table_name(namespace):
    ns = f'"{namespace}".' if namespace else ''
    return f'{ns}"type_code_test"'


def get_type_code_map(conn):
    c = conn.cursor()
    c.execute(__create_type_table(None))
    c.execute("select * from type_code_test")
    meta = [description for description in c.description]
    type_map = {}
    for t in zip(meta, supported_types, datavore_types):
        type_map[t[0].type_code] = [t[1], t[2]]
    c.execute(__drop_type_table(None))
    c.close()
    return type_map
