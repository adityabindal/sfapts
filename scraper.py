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
from time import sleep
import time
from random import randint
import json
import os
from bs4 import BeautifulSoup

# Environment Variables
base_url='https://sfbay.craigslist.org/jsonsearch/apa/sby/?'
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
		self.hashedTitle=hash(self.title)
		self.timeStamp=time.strftime('%Y-%m-%d %H:%M:%S')
	def saveToDB(self):
		scraperwiki.sqlite.save(
			unique_keys=['postingID','hashedTitle','timeStamp'],
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
					'timeStamp':self.timeStamp
				})

## Recursive function that combines getResults getListings
def getListings(url,ticker):
	sess=requests.Session()
	sess.headers['User-Agent']='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36'
	adapter=requests.adapters.HTTPAdapter(max_retries=100)
	sess.mount('http://',adapter)	
	response=sess.get(url)
	if response.ok:
		pass
	elif ticker<10:
		print response.reason
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
			# Save to SQLDB
			unit.saveToDB()

getListings(base_url+start_url,ticker)