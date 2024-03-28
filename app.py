import datetime
import os
import uuid
import yaml
import ipaddress

import flask
import flask_wtf
import flask_wtf.file
import wtforms
import wtforms.validators
import pathlib

import db_handler

app = flask.Flask(__name__)
app.jinja_env.autoescape = False

with open("config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)


app.secret_key = CONFIG["secret_key"]


VIDEO_STORE = pathlib.Path("videos")
PDF_STORE = pathlib.Path("pdfs")

VIDEO_STORE.mkdir(exist_ok=True)
PDF_STORE.mkdir(exist_ok=True)


class UploadFileForm(flask_wtf.FlaskForm):
    file = flask_wtf.file.FileField(
        "File (max. 200 MiB)",
        validators=[
            flask_wtf.file.FileRequired(),
            flask_wtf.file.FileSize(max_size=1024**2 * 200),
        ],
    )


class NewJobForm(flask_wtf.FlaskForm):
    video_id = wtforms.HiddenField("")
    page_width = wtforms.FloatField(
        "Page Width", default=210, validators=[wtforms.validators.NumberRange(min=0)]
    )
    page_height = wtforms.FloatField(
        "Page Height", default=297, validators=[wtforms.validators.NumberRange(min=0)]
    )
    grid_width = wtforms.FloatField(
        "Grid Width", default=2, validators=[wtforms.validators.NumberRange(min=0)]
    )
    grid_height = wtforms.FloatField(
        "Grid Height", default=4, validators=[wtforms.validators.NumberRange(min=0)]
    )
    image_width = wtforms.FloatField(
        "Image Width", default=80, validators=[wtforms.validators.NumberRange(min=0)]
    )
    image_height = wtforms.FloatField(
        "Image Height", default=60, validators=[wtforms.validators.NumberRange(min=0)]
    )
    margin_left = wtforms.FloatField(
        "Margin Left", default=20, validators=[wtforms.validators.NumberRange()]
    )
    margin_top = wtforms.FloatField(
        "Margin Top", default=28, validators=[wtforms.validators.NumberRange()]
    )
    gap_between_x = wtforms.FloatField(
        "Gap Between X", default=10, validators=[wtforms.validators.NumberRange()]
    )
    gap_between_y = wtforms.FloatField(
        "Gap Between Y", default=0, validators=[wtforms.validators.NumberRange()]
    )
    font_family = wtforms.StringField(
        "Font Family",
        default="Times",
        validators=[
            wtforms.validators.AnyOf(
                [
                    "Arial",
                    "Courier",
                    "Helvetica",
                    "Symbol",
                    "Times",
                    "ZapfDingbats",
                ]
            )
        ],
    )
    font_style = wtforms.StringField(
        "Font Style", default="", validators=[wtforms.validators.Regexp(r"^[BIU]*$")]
    )
    font_size = wtforms.FloatField(
        "Font Size", default=8, validators=[wtforms.validators.NumberRange(min=0)]
    )
    frame_number_x_offset = wtforms.FloatField(
        "Frame Number X Offset †",
        default=-9,
        validators=[wtforms.validators.NumberRange()],
    )
    frame_number_y_offset = wtforms.FloatField(
        "Frame Number Y Offset †",
        default=30,
        validators=[wtforms.validators.NumberRange()],
    )
    frame_order = wtforms.SelectField(
        "Frame Order",
        choices=[
            ("vertical_first", "Vertical First"),
            ("horizontal_first", "Horizontal First"),
        ],
        default="vertical_first",
    )
    framerate = wtforms.StringField(
        "Framerate",
        default="5",
        validators=[wtforms.validators.Regexp(r"^\d+(/\d+)?$")],
    )


def authenticate():
    with db_handler.Session() as session:
        token = flask.request.cookies.get("token", None)
        if token is not None:
            # search for token in database
            web_session = (
                session.query(db_handler.WebSession)
                .filter(db_handler.WebSession.token == token)
                .first()
            )
            print(
                f"{web_session!r} is not None and {web_session.expires!r} < {datetime.datetime.now()!r}"
            )
            print(
                f"{web_session is not None} and {web_session.expires < datetime.datetime.now()}"
            )
            if (
                web_session is not None
                and web_session.expires > datetime.datetime.now()
            ):
                current_domain = web_session.domain
            else:
                current_domain = None
        else:
            web_session = None
            current_domain = None

        remote_ip = flask.request.remote_addr
        if remote_ip in CONFIG["authorized_proxies"]:
            remote_ip = flask.request.headers.get("X-Forwarded-For", remote_ip)

        authorized_by = []
        for k, v in CONFIG["domains"].items():
            if ipaddress.ip_address(remote_ip) in ipaddress.ip_network(v):
                authorized_by.append(k)

        if len(authorized_by) > 0:
            if current_domain is not None and current_domain == ",".join(authorized_by):
                web_session.expires = datetime.datetime.now() + datetime.timedelta(
                    days=7
                )
                session.commit()
                return {
                    "domain": web_session.domain,
                    "expires": web_session.expires,
                    "on_network": True,
                }
            else:
                if current_domain is not None:
                    web_session.expires = datetime.datetime.now()

                new_session = db_handler.WebSession(domain=",".join(authorized_by))
                session.add(new_session)
                session.commit()

                return {
                    "domain": new_session.domain,
                    "expires": new_session.expires,
                    "token": new_session.token,
                    "on_network": True,
                }
        elif current_domain is not None:
            return {
                "domain": web_session.domain,
                "expires": web_session.expires,
            }


def authenticated(func):
    def wrap_authentication(*args, **kwargs):
        authentication = authenticate()
        print(authentication)
        if authentication:
            response = func(*args, **kwargs)
            if isinstance(response, str):
                flask_response = flask.make_response(response)
                
                if authentication.get("on_network"):
                    auth_text = f"Authorized by {authentication.get("domain")}"
                else:
                    auth_text = f"Your current authorization belongs to {authentication.get("domain")} and expires at {authentication.get("expires")}."

                flask_response.set_data(
                    flask_response.get_data().replace(
                        b"##authorization_message##", auth_text.encode()
                    )
                )

                if "token" in authentication:
                    flask_response.set_cookie("token", authentication["token"])
                return flask_response
            else:
                return response
        else:
            return "403 NOT AUTHORIZED", 403
    
    wrap_authentication.__name__ = func.__name__

    return wrap_authentication


@app.route("/")
@authenticated
def upload_file():
    return flask.render_template("upload_file.html.j2", form=UploadFileForm())


@app.route("/submit_file", methods=["POST"])
@authenticated
def submit_file():
    form = UploadFileForm()
    if form.validate_on_submit():
        with db_handler.Session() as session:
            file_uuid = uuid.uuid4()
            video = db_handler.Video(
                id=file_uuid,
                path=str(
                    (
                        VIDEO_STORE
                        / (
                            file_uuid.hex
                            + "."
                            + "".join(
                                filter(
                                    lambda x: x
                                    in "0123456789abcdefghijklmnopqrstuvwxyz",
                                    form.file.data.filename.split(".")[-1].lower(),
                                )
                            )
                        )
                    ).absolute()
                ),
            )
            session.add(video)
            session.commit()

            video_path = video.path
            form.file.data.save(video_path)

            return flask.url_for("video_file", video_id=video.id.hex)

    return "Data is not valid: " + str(form.errors), 400


@app.route("/video/<path:video_id>")
@authenticated
def video_file(video_id):
    copy_id = flask.request.args.get("copy")

    form=NewJobForm(video_id=video_id)

    if copy_id:
        with db_handler.Session() as session:
            copy_options = session.query(db_handler.PDFJob).get(uuid.UUID(copy_id)).options

    return flask.render_template(
        "video.html.j2", video_id=video_id, form=form
    )


@app.route("/submit_job", methods=["POST"])
@authenticated
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
            "frame_number_x_offset": form.frame_number_x_offset.data,
            "frame_number_y_offset": form.frame_number_y_offset.data,
            "frame_order": form.frame_order.data,
            "framerate": form.framerate.data,
        }

        with db_handler.Session() as session:
            video = session.query(db_handler.Video).get(uuid.UUID(form.video_id.data))
            pdf_uuid = uuid.uuid4()
            pdf = db_handler.PDFJob(
                id=pdf_uuid,
                video_id=video.id,
                path=str((PDF_STORE / (pdf_uuid.hex + ".pdf")).absolute()),
                options=options,
            )
            session.add(pdf)
            session.commit()

            return flask.redirect(flask.url_for("job", pdf_id=pdf.id.hex))

    return flask.redirect(flask.url_for("video_file", video_id=form.video_id.data))


@app.route("/job/<path:pdf_id>")
@authenticated
def job(pdf_id):
    with db_handler.Session() as session:
        return flask.render_template(
            "job.html.j2",
            job=session.query(db_handler.PDFJob).get(uuid.UUID(pdf_id)),
        )

@app.route("/pdf/<path:pdf_id>")
@authenticated
def pdf_file(pdf_id):
    with db_handler.Session() as session:
        job = session.query(db_handler.PDFJob).get(uuid.UUID(pdf_id))
        return flask.send_file(
            job.path,
            as_attachment=flask.request.args.get("download", "false") == "true",
            download_name="flipbook_" + pdf_id + ".pdf",
        )
