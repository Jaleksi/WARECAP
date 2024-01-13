from io import BytesIO
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.gridspec import GridSpec
import pandas as pd
import numpy as np


class DataVisualizer:
  def __init__(self, recap_data, image_title="IMAGE_TITLE"):
    font_entry = mpl.font_manager.FontEntry(
      fname="./application/static/NotoEmoji-Regular.ttf",
      name="Noto"
    )
    mpl.font_manager.fontManager.ttflist.append(font_entry)

    self.image_title = image_title
    self.recap_data = recap_data
    self.fig = plt.figure(figsize=(8.27, 11.7)) # A4 size
    self.main_gs = GridSpec(5, 2, figure=self.fig, hspace=0.5)
    self.green_color = "#55aa99"

  def export_image(self, return_as_buffer=False):
    self.plot_all_messages_by_day()
    self.plot_weekday_hour_deviations()
    self.plot_weekday_deviations_bar()
    self.plot_hours_deviation_bar()
    self.plot_top10_emojis_bar()
    self.plot_title()
    #plt.show()
    if return_as_buffer:
      buffer = BytesIO()
      plt.savefig(buffer, format="png")
      buffer.seek(0)
      plt.close(self.fig)
      return buffer
    else:
      plt.savefig(f"{self.image_title}.png")
      plt.close(self.fig)

  def plot_title(self):
    ax = self.fig.add_subplot(self.main_gs[0, :-1])
    ax.set_axis_off()
    ax.text(
      x=0,
      y=1,
      s=f'{self.recap_data["target_year"]} - {self.image_title}',
      fontsize=16,
      weight="bold",
      transform=ax.transAxes,
    )

    total_messages = sum([u["msg_count"] for u in self.recap_data["user_averages"].values()])
    total_users = len(self.recap_data["user_averages"])
    total_images_sent = sum([u["images_sent"] for u in self.recap_data["user_averages"].values()])
    avg_msg_len = int(sum([u["avg_msg_length"] for u in self.recap_data["user_averages"].values()]) // total_users)

    bold = lambda t: r"$\bf{" + str(t)  + "}$"

    subtitle_text = (
      f'In total {bold(total_messages)} messages were sent in {bold(self.recap_data["target_year"])} by {bold(total_users)} different users.\n'
      f'Out of all the messages sent {bold(total_images_sent)} had image attachment\n'
      f'and the average message length was about {bold(avg_msg_len)} characters.'
    )
    ax.text(
      x=0,
      y=0.25,
      s=subtitle_text,
      fontsize=8,
      weight="regular",
      transform=ax.transAxes,
    )

  def plot_all_messages_by_day(self):
    datas = []
    masks = []
    grid_width_ratios = []

    for month in self.recap_data["total_datetime_deviations"]["year_monthly"]:
      mask = np.array([
        [
          value is None
          for value
          in week
        ]
        for week in self.recap_data["total_datetime_deviations"]["year_monthly"][month]
      ]).T
      data = np.array([
        [
          value if value is not None else 0
          for value
          in week
        ]
        for week in self.recap_data["total_datetime_deviations"]["year_monthly"][month]
      ]).T

      datas.append(data)
      masks.append(mask)

      # some months have more week rows than others, need to have different width
      # ratio to keep all months same size
      ratio = 1 if data.shape[1] == 5 else 1.2
      grid_width_ratios.append(ratio)

    all_messages_grid = self.main_gs[1, :2].subgridspec(
      2,
      12,
      wspace=0.05,
      hspace=0,
      width_ratios=grid_width_ratios,
      height_ratios=[2, 1],
    )
    for i, (data, mask) in enumerate(zip(datas, masks)):
      ax = self.fig.add_subplot(all_messages_grid[i])
      heatmap = sns.heatmap(
        data=data,
        ax=ax,
        square=True,
        linewidths=1,
        cmap=sns.color_palette("light:#5A9", as_cmap=True),
        mask=mask,
        xticklabels=False,
        yticklabels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] if i == 0 else False,
        cbar=False,
      )
      heatmap.set_yticklabels(heatmap.get_yticklabels(), size=6)
      month_name = list(self.recap_data["total_datetime_deviations"]["year_monthly"].keys())[i]
      plt.title(month_name[:3], fontsize=8)

    # plot the year line graph
    line_ax = self.fig.add_subplot(all_messages_grid[12:])
    line_ax.margins(x=0, y=0)
    line_plot = sns.lineplot(
      data=self.recap_data["total_datetime_deviations"]["year_daily"][:365],
      ax=line_ax,
      color=self.green_color,
      linewidth=1,
    )
    line_ax.fill_between(
      [i for i in range(365)],
      self.recap_data["total_datetime_deviations"]["year_daily"][:365],
      color="#55aa99",
    )
    line_ax.set_xticklabels([])
    line_ax.set_yticklabels([])
    line_ax.axis("off")

  def plot_hour_deviations(self):
    grid = GridSpec(1, 1, top=0.45, wspace=0.05)
    ax = self.fig.add_subplot(grid[0], projection="polar")
    values = self.recap_data["total_datetime_deviations"]["total_hours"]
    keys = [str(i).zfill(2) for i in range(24)]
    theta = np.linspace(0, 2 * np.pi, len(values), endpoint=False)

    # Plot the bars on the polar axis
    bars = ax.bar(theta, values, width=0.225, align='center')

    # Add labels and title
    ax.grid(False)
    ax.set_xticks(theta, labels=keys)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_yticks([])

  def plot_weekday_hour_deviations(self):
    ax = self.fig.add_subplot(self.main_gs[3, 0])

    data = np.array([
      week_data for _, week_data in self.recap_data["total_datetime_deviations"]["weekdays"].items()
    ])

    heatmap = sns.heatmap(
      data=data,
      ax=ax,
      square=True,
      linewidths=1,
      cmap=sns.color_palette("light:#5A9", as_cmap=True),
      xticklabels=[str(i).zfill(2) for i in range(24)],
      yticklabels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
      cbar=False,
    )
    heatmap.set_xticklabels(heatmap.get_xticklabels(), size=6)
    heatmap.set(title="Weekdays vs hours")

  def plot_weekday_deviations_bar(self):
    ax = self.fig.add_subplot(self.main_gs[2, 1])

    days_total_messages = [
      sum(weekday_data) for weekday_data
      in self.recap_data["total_datetime_deviations"]["weekdays"].values()
    ]
    sns.barplot(
      y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
      x=days_total_messages,
      ax=ax,
      color=self.green_color,
      orient="h",
    ).set(title="Message distribution by weekday")
    sns.despine(bottom=True, left=True)

  def plot_hours_deviation_bar(self):
    ax = self.fig.add_subplot(self.main_gs[2, 0])
    hours_data = self.recap_data["total_datetime_deviations"]["total_hours"]
    barplot = sns.barplot(
      x=[str(i).zfill(2) for i in range(24)],
      y=hours_data,
      ax=ax,
      color=self.green_color,
      orient="v",
    )
    barplot.set(title="Message distribution by hour")
    barplot.set_xticklabels(barplot.get_xticklabels(), size=6)
    sns.despine(bottom=True, left=True)


  def plot_avg_msg_len_by_user(self):
    grid = GridSpec(1, 1, top=0.45, wspace=0.05)
    ax = self.fig.add_subplot(grid[0])
    users = list(self.recap_data["user_averages"].keys())
    msg_lengths = [user["avg_msg_length"] for user in self.recap_data["user_averages"].values()]
    sns.barplot(
      #label="Average message length by user",
      x=users,
      y=msg_lengths,
      ax=ax,
    )
    ax.set(ylabel="Average message length")


  def plot_top10_emojis_bar(self):
    ax = self.fig.add_subplot(self.main_gs[3, 1])
    emoji_data = self.recap_data["top_emojis"]
    barplot = sns.barplot(
      x=list(emoji_data.keys()),
      y=list(emoji_data.values()),
      ax=ax,
      color=self.green_color,
      orient="v",
    )
    barplot.set(title="Most used emojis")
    #barplot.set_yscale("log")

    # change font for emojis because default may not support all
    for tick in ax.get_xticklabels():
      tick.set_fontname("Noto")

    sns.despine(bottom=True, left=True)