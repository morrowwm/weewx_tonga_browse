#!/usr/bin/python3
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from geopy import distance
from scipy.interpolate import splev, splrep

# change these paramters as desired
# choose your backend database type
DB="sqlite3"
#DB="mysql"
# your location latitude and longitude
home = (44.80321621050904, -63.62038361172844)
hour_lead = 4
hour_lag = 4
smoothing_hours = 10
highlight_hours = 6
travel_speed = 0.32 # km/s

# ------- normally shouldn't need to change anything below here ----------
raw_data_color = "black"
extracted_data_color = "green"

if DB == "sqlite3":
    import sqlite3
else:
    import sys
    import mysql.connector
    from mysql.connector import errorcode as msqlerrcode
    db_user="weewx"
    db_pwd="insert-your-password"
    db_name="weewx"

hunga_tonga = (-20.5452074472518, -175.38715105641674)
earth_circumference=40040
eruption_time = 1642220085 # 2022-01-15 04:14:45 UTC

distance = distance.distance(hunga_tonga, home).km
travel_time = distance / travel_speed
arrival_time = eruption_time + travel_time

once_around = earth_circumference  / travel_speed
opposite_wave_time = eruption_time + once_around - travel_time
return_wave_time = eruption_time + once_around + travel_time

start_time = 3600*(arrival_time // 3600 - hour_lead)  # start at an even hour
stop_time = 3600*(return_wave_time // 3600 + hour_lag)

print("distance to eruption %0.1f km\narrival at %.0f (%s)" %
      (distance, arrival_time, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(arrival_time))))
print("opposite pulse arrival at %.0f (%s)" %
    ( opposite_wave_time , time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(opposite_wave_time))))
print("second time around pulse arrival at %.0f (%s)" %
    ( return_wave_time , time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(return_wave_time))))

if DB == "sqlite3":
    connection = sqlite3.connect('weewx.sdb')
else:
    try:
        connection = mysql.connector.connect( user=db_user, password=db_pwd,
                host='127.0.0.1', database=db_name)

    except mysql.connector.Error as err:
      if err.errno == msqlerrcode.ER_ACCESS_DENIED_ERROR:
        print("Bad user name or password")
      elif err.errno == msqlerrcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
      else:
        print(err)
      sys.exit( 2)
      
cursor = connection.cursor()

query = "select datetime, barometer from archive where datetime > %.0f and datetime < %.0f and barometer is not null order by dateTime;" % (start_time, stop_time)
print(query)
cursor.execute(query)

result = cursor.fetchall()
connection.close()

npoints = len(result)
print( f"query returned {npoints} data points")
if npoints == 0: exit

xdata = []
ydata = []
tdata = []

for row in result:
   xdata.append(row[0])
   tdata.append(mdates.datestr2num(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(row[0]))))
   ydata.append(row[1])
   
# spline fit to remove base variations in pressure
knots = np.linspace(np.min(tdata), np.max(tdata), (stop_time-start_time)/(3600*smoothing_hours), endpoint=True)  # spline knot every N hours
#print(knots)
if len(knots) < 1:
    print("Smoothing length of %.0f is too long for curve fit. Try %.0f hours or less."
          % (smoothing_hours, ((stop_time-start_time)/3600)))
    exit()
smooth = splrep(x=tdata, y=ydata, task=-1, t=knots[1:-1]) # need to exclude exterior knots. Spline order is 3
                       
fig, ax = plt.subplots(figsize=(10,5))

plt.text(tdata[0], np.max(ydata) + 0.05*(np.max(ydata) - np.min(ydata)), "location: %0.1f, %0.1f speed %3.0f m/s"
         % (home[0], home[1], travel_speed*1000.0))

date_formatter = mdates.DateFormatter('%m-%d %H:%M')
ax.yaxis.label.set_color(raw_data_color)
ax.set_ylabel('barometric pressure (hPa)')
ax.tick_params(axis="x", rotation=90)
ax.xaxis.set_major_locator(mdates.HourLocator(interval = 4))
ax.xaxis.set_major_formatter(date_formatter)
ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval = 15))
#ax.set_xlim(xmin=tdata[0]//1) # start at a round hour

fig.subplots_adjust(bottom=0.3)

ax.set_ylim( np.min(ydata), np.max(ydata))
ax.plot(tdata, ydata, marker='.', markeredgecolor="paleturquoise", markerfacecolor='None', markersize=2, linestyle='None')
ax.plot(knots, splev(knots, smooth), marker='+', color="black", markersize=20, linestyle='None')
ax.plot(tdata, splev(tdata, smooth), color="black", linewidth=1)

ax2=ax.twinx()
ax2.yaxis.label.set_color(extracted_data_color)
ax2.set_ylabel('extracted feature (hPa)')
ax2.plot(tdata, ydata-splev(tdata, smooth), color="green", linewidth=1)

peakt = [
    mdates.datestr2num(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(arrival_time))),
    mdates.datestr2num(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(opposite_wave_time))),
    mdates.datestr2num(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(return_wave_time)))
]

bar_height = np.max(ydata)
annotation_y = np.min(ydata) + 0.05*(np.max(ydata) - np.min(ydata))

b1 = ax.bar( peakt, [bar_height, bar_height, bar_height] , width=0.25/highlight_hours, color="lightgrey" )
ax.annotate("Initial", xy=(peakt[0], annotation_y))
ax.annotate("Reverse", xy=(peakt[1], annotation_y))
ax.annotate("Second", xy=(peakt[2], annotation_y))


# save the plot as a file
fig.savefig('./hunga_tonga.png', format='png', dpi=100, bbox_inches='tight')

plt.show()
