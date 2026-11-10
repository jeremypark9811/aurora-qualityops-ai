from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, ForeignKey, UniqueConstraint, create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def now():
    return datetime.now(timezone.utc).isoformat()


class Source(Base):
    __tablename__ = 'source_records'
    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    row_number = Column(Integer, nullable=False)
    digest = Column(String, nullable=False)
    kind = Column(String, nullable=False)
    data = Column(JSON, nullable=False)
    __table_args__ = (UniqueConstraint('source', 'row_number'),)


class Claim(Base):
    __tablename__ = 'claims'
    id = Column(Integer, primary_key=True)
    customer_id = Column(String, nullable=False)
    product_id = Column(String, nullable=False)
    batch_id = Column(String, nullable=False, index=True)
    claim_type = Column(String, nullable=False)
    occurred_on = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    evidence_present = Column(Boolean, default=False)
    reporter = Column(String, nullable=False)
    status = Column(String, default='신규 접수')
    is_demo = Column(Boolean, default=False)
    created_at = Column(String, default=now)


class Analysis(Base):
    __tablename__ = 'analyses'
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey('claims.id'), index=True)
    result = Column(JSON, nullable=False)
    mode = Column(String, nullable=False)
    created_at = Column(String, default=now)


class Approval(Base):
    __tablename__ = 'approvals'
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey('claims.id'))
    analysis_id = Column(Integer, ForeignKey('analyses.id'), unique=True)
    action = Column(String, nullable=False)
    status = Column(String, default='대기')
    decided_by = Column(String)
    reason = Column(Text)
    decided_at = Column(String)
    created_at = Column(String, default=now)


class BatchState(Base):
    __tablename__ = 'batch_states'
    batch_id = Column(String, primary_key=True)
    status = Column(String, default='정상')
    shipment_hold = Column(Boolean, default=False)
    recall_approved = Column(Boolean, default=False)
    approval_id = Column(Integer, ForeignKey('approvals.id'))
    updated_at = Column(String, default=now)


class Task(Base):
    __tablename__ = 'department_tasks'
    id = Column(Integer, primary_key=True)
    dedupe_key = Column(String, unique=True, nullable=False)
    claim_id = Column(Integer, ForeignKey('claims.id'))
    batch_id = Column(String, index=True)
    department = Column(String, nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, default='대기')
    priority = Column(String, default='보통')
    details = Column(JSON, default=dict)
    reply = Column(JSON)
    created_at = Column(String, default=now)
    updated_at = Column(String, default=now)


class Evidence(Base):
    __tablename__ = 'evidence'
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey('claims.id'))
    kind = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    actor = Column(String, nullable=False)
    is_simulated = Column(Boolean, default=True)
    created_at = Column(String, default=now)


class Audit(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, index=True)
    batch_id = Column(String)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    before = Column(String)
    after = Column(String)
    reason = Column(Text, nullable=False)
    basis = Column(JSON, default=dict)
    task_id = Column(Integer)
    created_at = Column(String, default=now)


class Plan(Base):
    __tablename__ = 'recovery_plans'
    id = Column(Integer, primary_key=True)
    batch_id = Column(String, unique=True)
    claim_id = Column(Integer, ForeignKey('claims.id'))
    status = Column(String, default='생산 여력 확인 필요')
    data = Column(JSON, nullable=False)
    updated_at = Column(String, default=now)


class Setting(Base):
    __tablename__ = 'settings'
    key = Column(String, primary_key=True)
    data = Column(JSON, nullable=False)


def database(url):
    engine = create_engine(url, connect_args={'check_same_thread': False, 'timeout': 30} if url.startswith('sqlite') else {})
    if url.startswith('sqlite'):
        @event.listens_for(engine, 'connect')
        def sqlite_config(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA journal_mode=WAL')
    Base.metadata.create_all(engine)
    if url.startswith('sqlite'):
        with engine.begin() as connection:
            connection.exec_driver_sql("CREATE TRIGGER IF NOT EXISTS sources_no_update BEFORE UPDATE ON source_records BEGIN SELECT RAISE(ABORT, 'original snapshots are immutable'); END")
            connection.exec_driver_sql("CREATE TRIGGER IF NOT EXISTS sources_no_delete BEFORE DELETE ON source_records BEGIN SELECT RAISE(ABORT, 'original snapshots are immutable'); END")
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def serialize(obj):
    return {col.name: getattr(obj, col.name) for col in obj.__table__.columns}
