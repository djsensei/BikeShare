'''
Main modules for bikeshare data

Dan Morris 3/28/14
'''

import simplejson as json
import datetime as dt
#from fun import *
from constants import *
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation

class Trip:
	def __init__(self, trip_data_line):
		d = trip_data_line.split(",")
		self.id = d[0]
		self.duration = int(d[1]) # units: seconds
		self.start_moment = dtfix(d[2])
		self.start_station = station_name_to_id.get(d[3],"0")
		self.start_terminal = d[4]
		self.end_moment = dtfix(d[5])
		self.end_station = station_name_to_id.get(d[6],"0")
		self.end_terminal = d[7]
		self.bike_id = d[8]
		self.sub_type = d[9]
		self.zipcode = d[10]
		self.city = self.city_find()
		self.weekday = self.dayofweek()
		self.route = self.start_station+','+self.end_station
		return

	def dayofweek(self): # TODO: Fix with new datetimescheme
		# Determines which day the trip starts, returns an integer
		#  between 0 and 6. Monday=0, Sunday=6
		td = self.start_moment.date() - day_one
		return (td.days + 3) % 7

	def city_find(self):
		for k in stations_by_city.keys():
			if self.start_station in stations_by_city[k]:
				return k
		return None

	def active_during(self, datetime):
		# returns True if the trip is active during given datetime
		if datetime >= self.start_moment and datetime < self.end_moment:
			return True
		else:
			return False

class TripGraph:
	def __init__(self, trip_list):
		self.nodes = [] # station ids
		self.edges = {} # keyed by 'start,end' string
		for t in trip_list:
			s = t.start_station
			e = t.end_station
			# Add station if new
			if s not in self.nodes:
				self.nodes.append(s)
			if e not in self.nodes:
				self.nodes.append(e)
			# Load edges dict with lists of trips on each edge
			k = s+","+e
			if k in self.edges:
				self.edges[k].append(t)
			else:
				self.edges[k] = [t]
		return

class SystemSnapshot:
	# A simplified look at the whole system at a given moment in time
	#   designed to be easily portable in JSON or csv.
	def __init__(self, tripgraph, moment):
		self.moment = moment
		# Load nodes
		self.nodes = {} # key: station, value: # available bikes
		for n in tripgraph.nodes:
			self.nodes[n] = rebalancing_station_snapshot(n, moment)
		# Load edges
		self.edges = {} # key: 'start,end', value: # of active trips
		for k in tripgraph.edges:
			for t in tripgraph.edges[k]:
				if t.active_during(moment):
					if k in self.edges:
						self.edges[k] += 1
					else:
						self.edges[k] = 1
		return

	''' - currently unnecessary, no empty edges are created
	def remove_empty_edges(self):
		doomed = []
		for e in self.edges:
			if self.edges[e] == 0:
				doomed.append(e)
		for d in doomed:
			del self.edges[d]
		return'''

	def output_json(self):
		fname = snap_filename(self.moment, 'json')
		with open(fname, 'w') as f:
			json.dump(self.nodes, f, indent=0)
			json.dump(self.edges, f, indent=0)
		return

	def output_csvs(self):
		# Writes csvs to file with visualization purposes in mind
		nodes_filename = snap_filename(self.moment, 'nodes', 'csv')
		edges_filename = snap_filename(self.moment, 'edges', 'csv')
		with open(nodes_filename, 'w') as nf:
			header = 'station_id,available_bikes\n'
			nf.write(header)
			for n in self.nodes:
				nf.write(n+','+str(self.nodes[n])+'\n')
		with open(edges_filename, 'w') as ef:
			header = 'start_station,end_station,num_bikes\n'
			ef.write(header)
			for e in self.edges:
				ef.write(e+','+str(self.edges[e])+'\n')
		return

	def __repr__(self):
		s = "Snapshot of BikeShare at "+str(self.moment.hour)+":"\
		    +str(self.moment.minute)+" on "+str(self.moment.month)\
			+"/"+str(self.moment.day)+"/"+str(self.moment.year)+"\n"
		for k in self.nodes:
			s += station_id_to_name[k]+": "+str(self.nodes[k]['bikes'])\
			+" bikes and "+str(self.nodes[k]['freedocks'])+" free docks.\n"
		for e in self.edges:
			if self.edges[e] > 0:
				s += str(self.edges[e])+" bikers from station "\
				+e[0]+" to station "+e[1]+"\n"
		return s

