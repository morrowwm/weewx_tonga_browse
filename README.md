# weewx_tonga_browse
Python script to query the weewx database for pressure pulse at your location from the Hunga Tonga 2022 eruption

Edit the tonga_barometer.py using a text edit and adjust the input parameters:
 - specify your latitude/longitude as the home variable
 - specify the time period before the estimated arrival time of the pressure pulse in variable hour_lead
 - specify the time period after the event in hour_lag
 - smoothing_hours is used to smooth out the base pressure changes due to normal meteorology
 - highlight_hours determines the 
 - travel_speed is the expected speed of the pressure burst, likely the spped of sound or slightly slower
 - 

Move to the directory containing your weewx.sdb database, or specify its full path on the line:

Run the script
