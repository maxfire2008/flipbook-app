import uuid
import os
import datetime

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

Base = sqlalchemy.ext.declarative.declarative_base()


class Video(Base):
    __tablename__ = "videos"

    id = sqlalchemy.Column(
        sqlalchemy.UUID, primary_key=True, default=uuid.uuid4, unique=True
    )
    path = sqlalchemy.Column(sqlalchemy.String)
    created = sqlalchemy.Column(
        sqlalchemy.DateTime, nullable=False, default=sqlalchemy.func.now()
    )


class PDFJob(Base):
    __tablename__ = "pdf_jobs"

    id = sqlalchemy.Column(
        sqlalchemy.UUID, primary_key=True, default=uuid.uuid4, unique=True
    )
    video_id = sqlalchemy.Column(sqlalchemy.UUID, sqlalchemy.ForeignKey("videos.id"))
    video = sqlalchemy.orm.relationship("Video")
    path = sqlalchemy.Column(sqlalchemy.String)
    options = sqlalchemy.Column(sqlalchemy.JSON, nullable=False)
    status = sqlalchemy.Column(sqlalchemy.String, nullable=False, default="pending")
    output = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created = sqlalchemy.Column(
        sqlalchemy.DateTime, nullable=False, default=sqlalchemy.func.now()
    )


class WebSession(Base):
    __tablename__ = "web_sessions"

    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True, unique=True
    )
    token = sqlalchemy.Column(
        sqlalchemy.String, nullable=False, default=os.urandom(128).hex()
    )
    domain = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    expires = sqlalchemy.Column(
        sqlalchemy.DateTime,
        nullable=False,
        default=datetime.datetime.now() + datetime.timedelta(days=7),
    )


engine = sqlalchemy.create_engine("sqlite:///db.sqlite3")
Session = sqlalchemy.orm.sessionmaker(bind=engine)

Base.metadata.create_all(engine)
