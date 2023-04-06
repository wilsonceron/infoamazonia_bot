import copy
import numpy as np
import json
import os
import pickle
import pymongo
from bson.binary import Binary
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from pymongo.errors import ConnectionFailure

class DataBase:


	def __init__( self, configfile ):

		try:
			config_file	=	open('db/db.json', "r")
		except FileNotFoundError as e:
			print("DataBase config not found!")
			exit(1)
	
		try:
			db_config		=	json.load(config_file)
			host			=	db_config.get("host")
			port			=	db_config.get("port")
			self.db_name	=	db_config.get("dbname")
		except json.decoder.JSONDecodeError as e:
			print("Invalid database file, check your db.json")
			exit(1)

		try:
			self.client	=	MongoClient(host, port)
			self.db		=	self.client[ self.db_name ]
			self.client.admin.command('ismaster')
		except ConnectionFailure:
			print("Database server not available")
			exit(1)
		
	
	def checkConnection (self):
		try:
			info    = self.client.server_info()
			return True
		except ServerSelectionTimeoutError:
			return False

	def get_last_n_doc(self, collection_name, query, options, sort_options, limit):
		try:
			collist = self.db.list_collection_names()

			if collection_name in collist:
				coll	=	 self.db[collection_name]
				doc		=	coll.find(query,options).sort(sort_options).limit(limit)
				r		=	copy.copy(doc)
				if	len(list(r)):
					return {"success":True, "docs":doc}
					
				return {"success":False}

		except Exception as e:
			print(e)
			return {"success":False}

		

	def find(self, collection_name, query, params):
		try:
			collist = self.db.list_collection_names()
			if collection_name in collist:
				coll	=	 self.db[collection_name]
				doc		=	coll.find(query, params)
				r		=	copy.copy(doc)
				if	len(list(r)):
					return {"success":True, "docs":doc}
			
			return {"success":False}
		
		except Exception as e:
			print(e)
			return {"success":False}

	def insert_many( self, collection_name, docs):
		coll  =  self.db[ collection_name ]
		result=True
		for i in range(10):
			try:
				coll.insert_many(docs)
				return result
			except pymongo.errors.BulkWriteError as e:
				print(e)		
			except Exception as e:
				print(e)
		
		result = False

		




	def delete_one( self, collection_name, query):
		#Example .db.delete_one("users",{"user_id":{"$eq":user_id}})
		coll  =  self.db[ collection_name ]
		result=True
		try:
			r = coll.delete_one(query)
			#print(r.deleted_count)
		except Exception as e:
			print(e)
			result = False

		return result	



	def update_one( self, collection_name, query, newvalues):
		#Example db.update_one("users",{"user_id":{"$eq":user_id}}, { "$set": { "active": False } })
		coll  =  self.db[ collection_name ]
		result=True
		try:
			r = coll.update_one(query, newvalues)
			#print(r.modified_count)
		except Exception as e:
			print(e)
			result = False

		return result	

