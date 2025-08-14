"""
Test API endpoints for verifying connections to backend services.
"""
import psycopg2
from fastapi import APIRouter, HTTPException
from core.common.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
from core.common.logger import logger

router = APIRouter(prefix="/test", tags=["test"])

@router.get("/health")
async def backend_health():
    """Simple backend API health check."""
    try:
        return {
            "status": "success",
            "message": "Backend API is running",
            "service": "ggbots-api",
            "timestamp": "2025-08-14"
        }
    except Exception as e:
        logger.error(f"Backend health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Backend health check failed: {str(e)}")

@router.get("/ggbot-db")
async def test_ggbot_postgres():
    """Test connection to main GGBot PostgreSQL database."""
    try:
        # Connect to main ggbot database
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        
        with conn.cursor() as cur:
            # Simple test query
            cur.execute("SELECT current_database(), current_user, version();")
            result = cur.fetchone()
            
            # Get table count
            cur.execute("""
                SELECT count(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            table_count = cur.fetchone()[0]
            
        conn.close()
        
        return {
            "status": "success",
            "message": "GGBot PostgreSQL connection successful",
            "database": result[0],
            "user": result[1],
            "postgres_version": result[2],
            "table_count": table_count,
            "connection_info": {
                "host": DB_HOST,
                "port": DB_PORT,
                "database": DB_NAME
            }
        }
        
    except Exception as e:
        logger.error(f"GGBot PostgreSQL connection failed: {e}")
        raise HTTPException(status_code=500, detail=f"GGBot PostgreSQL connection failed: {str(e)}")

@router.get("/hummingbot-db")
async def test_hummingbot_postgres():
    """Test connection to Hummingbot PostgreSQL database."""
    try:
        # Connect to hummingbot database (different port from docker-compose)
        conn = psycopg2.connect(
            dbname="hummingbot_db",
            user=DB_USER,  # Same user as main DB
            password=DB_PASS,  # Same password as main DB
            host=DB_HOST,  # Same host (localhost in production)
            port="5433"  # Actual port for hummingbot container
        )
        
        with conn.cursor() as cur:
            # Simple test query
            cur.execute("SELECT current_database(), current_user, version();")
            result = cur.fetchone()
            
            # Get table count
            cur.execute("""
                SELECT count(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            table_count = cur.fetchone()[0]
            
        conn.close()
        
        return {
            "status": "success",
            "message": "Hummingbot PostgreSQL connection successful",
            "database": result[0],
            "user": result[1],
            "postgres_version": result[2],
            "table_count": table_count,
            "connection_info": {
                "host": DB_HOST,
                "port": "5433",
                "database": "hummingbot_db"
            }
        }
        
    except Exception as e:
        logger.error(f"Hummingbot PostgreSQL connection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Hummingbot PostgreSQL connection failed: {str(e)}")