class Station:
	def __init__(self, station_data_line):
		d = station_data_line.split(',')
		self.id = d[0]
		self.name = d[1]
		self.lat = float(d[2])
		self.lon = float(d[3])
		self.docks = int(d[4])
		self.city = d[5]
		self.install_date = datefix(d[6])
		self.elevation = float(d[7])
		self.loc = self.locationfix()

	def locationfix(self):
		# converts raw lat/lon coordinates into scaled x,y
		c = self.city
		x = (self.lon - center_latlon[c][1]) * latlon_scale[c][1]
		y = (self.lat - center_latlon[c][0]) * latlon_scale[c][0]
		return (x,y)

class Rebalancing:
	def __init__(self, rebalancing_data_line):
		d = rebalancing_data_line.split(',')
		self.id = d[0]
		self.bikes = int(d[1])
		self.freedocks = int(d[2])
		self.docks = self.bikes + self.freedocks
		moment = d[3].strip('\n')
		self.datetime = dtfix(moment)

'''
class Weather:
	def __init__(self, weather_data):
'''

def read_data(type, n="all"):
	# Reads the first n data lines from filename
	if type not in data_file_names.keys():
		print "bad type!"
		return None
	filename = data_file_names[type]
	datalist = []
	if n == "all":
		n = data_file_lengths[type] - 1
	with open(filename) as f:
		f.readline() # Clear header
		if type == "trip":
			for i in xrange(n):
				d = f.readline()
				datalist.append(Trip(d))
		elif type == "station":
			for i in xrange(n):
				d = f.readline()
				datalist.append(Station(d))
		elif type == "weather":
			for i in xrange(n):
				d = f.readline()
				datalist.append(Weather(d))
		elif type == "rebalancing":
			for i in xrange(n):
				d = f.readline()
				datalist.append(Rebalancing(d))
	return datalist

def read_all_data():
	# Call this to load all the data files into big lists
	# Note: currently ignores weather + rebalancing
	trips = read_data("trip")
	stations = read_data("station")
	return trips, stations

def datefix(rawdate):
	# Converts a raw date "mm/dd/yyyy" or "yyyy/mm/dd" into a datetime.date object
	d = rawdate.strip('\r\n')
	d = d.split("/")
	if len(d[0])==4:
		return dt.date(int(d[0]), int(d[1]), int(d[2]))
	else:
		return dt.date(int(d[2]), int(d[0]), int(d[1]))

def timefix(rawtime):
	# Converts a raw time into a datetime.time object
	# Accepts hh:mm or hh:mm:ss
	t = rawtime.split(":")
	if len(t) == 2:
		return dt.time(int(t[0]), int(t[1]))
	elif len(t) == 3:
		return dt.time(int(t[0]), int(t[1]), int(t[2]))
	else:
		print "weird time data!"
		return

def dtfix(rawdt):
	# Converts raw datetime string into a datetime object
	x = rawdt.strip('\r\n')
	x = x.split(" ")
	date = x[0].split("/")
	time = x[1].split(":")
	if len(date[0])==4:
		year = int(date[0])
		month = int(date[1])
		day = int(date[2])
	else:
		year = int(date[2])
		month = int(date[0])
		day = int(date[1])
	hour = int(time[0])
	minute = int(time[1])
	if len(time)==3:
		second = int(time[2])
	return dt.datetime(year,month,day,hour,minute,second=0)

def snap_filename(moment, lead='', type='csv'):
	if type == 'csv':
		ext = 'csv'
	else:
		ext = 'txt'
	f = "datafiles/"+lead+'_'+type+"_"+str(moment.month)+"-"\
		+str(moment.day)+"-"+str(moment.year)+"_"\
		+str(moment.hour)+"h"+str(moment.minute)+"m."+ext
	return f

def all_trips_from(station_id, trip_data):
	# Returns a subset of trip_data
	trips = []
	for t in trip_data:
		if t.start_station == station_id:
			trips.append(t)
	return trips

def all_trips_to(station_id, trip_data):
	# Returns a subset of trip_data
	trips = []
	for t in trip_data:
		if t.end_station == station_id:
			trips.append(t)
	return trips

def all_trips_by_bike_id(trip_data, bikeid):
	trips = []
	for t in trip_data:
		if t.bike_id == bikeid:
			trips.append(t)
	return trips

def all_trips_by_city(trip_data, city):
	trips = []
	for t in trip_data:
		if t.city == city:
			trips.append(t)
	return trips

