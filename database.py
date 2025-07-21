import aiomysql
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

class Database:
    pool = None
    
    @classmethod
    async def create_pool(cls):
        # DATABASE_URL이 있으면 파싱해서 사용
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            # URL 파싱
            parsed = urlparse(database_url.replace('mysql+pymysql://', 'mysql://'))
            
            db_config = {
                'host': parsed.hostname,
                'port': parsed.port or 3306,
                'user': parsed.username,
                'password': parsed.password,
                'db': parsed.path.lstrip('/'),
                'charset': 'utf8',
                'autocommit': True,
                'minsize': 1,
                'maxsize': 10
            }
        else:
            # 개별 환경변수 사용
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 3306)),
                'user': os.getenv('DB_USER', 'root'),
                'password': os.getenv('DB_PASSWORD', ''),
                'db': os.getenv('DB_NAME', 'your_database'),
                'charset': 'utf8',
                'autocommit': True,
                'minsize': 1,
                'maxsize': 10
            }
        
        cls.pool = await aiomysql.create_pool(**db_config)
    
    @classmethod
    async def close_pool(cls):
        if cls.pool:
            cls.pool.close()
            await cls.pool.wait_closed()