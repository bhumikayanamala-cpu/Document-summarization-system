from flask import Flask, render_template, request, send_file
import os
import pdfplumber
from transformers import pipeline
import io

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Faster summarization model
summarizer = pipeline(
    "summarization",
    model="sshleifer/distilbart-cnn-12-6"
)


# split long text into chunks
def split_text(text, chunk_size=800):

    words = text.split()

    chunks = []

    for i in range(0, len(words), chunk_size):

        chunks.append(" ".join(words[i:i+chunk_size]))

    return chunks



# extract text and only real tables
def extract_text_and_tables(file_path):

    text_data = ""

    valid_tables = []

    with pdfplumber.open(file_path) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if text:
                text_data += text + "\n"


            tables = page.extract_tables()

            for table in tables:

                if not table:
                    continue


                cleaned = []

                for row in table:

                    row_data = [str(cell).strip() if cell else "" for cell in row]

                    if any(row_data):
                        cleaned.append(row_data)


                if len(cleaned) < 2:
                    continue


                col_count = max(len(r) for r in cleaned)


                # ignore single column tables
                if col_count <= 1:
                    continue


                # ignore paragraph-like tables
                long_text_cells = sum(
                    1 for row in cleaned
                    for cell in row
                    if len(cell.split()) > 12
                )

                if long_text_cells > 3:
                    continue


                # ignore very wide messy tables
                if col_count > 6:
                    continue


                valid_tables.append(cleaned)


    return text_data, valid_tables



# generate summary
def generate_summary(text):

    if not text.strip():

        return "No readable text found."


    chunks = split_text(text)

    final_summary = ""


    for chunk in chunks:

        try:

            result = summarizer(

                chunk,

                max_length=120,

                min_length=40,

                do_sample=False

            )

            final_summary += result[0]["summary_text"] + " "

        except:

            continue


    return final_summary



# home page
@app.route("/", methods=["GET", "POST"])

def home():

    summaries = {}

    filenames = []


    if request.method == "POST":

        files = request.files.getlist("files")


        for file in files:

            if file and file.filename != "":

                filenames.append(file.filename)


                path = os.path.join(

                    app.config["UPLOAD_FOLDER"],

                    file.filename

                )


                file.save(path)


                text, tables = extract_text_and_tables(path)


                summary = generate_summary(text)


                summaries[file.filename] = {

                    "summary": summary,

                    "tables": tables

                }


                os.remove(path)


    return render_template(

        "index.html",

        summaries=summaries,

        filenames=filenames

    )



# download summary
@app.route("/download")

def download_summary():

    filename = request.args.get("filename")

    summary_text = request.args.get("summary")


    file_stream = io.BytesIO()

    file_stream.write(summary_text.encode("utf-8"))

    file_stream.seek(0)


    return send_file(

        file_stream,

        as_attachment=True,

        download_name=filename + "_summary.txt",

        mimetype="text/plain"

    )



if __name__ == "__main__":

    app.run(debug=True)