import cv2
from fpdf import FPDF
from PIL import Image


def video_to_flipbook(video_path, pdf_path):
    # Create PDF object
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Read the video
    vidcap = cv2.VideoCapture(video_path)

    # Variables for page dimensions
    _, frame = vidcap.read()
    height, width, _ = frame.shape
    aspect_ratio = width / height
    page_width = 210  # A4 width in mm
    page_height = page_width / aspect_ratio

    # Loop through video frames
    success, image = vidcap.read()
    while success:
        Image.fromarray(image).save("temp_image.jpg")
        # Write frame to PDF
        pdf.add_page()
        pdf.image("temp_image.jpg", x=0, y=0, w=page_width)

        # Read next frame
        success, image = vidcap.read()

    # Save PDF
    pdf.output(pdf_path)


if __name__ == "__main__":
    video_file_path = "NGG.webm"  # Replace with the path to your video file
    pdf_output_path = "NGG.pdf"  # Replace with the desired output PDF path
    video_to_flipbook(video_file_path, pdf_output_path)
