'''
constant variables for bikeshare analysis
'''
import datetime as dt
import simplejson as json

day_one = dt.date(2013,8,29) # A Thursday!

data_file_lengths = {"rebalancing": 453902,\
					 "station":     70,\
					 "weather":     921,\
					 "trip":        144016}

data_file_names = {}
for f in ["trip", "weather"]:
	data_file_names[f] = "datafiles/201402_" + f + "_data.csv"
data_file_names["station"] = "datafiles/station_data.csv"
data_file_names["rebalancing"] = "datafiles/rebalancing_compressed_data.csv"

# center_latlon is the "center" lat,lon pair for a city
center_latlon = {"San Francisco": [37.77865, -122.418235],\
                 "San Jose":      [37.337391,-121.886995],\
				 "Redwood City":  [37.486078,-122.232089],\
				 "Palo Alto":     [37.443988,-122.164759],\
				 "Mountain View": [37.389218,-122.081896]}

# scales lat/lon degrees to meters in each city
latlon_scale = {"San Francisco":  [110992.27,88095.77],\
                "San Jose":       [110983.95,88616.81],\
				"Redwood City":   [110986.75,88441.83],\
				"Palo Alto":      [110985.96,88491.42],\
				"Mountain View":  [110984.93,88555.88]}

# station name<->id dicts:
with open("datafiles/station_dict.txt") as f:
	station_name_to_id = json.loads(f.read())
station_id_to_name = {}
for k in station_name_to_id:
	station_id_to_name[station_name_to_id[k]] = k
	
# stations by city
stations_by_city = {"San Francisco":['41','42','45','46','47','48','49','50','51','53','54','55','56','57','58','59','60','61','62','63','64','65','66','67','68','69','70','71','72','73','74','75','76','77','82'],\
					"San Jose":['2','3','4','5','6','7','8','9','10','11','12','13','14','16','80'],\
					"Redwood City":['21','22','23','24','25','26','83'],\
					"Palo Alto":['34','35','36','37','38'],\
					"Mountain View":['27','28','29','30','31','32','33']}
					
city_codes = {"San Francisco":"SF","San Jose":"SJ","Redwood City":"RC","Palo Alto":"PA","Mountain View":"MV"}