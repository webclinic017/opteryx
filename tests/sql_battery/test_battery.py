"""
The best way to test a SQL engine is to throw queries at it.

We have two in-memory tables, one of natural satellite data and one of planet data.
These are both small to allow us to test the SQL engine quickly and is guaranteed to
be available whereever the tests are run.

These tests only test the shape of the response, more specific tests wil test values.
The point of these tests is that we can throw many variations of queries, such as
different whitespace and capitalization and ensure we get a sensible looking response.

We test the shape in this battery because if the shape isn't right, the response isn't
going to be right, and testing shape of an in-memory dataset is quick, we can test 100s
of queries in a few seconds.
"""
import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], "../.."))
import opteryx
import pytest
from opteryx.storage.adapters import DiskStorage
from opteryx.third_party.pyarrow_ops import head
import pyarrow

# fmt:off
STATEMENTS = [
        ("SELECT * FROM $satellites", 177, 8),
        ("SELECT * FROM $satellites;", 177, 8),
        ("SELECT * FROM $satellites\n;", 177, 8),
        ("select * from $satellites", 177, 8),
        ("Select * From $satellites", 177, 8),
        ("SELECT   *   FROM   $satellites", 177, 8),
        ("SELECT\n\t*\n  FROM\n\t$satellites", 177, 8),
        ("\n\n\n\tSELECT * FROM $satellites", 177, 8),
        ("SELECT * FROM $satellites WHERE name = 'Calypso'", 1, 8),
        ("SELECT * FROM $satellites WHERE `name` = 'Calypso'", 1, 8),
        ("select * from $satellites where name = 'Calypso'", 1, 8),
        ("SELECT * FROM $satellites WHERE name <> 'Calypso'", 176, 8),
        ("SELECT * FROM $satellites WHERE name = '********'", 0, 8),
        ("SELECT * FROM $satellites WHERE name LIKE '_a_y_s_'", 1, 8),
        ("SELECT * FROM $satellites WHERE name LIKE 'Cal%'", 4, 8),
        ("SELECT * FROM $satellites WHERE name like 'Cal%'", 4, 8),
        # Unknown problems with keywords in double quotes
        #("SELECT * FROM $satellites WHERE \"name\" = 'Calypso'", 1, 8),
        #("SELECT * FROM \"$satellites\" WHERE name = 'Calypso'", 1, 8),
        #("SELECT * FROM \"$satellites\" WHERE \"name\" = 'Calypso'", 1, 8),  
        ("SELECT * FROM $satellites WHERE `name` = 'Calypso'", 1, 8),
        ("SELECT * FROM `$satellites` WHERE name = 'Calypso'", 1, 8),
        ("SELECT * FROM `$satellites` WHERE `name` = 'Calypso'", 1, 8),  

        ("SELECT name, id, planetId FROM $satellites", 177, 3), 
        ("SELECT name, name FROM $satellites", 177, 2),
        ("SELECT name, id, name, id FROM $satellites", 177, 4),

        # Field aliases aren't supported yet
        #("SELECT name as Name FROM $satellites", 177, 3), 
        #("SELECT name as Name, id as Identifier FROM $satellites", 177, 3), 
        #("SELECT name as NAME FROM $satellites WHERE NAME = 'Calypso'", 177, 3), 
        #("SELECT name as NAME FROM $satellites GROUP BY NAME", 177, 3), 

        # functions aren't currently supported - more tests will be needed
        #("SELECT upper(name) as NAME, id as Identifier FROM $satellites", 177, 1), 

        # Joins aren't supported
        #("SELECT * FROM $satellites, $planets WHERE $planets.planetId = $satellites.planetId", 177, 1),  

        ("SELECT * FROM $satellites WHERE id = 5", 1, 8), 
        ("SELECT * FROM $satellites WHERE magnitude = 5.29", 1, 8),
        ("SELECT * FROM $satellites WHERE id = 5 AND magnitude = 5.29", 1, 8),
        ("SELECT * FROM $satellites WHERE id = 5 AND magnitude = 1", 0, 8),
        ("SELECT * FROM $satellites WHERE id = 5 AND name = 'Europa'", 1, 8),
        ("SELECT * FROM $satellites WHERE id = 5 OR name = 'Europa'", 1, 8),
        ("SELECT * FROM $satellites WHERE id = 5 OR name = 'Moon'", 2, 8),
        ("SELECT * FROM $satellites WHERE id BETWEEN 5 AND 8", 4, 8),
#       There appears to be a problem evaluating filters with a BETWEEN and an AND
#        ("SELECT * FROM $satellites WHERE name = 'Eurpoa' AND id BETWEEN 5 AND 8", 1, 8),
        ("SELECT * FROM $satellites WHERE id BETWEEN 5 AND 8 OR name = 'Moon'", 5, 8),
        ("SELECT * FROM $satellites WHERE id IN (5,6,7,8)", 4, 8),
        ("SELECT * FROM $satellites WHERE id IN (5,6,7,8) AND name = 'Europa'", 1, 8),
        ("SELECT * FROM $satellites WHERE id IN (5,6,7,8) OR name = 'Moon'", 5, 8),
        ("SELECT * FROM $satellites WHERE planetId = id", 1, 8),
        ("SELECT * FROM $satellites WHERE planetId > 8", 5, 8),
        ("SELECT * FROM $satellites WHERE planetId >= 8", 19, 8),
        ("SELECT * FROM $satellites WHERE planetId < 5", 3, 8),
        ("SELECT * FROM $satellites WHERE planetId <= 5", 70, 8),

        ("SELECT COUNT(*) FROM $satellites", 1, 1),
        ("SELECT count(*) FROM $satellites", 1, 1),
        ("SELECT COUNT (*) FROM $satellites", 1, 1),
        ("SELECT Count(*) FROM $satellites", 1, 1),
        ("SELECT COUNT(name) FROM $satellites", 1, 1),
        ("SELECT COUNT(*) FROM $satellites GROUP BY name", 177, 1),
        ("SELECT COUNT(*) FROM $satellites GROUP BY planetId", 7, 1),
        ("SELECT COUNT(*) FROM $satellites GROUP\nBY planetId", 7, 1),
        ("SELECT COUNT(*) FROM $satellites GROUP     BY planetId", 7, 1),
        ("SELECT COUNT(*), planetId FROM $satellites GROUP BY planetId", 7, 2),
        ("SELECT COUNT(*), planetId FROM $satellites WHERE planetId < 6 GROUP BY planetId", 3, 2),                
        ("SELECT COUNT(*), planetId FROM $satellites WHERE planetId <= 6 GROUP BY planetId", 4, 2),      
        ("SELECT COUNT(*), planetId FROM $satellites WHERE name LIKE 'Cal%' GROUP BY planetId", 3, 2),
        
        ("SELECT DISTINCT planetId FROM $satellites", 7, 1),
        ("SELECT * FROM $satellites LIMIT 50", 50, 8),
        ("SELECT * FROM $satellites OFFSET 150", 27, 8),
        ("SELECT * FROM $satellites LIMIT 50 OFFSET 150", 27, 8),
        ("SELECT * FROM $satellites LIMIT 50 OFFSET 170", 7, 8),
        ("SELECT * FROM $satellites ORDER BY name", 177, 8),

        ("SELECT MAX(planetId) FROM $satellites", 1, 1),
        ("SELECT MIN(planetId) FROM $satellites", 1, 1),
        ("SELECT SUM(planetId) FROM $satellites", 1, 1),
        ("SELECT MAX(id), planetId FROM $satellites GROUP BY planetId", 7, 2),
        ("SELECT MIN(id), planetId FROM $satellites GROUP BY planetId", 7, 2),
        ("SELECT SUM(id), planetId FROM $satellites GROUP BY planetId", 7, 2),
        ("SELECT MIN(id), MAX(id), SUM(planetId), planetId FROM $satellites GROUP BY planetId", 7, 4),

        ("SELECT BOOLEAN(planetId) FROM $satellites GROUP BY planetId", 177, 1),
        ("SELECT VARCHAR(planetId) FROM $satellites GROUP BY planetId", 177, 1),
        ("SELECT TIMESTAMP(planetId) FROM $satellites GROUP BY planetId", 177, 1),
        ("SELECT NUMERIC(planetId) FROM $satellites GROUP BY planetId", 177, 1),
        ("SELECT GET(name, 1) FROM $satellites GROUP BY planetId", 177, 1),

        ("SELECT planetId, Count(*) FROM $satellites group by planetId having count(*) > 5", 4, 2),

        ("SELECT * FROM $satellites order by name", 177, 8),
        ("SELECT * FROM $satellites order by name desc", 177, 8),
        ("SELECT name FROM $satellites order by name", 177, 1),
        ("SELECT * FROM $satellites order by magnitude, name", 177, 8)

    ]
    # fmt:on

@pytest.mark.parametrize(
    "statement, rows, columns", STATEMENTS    
)
def test_sql_battery(statement, rows, columns):
    """
    Test an assortment of statements
    """
    conn = opteryx.connect(reader=DiskStorage(), partition_scheme=None)
    cursor = conn.cursor()
    cursor.execute(statement)

    result = pyarrow.concat_tables(cursor._results)
    actual_rows, actual_columns = result.shape

    assert (
        rows == actual_rows
    ), f"Query returned {actual_rows} rows but {rows} were expected, {statement}, {head(result)}"
    assert (
        columns == actual_columns
    ), f"Query returned {actual_columns} cols but {columns} were expected, {statement}, {head(result)}"


if __name__ == "__main__":

    print(f"RUNNING BATTERY OF {len(STATEMENTS)} TESTS")
    for statement, rows, cols in STATEMENTS:
        print(statement)
        test_sql_battery(statement, rows, cols)