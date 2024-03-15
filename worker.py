import datetime
import pathlib
import time

import db_handler
import video_to_flipbook


def do_job():
    # query for the next pending job
    with db_handler.Session() as session:
        job = (
            session.query(db_handler.PDFJob)
            .filter(db_handler.PDFJob.status == "pending")
            .order_by(db_handler.PDFJob.created)
            .first()
        )

        if job is None:
            return

        # mark the job as started
        job.status = "started"
        session.commit()

        video_path = job.video.path
        pdf_path = pathlib.Path(job.path)
        options = job.options

    video_to_flipbook.video_to_flipbook(video_path, pdf_path, options)

    # mark the job as finished
    with db_handler.Session() as session:
        job.status = "finished"
        session.commit()


def clear_old_files():
    with db_handler.Session() as session:
        videos = (
            session.query(db_handler.Video)
            .filter(
                db_handler.Video.created
                < (datetime.datetime.now() - datetime.timedelta(days=7))
            )
            .all()
        )
        for video in videos:
            video_path = pathlib.Path(video.path)
            video_path.unlink()

        jobs = (
            session.query(db_handler.PDFJob)
            .filter(
                db_handler.PDFJob.created
                < (datetime.datetime.now() - datetime.timedelta(days=7))
            )
            .all()
        )
        for job in jobs:
            pdf_path = pathlib.Path(job.path)
            pdf_path.unlink()
            job.pdf_path = None
            job.status = "deleted"


if __name__ == "__main__":
    while True:
        do_job()
        time.sleep(5)
