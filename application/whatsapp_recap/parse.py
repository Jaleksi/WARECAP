import re
import json

from datetime import datetime, timedelta
from calendar import monthrange

import emoji

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def generate_json_from_chat_data(
  chat_data,
  year_to_recap,
  from_filestorage=False,
  export_json=True
):
  messages = (
    parse_chat_from_filestorage_object(chat_data, year_to_recap)
    if from_filestorage
    else parse_chat_from_file_path(chat_data, year_to_recap)
  )
  result = {
    "target_year": year_to_recap,
    "streaks": longest_streaks(messages),
    "top_emojis": top_emojis(messages),
    "total_datetime_deviations": datetime_deviation(messages, year_to_recap),
    "user_averages": user_averages(messages, year_to_recap)
  }

  if export_json:
    with open("result.json", "w", encoding="utf-8") as output:
      output.write(json.dumps(result, ensure_ascii=False, indent=4))

  return result

def parse_chat_from_file_path(file_path, year_to_recap):
  with open(file_path, "r", encoding="utf-8") as f:
    return parse_chat(f.read(), year_to_recap)

def parse_chat_from_filestorage_object(fs_object, year_to_recap):
  return parse_chat(fs_object.read().decode("utf-8"), year_to_recap)

def parse_chat(contents, year_to_recap):
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


def longest_streaks(msgs):
  streak_limit = 600 # 10mins

  longest_silent_duration = 0
  longest_silence_starter = None
  
  longest_streak_duration = 0
  cur_streak_duration = 0
  longest_streak_start = None
  longest_streak_end = None
  cur_streak_start = msgs[0]
  cur_streak_end = None

  for i, msg in enumerate(msgs):
    if i == len(msgs) - 1:
      break
    duration = msgs[i + 1]["datetime"] - msg["datetime"]
    if not longest_silent_duration or duration > longest_silent_duration:
      longest_silence_starter = msg
      longest_silent_duration = duration

    if i == 0:
      continue

    if duration.seconds < streak_limit:
      cur_streak_duration += duration.seconds
      cur_streak_end = msgs[i + 1]
    else:
      if cur_streak_duration > longest_streak_duration:
        longest_streak_duration = cur_streak_duration
        longest_streak_start = cur_streak_start
        longest_streak_end = cur_streak_end
      cur_streak_start = msgs[i + 1]
      cur_streak_end = None
      cur_streak_duration = 0

  return {
    "longest_silence_in_seconds": longest_silent_duration.seconds,
    "longest_streak_duration_in_seconds": longest_streak_duration
  }

def top_emojis(messages):
  # Returns top 10 used emojis
  emoji_scores = {}
  for msg in messages:
    if msg["text"] is None:
      continue
    found_emojis = emoji.emoji_list(msg["text"])
    if found_emojis:
      for found_emoji in found_emojis:
        if found_emoji["emoji"] in emoji_scores:
          emoji_scores[found_emoji["emoji"]] += 1
        else:
          emoji_scores[found_emoji["emoji"]] = 1
  sorted_by_usage = dict(sorted(emoji_scores.items(), reverse=True, key=lambda item: item[1])[:10])
  return sorted_by_usage


def datetime_deviation(messages, year_to_recap, target_user=None):
  days_count = {
    "Monday": [0 for _ in range(24)],
    "Tuesday": [0 for _ in range(24)],
    "Wednesday": [0 for _ in range(24)],
    "Thursday": [0 for _ in range(24)],
    "Friday": [0 for _ in range(24)],
    "Saturday": [0 for _ in range(24)],
    "Sunday": [0 for _ in range(24)]

  }
  total_hours_count = [0 for _ in range(24)]
  year_days_count = [0 for _ in range(366)] # 366 in case of leap year
  year_start = datetime(year_to_recap, 1, 1)

  for msg in messages:
    if target_user and msg["name"] != target_user:
      continue
    # Add to week day count
    days_count[WEEKDAYS[msg["datetime"].weekday()]][msg["datetime"].hour] += 1

    # Add to hour count
    total_hours_count[msg["datetime"].hour] += 1

    # Add to years total days count
    datediff = msg["datetime"] - year_start
    year_days_count[datediff.days] += 1

  # Create dict for whole year where months are separate keys
  # and weeks are divided to their own array
  months_data = {}
  cur_day_index = 0
  for month_index in range(0, 12):
    _, last_day = monthrange(year_to_recap, month_index + 1)
    weeks = []

    current_week = [None for _ in range(7)]
    for day in range(1, last_day + 1):
      weekday_index = datetime(year_to_recap, month_index + 1, day).weekday()
      current_week[weekday_index] = year_days_count[cur_day_index]
      cur_day_index += 1;
      if weekday_index == 6 or day == last_day:
        weeks.append(current_week)
        current_week = [None for _ in range(7)]

    months_data[MONTHS[month_index]] = weeks

  return {
    "weekdays": days_count,
    "total_hours": total_hours_count,
    "year_monthly": months_data,
    "year_daily": year_days_count,
  }

def user_averages(messages, year_to_recap):
  users = {}
  for msg in messages:
    user = msg["name"]
    if user in users:
      users[user]["msg_count"] += 1
      if msg["text"] is not None:
        users[user]["msg_chars_total"] += len(msg["text"])
      if msg["hasImage"]:
        users[user]["images_sent"] += 1
    else:
      users[user] = {
      "msg_count": 1,
      "msg_chars_total": 0 if msg["text"] is None else len(msg["text"]),
      "images_sent": 1 if msg["hasImage"] else 0
    }

  for user in users:
    users[user]["avg_msg_length"] = users[user]["msg_chars_total"] / users[user]["msg_count"]
    users[user]["datetime_deviations"] = datetime_deviation(messages, year_to_recap, user)
  return users

