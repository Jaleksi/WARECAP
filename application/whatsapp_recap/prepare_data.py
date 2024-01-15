from datetime import datetime
from calendar import monthrange

import emoji

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def get_prepared_data(messages, year_to_recap):
  return {
    "target_year": year_to_recap,
    "streaks": longest_streaks(messages),
    "top_emojis": top_emojis(messages),
    "total_datetime_deviations": datetime_deviation(messages, year_to_recap),
    "user_averages": user_averages(messages, year_to_recap)
  }

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
