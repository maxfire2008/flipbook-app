import sys
import pathlib
import tempfile
import json
import shutil
import subprocess
import fpdf


def extract_images(video_path: str | pathlib.Path, framerate: str) -> pathlib.Path:
    temp_images_path = pathlib.Path(tempfile.mkdtemp(prefix="video_to_flipbook"))
    temp_images_path.mkdir(parents=True, exist_ok=True)

    ffmpeg_process = subprocess.Popen(
        [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-r",
            str(framerate),
            str(temp_images_path) + "/%08d.jpeg",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        outs, errs = ffmpeg_process.communicate(timeout=15)
    except subprocess.TimeoutExpired as e:
        ffmpeg_process.kill()
        outs, errs = ffmpeg_process.communicate()
        print(outs)
        print(errs)

    return temp_images_path


def video_to_flipbook(video_path, pdf_path, options=None):
    if options == None:
        options = {}
    page_width = options.get("page_width", 210)
    page_height = options.get("page_height", 297)

    grid_width = options.get("grid_width", 2)
    grid_height = options.get("grid_height", 4)

    image_width = options.get("image_width", 80)
    image_height = options.get("image_height", 60)

    margin_left = options.get("margin_left", 20)
    margin_top = options.get("margin_top", 28)

    gap_between_x = options.get("gap_between_x", 10)
    gap_between_y = options.get("gap_between_y", 0)

    font_family = options.get("font_family", "Times")
    font_style = options.get("font_style", "")
    font_size = options.get("font_size", 8)

    frame_number_x_offset = options.get("frame_number_x_offset", -(gap_between_x * 0.9))
    frame_number_y_offset = options.get("frame_number_y_offset", image_height / 2)

    frame_order = options.get("frame_order", "vertical_first")
    framerate = options.get("framerate", "5")

    pdf = fpdf.FPDF(orientation="P", unit="mm", format=(page_width, page_height))
    pdf.set_font(font_family, font_style, font_size)

    images_path = extract_images(video_path, framerate)

    for i, image in enumerate(sorted(images_path.glob("*.jpeg"))):
        page_index = i % (grid_width * grid_height)
        if frame_order == "vertical_first":
            x_index = page_index // grid_height
            y_index = page_index % grid_height
        elif frame_order == "horizontal_first":
            x_index = page_index % grid_width
            y_index = page_index // grid_width

        x_position = (image_width + gap_between_x) * x_index + margin_left
        y_position = (image_height + gap_between_y) * y_index + margin_top

        if page_index == 0:
            pdf.add_page()

        pdf.text(
            x=x_position + frame_number_x_offset,
            y=y_position + frame_number_y_offset,
            txt=str(i),
        )
        pdf.image(str(image), x=x_position, y=y_position, w=image_width, h=image_height)

    pdf.output(pdf_path)

    shutil.rmtree(images_path)


if __name__ == "__main__":
    video_to_flipbook(sys.argv[1], sys.argv[2], options=json.loads(sys.argv[3]))
