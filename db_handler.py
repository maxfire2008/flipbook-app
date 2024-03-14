import uuid

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

Base = sqlalchemy.ext.declarative.declarative_base()


class Video(Base):
    __tablename__ = "videos"

    id = sqlalchemy.Column(
        sqlalchemy.UUID, primary_key=True, default=uuid.uuid4, unique=True
    )
    file_path = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    created = sqlalchemy.Column(
        sqlalchemy.DateTime, nullable=False, default=sqlalchemy.func.now()
    )


class PDFJob(Base):
    __tablename__ = "pdf_jobs"

    id = sqlalchemy.Column(
        sqlalchemy.UUID, primary_key=True, default=uuid.uuid4, unique=True
    )
    video_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("videos.id"))
    pdf_path = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    options = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    status = sqlalchemy.Column(sqlalchemy.String, nullable=False, default="pending")
    error = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created = sqlalchemy.Column(
        sqlalchemy.DateTime, nullable=False, default=sqlalchemy.func.now()
    )
