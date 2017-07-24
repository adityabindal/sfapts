# This is a template for a Python scraper on morph.io (https://morph.io)
# including some code snippets below that you should find helpful

# import scraperwiki
# import lxml.html
#
# # Read in a page
# html = scraperwiki.scrape("http://foo.com")
#
# # Find something on the page using css selectors
# root = lxml.html.fromstring(html)
# root.cssselect("div[align='left']")
#
# # Write out to the sqlite database using scraperwiki library
# scraperwiki.sqlite.save(unique_keys=['name'], data={"name": "susan", "occupation": "software developer"})
#
# # An arbitrary query against the database
# scraperwiki.sql.select("* from data where 'name'='peter'")

# You don't have to do things with the ScraperWiki and lxml libraries.
# You can use whatever libraries you want: https://morph.io/documentation/python
# All that matters is that your final data is written to an SQLite database
# called "data.sqlite" in the current working directory which has at least a table
# called "data".

import scraperwiki
import requests
import sqlite3
import re
import hashlib
from time import sleep
import time
from random import randint
import json
import os
import geojson
import datetime
from slackclient import SlackClient
from bs4 import BeautifulSoup

# Environment Variables
base_url='https://sfbay.craigslist.org/jsonsearch/apa/sfc/?'
start_url='s=120&map=1'
ticker=0
os.environ['TZ']='US/Central'
time.tzset()

# Apartment Class
class apartment(object):
	"""Apartment class that parses Craigslist json"""
	def __init__(self, obj):
		self.bedrooms=obj['Bedrooms']
		self.price=obj['Ask']
		self.title=obj['PostingTitle']
		self.latitude=obj['Latitude']
		self.longitude=obj['Longitude']
		self.url=obj['PostingURL']
		self.postingID=obj['PostingID']
		self.postingDate=obj['PostedDate']
		self.timeStamp=time.strftime('%Y-%m-%d %H:%M:%S')
		self.neighborhood=get_neighborhood_for_point(self.latitude,self.longitude,poly)
		self.hashedTitle=hashlib.md5(str((self.title).encode('utf-8'))+str(self.price)+str(self.neighborhood)).hexdigest()	
		self.daysSince=(datetime.datetime.now()-datetime.datetime.fromtimestamp(self.postingDate)).days
	def saveToDB(self):
		scraperwiki.sqlite.save(
			unique_keys=['hashedTitle'],
			data={
					'bedrooms':self.bedrooms,
					'price':self.price,
					'title':self.title,
					'latitude':self.latitude,
					'longitude':self.longitude,
					'url':self.url,
					'postingID':self.postingID,
					'postingDate':self.postingDate,
					'hashedTitle':self.hashedTitle,
					'timeStamp':self.timeStamp,
					'neighborhood':self.neighborhood,
					'daysSince':self.daysSince
				})
	def inFilter(self):
		filterNeighborhoods=['Russian Hill','Pacific Heights','Lower Pacific Heights','Telegraph Hill']
		if self.neighborhood in filterNeighborhoods and self.price < 5000 and self.bedrooms >0 and self.bedrooms<3 and self.price>2000:
			return True
		else:
			return False

## Recursive function that combines getResults getListings
def getListings(url,ticker):
	morph_api_url = "https://api.morph.io/abgtrevize/sfapts/data.json"
	morph_api_key = os.environ['MORPH_API_KEY']
	hashList = requests.get(morph_api_url, params={
		'key': morph_api_key,
		'query': "select distinct hashedTitle from data;"
		}).content	
	time.sleep(1)
	sess=requests.Session()
	sess.headers['User-Agent']='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36'
	adapter=requests.adapters.HTTPAdapter(max_retries=100)
	sess.mount('http://',adapter)	
	response=sess.get(url)
	if response.ok:
		pass
	elif ticker<10:
		print response.reason
		print response.content
		ticker=ticker+1
		pass
	else:
		sys.exit()
#	print response.reason
	for i in response.json()[0]:
#		print i
		if 'GeoCluster' in i.keys():
			getListings(base_url+i['url'],ticker)			
		else:
#			print i
			# Create apartment class instance from object
			unit=apartment(i)
			if unit.hashedTitle in hashList:
				unit.saveToDB()
			else:
				# Send to AuntAgatha
				unit.saveToDB()
				if unit.inFilter():
					desc = "{0} | {1} | {2} | <{3}>".format(str(unit.neighborhood), unit.price, unit.title.encode('utf-8'), unit.url)	
					sc.api_call(
					    "chat.postMessage", channel=SLACK_CHANNEL, text=desc,
					    username='auntagatha', icon_emoji=':older_woman:'
					)

def point_inside_polygon(x,y,poly):
    """Return True if the point described by x, y is inside of the polygon
    described by the list of points [(x0, y0), (x1, y1), ... (xn, yn)] in
    ``poly``

    Code from http://www.ariel.com.au/a/python-point-int-poly.html which
    in turn was adapted from C code found at
    http://local.wasp.uwa.edu.au/~pbourke/geometry/insidepoly/
    """
    n = len(poly)
    inside =False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y
    return inside

def get_neighborhood_for_point(lat, lng, commareas):
    for neighborhood in commareas:
        if point_inside_polygon(lng, lat, neighborhood['geometry']['coordinates'][0][0]):
            return neighborhood['properties']['name']


if int(time.strftime('%d'))%1==0:
	SLACK_TOKEN = os.environ['MORPH_SLACK_TOKEN']
	SLACK_CHANNEL = "#auntagatha"
	sc = SlackClient(SLACK_TOKEN)
	poly=geojson.loads(open('SF Find Neighborhoods.geojson').read())['features']
	getListings(base_url+start_url,ticker)