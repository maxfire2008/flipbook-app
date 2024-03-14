import os

import flask
import flask_wtf
import flask_wtf.file
import wtforms
import wtforms.validators
import sqlalchemy
import pathlib

import db_handler

app = flask.Flask(__name__)
app.secret_key = os.urandom(128)
app.jinja_env.autoescape = False

engine = sqlalchemy.create_engine("sqlite:///db.sqlite3")
Session = sqlalchemy.orm.sessionmaker(bind=engine)

db_handler.Base.metadata.create_all(engine)

VIDEO_STORE = pathlib.Path("videos")
PDF_STORE = pathlib.Path("pdfs")

VIDEO_STORE.mkdir(exist_ok=True)
PDF_STORE.mkdir(exist_ok=True)


class UploadFileForm(flask_wtf.FlaskForm):
    file = flask_wtf.file.FileField(
        "File (max. 200 MB)",
        validators=[
            flask_wtf.file.FileRequired(),
            flask_wtf.file.FileSize(max_size=1024**3 * 200),
        ],
    )


class NewJobForm(flask_wtf.FlaskForm):
    file_id = wtforms.HiddenField("File ID")
    page_width = wtforms.IntegerField("Page Width", default=210)
    page_height = wtforms.IntegerField("Page Height", default=297)
    grid_width = wtforms.IntegerField("Grid Width", default=2)
    grid_height = wtforms.IntegerField("Grid Height", default=4)
    image_width = wtforms.IntegerField("Image Width", default=80)
    image_height = wtforms.IntegerField("Image Height", default=60)
    margin_left = wtforms.IntegerField("Margin Left", default=20)
    margin_top = wtforms.IntegerField("Margin Top", default=28)
    gap_between_x = wtforms.IntegerField("Gap Between X", default=10)
    gap_between_y = wtforms.IntegerField("Gap Between Y", default=0)
    font_family = wtforms.StringField("Font Family", default="Times")
    font_style = wtforms.StringField("Font Style", default="")
    font_size = wtforms.IntegerField("Font Size", default=8)
    frame_number_x_offset = wtforms.IntegerField("Frame Number X Offset †", default="")
    frame_number_y_offset = wtforms.IntegerField("Frame Number Y Offset †", default="")
    frame_order = wtforms.SelectField(
        "Frame Order",
        choices=[
            ("vertical_first", "Vertical First"),
            ("horizontal_first", "Horizontal First"),
        ],
        default="vertical_first",
    )
    framerate = wtforms.IntegerField("Framerate", default=5)


@app.route("/")
def upload_file():
    return flask.render_template("upload_file.html.j2", form=UploadFileForm())


@app.route("/submit_file", methods=["POST"])
def submit_file():
    form = UploadFileForm()
    if form.validate_on_submit():
        with Session() as session:
            video = db_handler.Video()
            session.add(video)
            session.commit()

            video_path = VIDEO_STORE / video.id.hex
            form.file.data.save(video_path)

            return flask.redirect(flask.url_for("video_file", video_id=video.id.hex))

    return "Data is not valid", 400


@app.route("/video/<path:video_id>")
def video_file(video_id):
    return flask.render_template("video.html.j2", video_id=video_id, form=NewJobForm())


@app.route("/submit_job", methods=["POST"])
def submit_job():
    form = NewJobForm()
    if form.validate_on_submit():
        options = {
            "page_width": form.page_width.data,
            "page_height": form.page_height.data,
            "grid_width": form.grid_width.data,
            "grid_height": form.grid_height.data,
            "image_width": form.image_width.data,
            "image_height": form.image_height.data,
            "margin_left": form.margin_left.data,
            "margin_top": form.margin_top.data,
            "gap_between_x": form.gap_between_x.data,
            "gap_between_y": form.gap_between_y.data,
            "font_family": form.font_family.data,
            "font_style": form.font_style.data,
            "font_size": form.font_size.data,
            "frame_order": form.frame_order.data,
            "framerate": form.framerate.data,
        }
        if form.frame_number_x_offset.data:
            options["frame_number_x_offset"] = form.frame_number_x_offset.data
        if form.frame_number_y_offset.data:
            options["frame_number_y_offset"] = form.frame_number_y_offset.data

    return flask.render_template("new_job.html.j2", form=form)
