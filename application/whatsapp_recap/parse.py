import re
import json

from datetime import datetime
from .prepare_data import get_prepared_data

def generate_json_from_chat_data(
  chat_data,
  year_to_recap,
  from_filestorage=False,
  export_json=True,
  android=True
):
  messages = (
    parse_chat_from_filestorage_object(chat_data, year_to_recap, android)
    if from_filestorage
    else parse_chat_from_file_path(chat_data, year_to_recap, android)
  )
  result = get_prepared_data(messages, year_to_recap)

  if export_json:
    with open("result.json", "w", encoding="utf-8") as output:
      output.write(json.dumps(result, ensure_ascii=False, indent=4))

  return result

def parse_chat_from_file_path(file_path, year_to_recap, android):
  with open(file_path, "r", encoding="utf-8") as f:
    if android:
      return parse_chat_android(f.read(), year_to_recap)
    return parse_chat_ios(f.read(), year_to_recap)

def parse_chat_from_filestorage_object(fs_object, year_to_recap, android):
  if android:
    return parse_chat_android(fs_object.read().decode("utf-8"), year_to_recap)
  return parse_chat_ios(fs_object.read().decode("utf-8"), year_to_recap)

def parse_chat_android(contents, year_to_recap):
  MEDIA_STRING = "<Media omitted>"
  messages = []
  raw_msgs = re.split(r"(\d+\/\d+\/\d+, \d{2}:\d{2} - )", contents)[1:]
  raw_msgs = [raw_msgs[i] + raw_msgs[i + 1] for i in range(0, len(raw_msgs), 2)]
  for rm in raw_msgs:
    split_rm = rm.split(":")
    if len(split_rm) < 3:
      continue

    msg_data = {
      "hasImage": MEDIA_STRING in rm
    }
    if MEDIA_STRING in rm:
      msg_data["text"] = None
    else:
      msg_text = split_rm[2].replace("\n", " ")
      msg_data["text"] = msg_text[1:len(msg_text)-1]

    meta_string = ":".join(split_rm[0:2])
    
    date = re.search(r"\d+\/\d+\/\d+", meta_string).group(0)
    time = re.search(r"\d{2}:\d{2}", meta_string).group(0)
    msg_data["datetime"] = datetime.strptime(f"{date} {time}", "%m/%d/%y %H:%M")

    if msg_data["datetime"].year != year_to_recap:
      continue

    msg_data["name"] = re.search(r"- (.+)", meta_string).group(1)
    messages.append(msg_data)
  return messages

def parse_chat_ios(contents, year_to_recap):
  MEDIA_STRINGS = ["ei kuvaa", "videota ei sisällytetä"]
  messages = []
  raw_msgs = re.split(r"(\[\d+\.\d+\.\d{4} \d{2}\.\d{2}\.\d{2}\] )", contents)[1:]
  raw_msgs = [raw_msgs[i] + raw_msgs[i + 1] for i in range(0, len(raw_msgs), 2)]
  for rm in raw_msgs:
    split_rm = rm.split(":")
    if len(split_rm) != 2:
      continue

    has_image = any([True if s in rm else False for s in MEDIA_STRINGS])
    msg_data = {
      "hasImage": has_image
    }

    msg_data["text"] = None if has_image else split_rm[1].replace("\n", " ")[1:]

    meta_string = split_rm[0]
    
    date = re.search(r"\d+\.\d+\.\d{4}", meta_string).group(0)
    time = re.search(r"\d{2}\.\d{2}\.\d{2}", meta_string).group(0)
    msg_data["datetime"] = datetime.strptime(f"{date} {time}", "%d.%m.%Y %H.%M.%S")

    if msg_data["datetime"].year != year_to_recap:
      continue

    msg_data["name"] = re.search(r"] (.+)", meta_string).group(1)
    messages.append(msg_data)
  return messages