def weekday_split_trips(trip_data):
	weekday = []
	weekend = []
	for t in trip_data:
		if t.weekday > 4:
			weekend.append(t)
		else:
			weekday.append(t)
	return weekday, weekend

def count_trips_by_start_hour(trip_data):
	# Prints a count of trips in the trip_data list by start hour
	hours = [0]*24
	for t in trip_data:
		hours[t.start_moment.hour] += 1
	for h in range(24):
		print '%s trips in hour %s' % (hours[h], h)
	return

def create_station_nameid_json():
	# Creates a json file of {station name: station id} pairs
	station_data = read_data("station", "all")
	station_dict = {}
	for s in station_data:
		station_dict[s.name] = s.id
	return station_dict

def compress_rebalancing_datafile(\
	fname="datafiles/rebalancing_compressed_data.csv", n="all"):
	# Compresses the rebalancing data file into a shorter one by
	#   removing redundant lines of data.
	if n=="all":
		n = data_file_lengths["rebalancing"]
	with open(fname, "w") as writefile:
		with open(data_file_names["rebalancing"]) as f:
			# copy header and first line to new file
			writefile.write(f.readline()) # header
			first = f.readline() # first data line
			writefile.write(first)
			check = first.split(',"201')[0]
			# scan datalines. copy new ones, ignore redundant ones
			for i in xrange(n):
				l = f.readline()
				if l == "":
					break
				s = l.split(',"201')
				if s[0] != check:
					check = s[0]
					writefile.write(l)
	return

def compressed_rebalancing_station_sort(\
	fname="datafiles/rebalancing_compressed_data.csv"):
	# splits the compressed rebalancing data file by station id
	with open(fname) as f:
		header = f.readline()
		i = 3 # first data line in the loop
		l = f.readline()
		cs = l.split(',')[0]
		writefile = open('datafiles/rebalancing_data_station_'+cs.strip('"')+'.csv','w')
		writefile.write(header)
		writefile.write(l)
		while i < 453903: # Not robust if source file changes!
			# read line
			l = f.readline()
			# check if current station
			temp = l.split(',')[0]
			if temp != cs:
				writefile.close()
				writefile = open('datafiles/rebalancing_data_station_'+temp.strip('"')+'.csv','w')
				writefile.write(header)
				cs = temp
			writefile.write(l)
			i += 1
		writefile.close()
	return

def rebalancing_station_snapshot(station, datetime):
	# Returns the # of bikes at a specific station and moment
	rfile = "datafiles/rebalancing_station_"+station+".csv"
	with open(rfile) as f:
		f.readline() # clear header
		new = f.readline()
		d = new.split(',')[3]
		d = d.strip('\n')
		d = dtfix(d)
		if d > datetime:
			print "station not open yet"
			return None
		while d < datetime:
			old = new
			new = f.readline()
			d = new.split(',')[3]
			d = d.strip('\n')
			d = dtfix(d)
	return int(old.split(',')[1])

def compress_node_files():
	# Compresses all node files into a single file for
	#   animated visualization in Tableau.
	header = "frame,time,station_id,available_bikes\n"
	with open('datafiles/all_nodes_1-15-2014.csv', 'w') as wf:
		wf.write(header)
		for hour in range(0,24):
			for minute in range(0,60,15):
				frame = hour*4 + (minute/15)
				line_lead = str(frame)+','+str(hour)+':'+str(minute)+','
				rfs = 'datafiles/nodes_csv_1-15-2014_'+str(hour)+'h'\
				      +str(minute)+'m.csv'
				with open(rfs) as rf:
					rf.readline() # clear header
					while True:
						l = rf.readline()
						if l=='':
							break
						wf.write(line_lead+l)
	return

def simplify_stations_latlong():
	header1 = "lat,long\n"
	with open('datafiles/ordered_latlon.csv',"w") as wf:
		wf.write(header1)
		with open("datafiles/201402_station_data.csv") as rf:
			rf.readline()
			while True:
				l = rf.readline()
				if l == '':
					break
				d = l.split(',')
				wf.write(d[2]+','+d[3]+'\n')
	return

def append_elevation_data(fname = 'datafiles/raw_elevation_data.txt'):
	with open(fname) as ref:
		with open('datafiles/201402_station_data.csv') as sf:
			with open('datafiles/station_data.csv','w') as nsf:
				ref.readline()
				header = sf.readline().strip('\n')
				nsf.write(header+',elevation\n')
				while True:
					sl = sf.readline()
					if sl=='':
						break
					rl = ref.readline().split()
					nsf.write(sl.strip('\n')+','+rl[2]+'\n')
	return

