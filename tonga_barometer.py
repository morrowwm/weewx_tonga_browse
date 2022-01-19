#!/usr/bin/python3
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlite3
from geopy import distance
from scipy.interpolate import splev, splrep

# change as needed
home = (44.80321621050904, -63.62038361172844)

hunga_tonga = (-20.5452074472518, -175.38715105641674)
speed_of_sound = 0.32 # km/s
eruption_time = 1642220085 # 2022-01-15 04:14:45 UTC
hour_lead = 24
hour_lag = 120

distance = distance.distance(hunga_tonga, home).km
travel_time = distance / speed_of_sound
arrival_time = eruption_time + travel_time
start_time = 3600*(arrival_time // 3600 - hour_lead)  # start at an even hour

print("distance to eruption %0.1f km arrival at %.0f (%s)" % (distance, arrival_time, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(arrival_time))))
      
connection = sqlite3.connect('weewx.sdb')
cursor = connection.cursor()

query = "select datetime, barometer from archive where datetime > %.0f and datetime < %.0f order by dateTime;" % (start_time, arrival_time + hour_lag*3600)
print(query)
cursor.execute(query).fetchall

result = cursor.fetchall()

connection.close()

xdata = []
ydata = []
tdata = []

for row in result:
   xdata.append(row[0])
   tdata.append(mdates.datestr2num(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(row[0]))))
   ydata.append(row[1])
   
# remove any linear trend
coeff = np.polyfit(xdata, ydata, 2)
trend = np.polyval(coeff, xdata)

knots = np.linspace(np.min(tdata), np.max(tdata), (hour_lead+hour_lag)/6, endpoint=True)  # spline knot every 12 hours

smooth = splrep(x=tdata, y=ydata, task=-1, t=knots[4:-4]) # need to exclude exterior knots. Spline order is 3
                        
fig, ax = plt.subplots()

plt.text(tdata[1], np.max(ydata), "location: %0.2f, %0.2f" % home)

date_formatter = mdates.DateFormatter('%m-%d %H:%M')
ax.tick_params(axis="x", rotation=90)
ax.xaxis.set_major_locator(mdates.HourLocator(interval = 4))
ax.xaxis.set_major_formatter(date_formatter)
ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval = 15))
#ax.set_xlim(xmin=tdata[0]//1) # start at a round hour

fig.subplots_adjust(bottom=0.2)

ax.plot(tdata, ydata, color="paleturquoise", linewidth=3)
ax.plot(tdata, splev(tdata, smooth), color="black", linewidth=1)

ax2=ax.twinx()
ax2.plot(tdata, ydata-splev(tdata, smooth), linewidth=1)

# save the plot as a file
fig.savefig('./hunga_tonga.png', format='png', dpi=100, bbox_inches='tight')

plt.show()
