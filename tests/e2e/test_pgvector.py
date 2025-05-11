import pytest
import psycopg2
import numpy as np
from psycopg2.extras import execute_values

@pytest.fixture
def db_connection():
    """Create a connection to the Postgres database"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="synapse",
            password="synapsepass",
            database="synapse"
        )
        yield conn
        conn.close()
    except Exception as e:
        pytest.skip(f"Could not connect to database: {str(e)}")

def test_pgvector_extension(db_connection):
    """Test that the pgvector extension is installed and working"""
    cursor = db_connection.cursor()
    
    try:
        # Check if vector extension is installed
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()
        assert result is not None, "pgvector extension is not installed"
        
        # Create a test table with vector column
        cursor.execute("DROP TABLE IF EXISTS test_vectors;")
        cursor.execute("CREATE TABLE test_vectors (id serial PRIMARY KEY, embedding vector(3));")
        
        # Insert some test vectors
        test_vectors = [
            (np.array([1.0, 2.0, 3.0]),),
            (np.array([4.0, 5.0, 6.0]),),
            (np.array([7.0, 8.0, 9.0]),)
        ]
        
        execute_values(
            cursor,
            "INSERT INTO test_vectors (embedding) VALUES %s",
            [(f"[{v[0][0]},{v[0][1]},{v[0][2]}]",) for v in test_vectors]
        )
        
        # Test vector operations
        cursor.execute("SELECT embedding <-> '[1,2,3]' AS distance FROM test_vectors ORDER BY distance LIMIT 1;")
        result = cursor.fetchone()
        assert result is not None, "Vector distance calculation failed"
        
        # Clean up
        cursor.execute("DROP TABLE test_vectors;")
        db_connection.commit()
        
    except Exception as e:
        db_connection.rollback()
        pytest.fail(f"pgvector test failed: {str(e)}")
    finally:
        cursor.close()