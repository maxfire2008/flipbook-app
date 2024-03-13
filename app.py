import os
import flask
import flask_wtf
import flask_wtf.file
import wtforms
import wtforms.validators

app = flask.Flask(__name__)
app.secret_key = os.urandom(128)
app.jinja_env.autoescape = False


class NewJobForm(flask_wtf.FlaskForm):
    file = flask_wtf.file.FileField(
        "File",
        validators=[
            flask_wtf.file.FileRequired(),
            flask_wtf.file.FileSize(max_size=1024**3 * 500),
        ],
    )
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
def new_job():
    return flask.render_template("new_job.html.j2", form=NewJobForm())


@app.route("/submit", methods=["POST"])
def submit_job():
    pass
