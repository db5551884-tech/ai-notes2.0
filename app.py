from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file
import io
import pdfplumber
from docx import Document
from pptx import Presentation
model = genai.GenerativeModel("gemini-2.5-flash")
import openai
from pptx import Presentation
from reportlab.pdfgen import canvas
from flask import send_file
import io
import pdfplumber
from flask import Flask, render_template, request
import PyPDF2
import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("API_KEY"))

app = Flask(__name__)


def summarize(text):

    prompt = f"""
Зроби:

1. Короткий конспект у вигляді пунктів
2. 5 тестових питань по тексту

Текст:
{text}
"""

    response = model.generate_content(prompt)

    return response.text.replace("\n", "<br>")


def extract_text(file):

    filename = file.filename

    if filename.endswith(".pdf"):
        import pdfplumber
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    elif filename.endswith(".docx"):
        from docx import Document
        doc = Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

    elif filename.endswith(".pptx"):
        from pptx import Presentation
        ppt = Presentation(file)
        text = ""
        for slide in ppt.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text

    return ""

@app.route("/", methods=["GET", "POST"])
def index():
    global lecture_text

    summary = ""

    if request.method == "POST":
        print("BUTTON WORKS")

        text = request.form.get("text")
        file = request.files.get("file")

        if file and file.filename.endswith(".pdf"):
            import pdfplumber

            with pdfplumber.open(file) as pdf:
                pdf_text = ""

                for page in pdf.pages:
                    pdf_text += page.extract_text()

            summary = summarize(pdf_text)
            lecture_text = pdf_text


        elif text:
            summary = summarize(text)
            lecture_text = text
        elif file and file.filename.endswith(".pptx"):

            ppt = Presentation(file)

            ppt_text = ""

            for slide in ppt.slides:
                for shape in slide.shapes:
                 if hasattr(shape, "text"):
                     ppt_text += shape.text + " "
                
            summary = summarize(ppt_text)
            lecture_text = ppt_text
    file = request.files.get("file")

    if file and file.filename != "":
        lecture_text = extract_text(file)
    else:
        lecture_text = request.form["text"]

    return render_template("index.html", summary=summary)

if __name__ == "__main__":
    app.run(debug=True)
@app.route("/download")
def download():

    summary = request.args.get("text")

    buffer = io.BytesIO()

    p = canvas.Canvas(buffer)

    y = 800

    for line in summary.split("<br>"):
        p.drawString(50, y, line)
        y -= 20

    p.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="notes.pdf",
        mimetype="application/pdf"
    )

@app.route("/ask", methods=["POST"])
def ask():

    question = request.form.get("question")

    context = lecture_text[:1000]

    prompt = f"Answer the question based on this lecture:\n{context}\n\nQuestion: {question}"

    result = summarizer(prompt, max_length=100, num_return_sequences=1)

    answer = result[0]["generated_text"]

    return render_template("index.html", summary="", answer=answer)


def extract_text(file):

    filename = file.filename

    if filename.endswith(".pdf"):
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    elif filename.endswith(".docx"):
        doc = Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

    elif filename.endswith(".pptx"):
        ppt = Presentation(file)
        text = ""
        for slide in ppt.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text

    return ""

def create_pdf(text):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []

    for line in text.split("\n"):
        content.append(Paragraph(line, styles["Normal"]))

    doc.build(content)

    buffer.seek(0)

    return buffer
@app.route("/download")
def download():

    summary = request.args.get("text")

    pdf = create_pdf(summary)

    return send_file(
        pdf,
        as_attachment=True,
        download_name="summary.pdf",
        mimetype="application/pdf"
    )
import os

port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)