def compile_all_routes(trip_data, station_data):
	weekday, weekend = weekday_split_trips(trip_data)
	routes = {} # k: 'start,end' v:[weekday trips, weekend trips, elevation]
	for t in weekday:
		if t.route in routes:
			routes[t.route][0] += 1
		else:
			routes[t.route] = [1,0]
	for t in weekend:
		if t.route in routes:
			routes[t.route][1] += 1
		else: # no weekday trip or weekend trip yet on this route
			routes[t.route] = [0,1]
	sdict = stations_as_dict(station_data)
	for r in routes:
		se = r.split(',')
		elev = sdict[se[1]].elevation - sdict[se[0]].elevation
		routes[r].append(elev)
	with open('datafiles/routes.csv','w') as wf:
		header = "start_station,end_station,weekday_rides,weekend_rides,elevation_change(m)\n"
		wf.write(header)
		for r in routes:
			l = r + ',' + str(routes[r][0]) + ',' + str(routes[r][1])\
				+ ',' + '{:.4}'.format(routes[r][2]) + '\n'
			wf.write(l)
	return

def tableau_friendly_routes(routefile='datafiles/routes.csv'):
	with open(routefile) as rf:
		with open('datafiles/routes_path.csv','w') as wf:
			rf.readline() # clear header
			header = "station_id,path_id,path_order,weekday_rides,weekend_rides,elevation_change(m)\n"
			wf.write(header)
			while True:
				l = rf.readline()
				if l=='':
					break
				d = l.split(',')
				wf.write(d[0]+','+d[0]+' to '+d[1]+',1,'+d[2]+','\
						 +d[3]+','+d[4])
				wf.write(d[1]+','+d[0]+' to '+d[1]+',2,'+d[2]+','\
						 +d[3]+','+d[4])
	return

def station_routes_path(station_id, routefile='datafiles/routes_path.csv'):
	# Creates a routes path csv with only routes including station_id
	newfile = routefile[:-4] + '_' + station_id + '.csv'
	with open(routefile) as rf:
		with open(newfile, 'w') as wf:
			header = rf.readline()
			wf.write(header)
			while True:
				a = rf.readline()
				if a=='':
					break
				b = rf.readline()
				if a.split(',')[0]==station_id\
				   or b.split(',')[0]==station_id:
					wf.write(a)
					wf.write(b)
	return

def compile_empty_full():
	for s in range(2,83):
		try:
			empty_full_by_station(s)
		except:
			continue
	return

def empty_full_by_station(station_id):
	station_id = str(station_id)
	rfname = 'datafiles/rebalancing_station_'+ station_id + '.csv'
	wfename = 'datafiles/empty_station_' + station_id + '.csv'
	wffname = 'datafiles/full_station_' + station_id + '.csv'
	eheader = 'station_id,num_bikes,start_moment,end_moment\n'
	fheader = 'station_id,num_docks,start_moment,end_moment\n'
	with open(rfname, 'r') as rf:
		with open(wfename, 'wb') as wfe:
			with open(wffname, 'wb') as wff:
				wfe.write(eheader) # write empty header
				wff.write(fheader) # write full header
				rf.readline() # clear header
				e = ''
				f = ''
				while True:
					l = rf.readline().strip('\r\n')
					if l == '':
						break
					d = l.split(',')
					# Check for previously empty/full station
					if e != '':
						line = e + ',' + d[3] + '\n'
						wfe.write(line)
						e = ''
					elif f != '':
						line = f + ',' + d[3] + '\n'
						wff.write(line)
						f = ''
					# Check for currently empty/full station
					if d[1] == '1' or d[1] == '0':
						e = d[0]+','+d[1]+','+d[3]
					elif d[2] == '1' or d[2] == '0':
						f = d[0]+','+d[2]+','+d[3]
	return

