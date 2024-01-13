from flask import Flask, render_template, request, send_file, Response
from .whatsapp_recap.parse import generate_json_from_chat_data
from .whatsapp_recap.data_viz import DataVisualizer

app = Flask(__name__)

@app.route("/")
def index():
  return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
  target_year = int(request.form.get("year"))
  graph_title = request.form.get("title")
  chat_file = request.files.get("chatlog")


  chat_json = generate_json_from_chat_data(
    chat_file,
    target_year,
    from_filestorage=True,
    export_json=False
  )

  dv = DataVisualizer(chat_json, image_title=graph_title)
  img_buffer = dv.export_image(return_as_buffer=True)
  return send_file(img_buffer, download_name=f"{graph_title}_{target_year}.png", as_attachment=True)