import sys
from whatsapp_recap.parse import generate_json_from_chat_data
from whatsapp_recap.data_viz import DataVisualizer

if __name__ == '__main__':
  try:
    file_path = sys.argv[1]
  except IndexError:
    print("give filepath as argument")

  chat_data = generate_json_from_chat_data(file_path, 2023, android=False)

  image_title = "GROUP_CHAT_NAME"
  dv = DataVisualizer(chat_data, image_title)
  dv.export_image()
