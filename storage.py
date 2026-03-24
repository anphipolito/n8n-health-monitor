from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey,Enum
from sqlalchemy.orm import DeclarativeBase, Session
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
class Base(DeclarativeBase):
    pass    
class WorkflowScan(Base):
    __tablename__ = 'workflow_scans'
    id = Column(Integer, primary_key=True)
    workflow_id = Column(String, nullable=False)
    run_at = Column(DateTime, default=datetime.utcnow)
    workflow_name = Column(String, nullable=False)
    health_score = Column(Float, nullable=False)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    environment = Column(String, nullable=False)

class WorkflowIssue(Base):
    __tablename__ = 'workflow_issues'
    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey('workflow_scans.id'), nullable=False)
    workflow_id = Column(String, nullable=False)
    rule_name = Column(String, nullable=False)
    severity = Column(Enum('high', 'medium', 'low', name='issue_severity'), nullable=False)
    status = Column(Enum('active', 'resolved', name='issue_status'), default='active')
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

def init_db():
    db_url = os.getenv('DATABASE_URL')
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine

