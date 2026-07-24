from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from neo4j import GraphDatabase

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()

class Neo4jExtension:
    def __init__(self):
        self.driver = None
        self.database = 'neo4j'

    def init_app(self, app):
        uri = app.config['NEO4J_URI']
        user = app.config['NEO4J_USER']
        password = app.config['NEO4J_PASSWORD']
        self.database = app.config['NEO4J_DATABASE']
        max_pool = app.config['NEO4J_MAX_POOL_SIZE']

        self.driver = GraphDatabase.driver(
            uri, auth=(user, password), max_connection_pool_size=max_pool
        )

        @app.teardown_appcontext
        def close_driver(exception):
            pass # Driver is managed application-wide, sessions are closed manually

    def get_session(self):
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized.")
        return self.driver.session(database=self.database)

    def close(self):
        if self.driver:
            self.driver.close()

neo4j_ext = Neo4jExtension()

def get_neo4j_session():
    return neo4j_ext.get_session()