def percentages_empty_full():
	# Creates stations_empty_full.csv which contains percentages of problematic
	#   bike/dock counts for each station
	stations = {}
	with open('datafiles/station_data.csv') as sf: # create dict of stations
		sf.readline() # clear header
		while True:
			l = sf.readline()
			if l=='':
				break
			l = l.split(',')
			stations[l[0]] = {'station_id':l[0], 'total_seconds':0, \
			                  'distribution':[0,0,0,0,0]} # from empty to full
			start_date = datefix(l[6])
			if start_date < dt.date(2013,8,29):
				start_date = dt.date(2013,8,29)
			end_date = dt.date(2013,3,1)
			date_diff = end_date - start_date
			stations[l[0]]['total_seconds'] = date_diff.total_seconds()

	for s in stations: # load data from each station (empty_station_N.csv files)
		try:
			with open('datafiles/empty_station_'+s+'.csv') as ef: # load empties
				ef.readline()
				while True:
					l = ef.readline()
					if l=='':
						break
					d = l.split(',')
					duration = dtfix(d[2]) - dtfix(d[3])
					duration = duration.total_seconds()
					if d[1]=='1':
						stations[s]['distribution'][1] += duration
					else:
						stations[s]['distribution'][0] += duration
		except:
			continue
		try:
			with open('datafiles/full_station_'+s+'.csv') as ff: # load fulls
				ff.readline()
				while True:
					l = ff.readline()
					if l=='':
						break
					d = l.split(',')
					duration = dtfix(d[2]) - dtfix(d[3])
					duration = duration.total_seconds()
					if d[1]=='1':
						stations[s]['distribution'][3] += duration
					else:
						stations[s]['distribution'][4] += duration
		except:
			continue
		stations[s]['distribution'][2] = stations[s]['total_seconds'] - \
		                                 stations[s]['distribution'][0] - \
																		 stations[s]['distribution'][1] - \
																		 stations[s]['distribution'][3] - \
																		 stations[s]['distribution'][4]
		for i in range(5): # express as percentages
			stations[s]['distribution'][i] = stations[s]['distribution'][i] / \
			                                 stations[s]['total_seconds']

	header = 'station_id,empty,onebike,ok,onedock,full\n'
	with open('datafiles/stations_empty_full.csv','wb') as wf:
		wf.write(header)
		for s in sorted([int(i) for i in stations.keys()]):
			line = str(s)+','
			for i in range(5):
				line += '{:.5%}'.format(stations[str(s)]['distribution'][i])
				if i < 4:
					line += ','
			line += '\n'
			wf.write(line)
	return

def popular_stations(trip_data, n=5):
	# Returns a list of the n most popular stations by # trips
	s = {}
	# compile dict of trips by station
	for t in trip_data:
		if t.start_station not in s:
			s[t.start_station] = 0
		s[t.start_station] += 1
		if t.end_station not in s:
			s[t.end_station] = 0
		s[t.end_station] += 1
	# sort best
	k = sorted(s.keys(), key = lambda x: s[x])
	k.reverse()
	return k[:n]

def stations_as_dict(station_data_list):
	d = {}
	for s in station_data_list:
		d[s.id] = s
	return d

def animate_bike_availability(reb_data, time_delta=1):
	# animates the number of bikes available at a station over time
	# reb_data = a list of Rebalancing objects
	n = reb_data[0].docks
	cg = color_gradient(n)

	fig = plt.figure()
	ax = fig.add_subplot(111)
	ax.set_ylim(0,27)
	ax.set_xlim(0,2)

	anim = animation.FuncAnimation(fig, animator, blit=True)
	plt.show()

	def animator(i):
		# Plots the proper color for bike availability at the
		# given date+time tuple d_t
		b = reb_data[i].bikes
		plt.plot(1, b, '.', markersize=20.0, color=cg[b])
		return plt

	return

def color_gradient(n, s = (0,.75,0), f = (1,0,.3)):
	# returns an n-length array of color code tuples from start to finish
	# based on the color in rgb_base
	nf = float(n-1)
	g = []
	diff = ((f[0]-s[0])/nf, (f[1]-s[1])/nf, (f[2]-s[2])/nf)
	for i in xrange(n):
		g.append((s[0]+diff[0]*i, s[1]+diff[1]*i, s[2]+diff[2]*i))
	return g

if __name__ == "__main__":
	trips, stations = read_all_data()
	count_trips_by_start_hour(trips)

	# percentages_empty_full()
	'''
	trips, stations = read_all_data()
	popular = popular_stations(trips)
	print popular
	for p in popular:
		station_routes_path(p)
	'''
	'''
	trips, stations = read_all_data()
	tripgraph = TripGraph(trips)
	year = 2014
	month = 1
	day = 15
	for hour in range(24):
		for minute in range(0,60,15):
			moment = dt.datetime(year, month, day, hour, minute)
			snapshot = SystemSnapshot(tripgraph, moment)
			snapshot.output_csvs()'''
