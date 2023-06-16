import csv
import datetime
import json
import sys, os
import time


from apscheduler.schedulers.background import BackgroundScheduler
from bson import ObjectId 
from collections import Counter
from collections import defaultdict

from classes import  dataBase
from classes import news
from classes.app import app
from classes.whatsapp_client import WhatsAppWrapper

from datetime import datetime, timedelta

# pip3 install apscheduler

class Manager:
	
	def __init__(self):
		
		self.db 				=	dataBase.DataBase("db/db.json")
		self.news 				=	news.News()
		self.app				=	app
		self.client				=	WhatsAppWrapper()

	def update_and_notify(self):
		""" Get lastest news from Wordpress API"""
		print("Database update running...")
		
		latest_news		=	self.news.get_news()
		if latest_news.get("success"):
			print("Number of new news:"+str(latest_news.get("number_of_news")))
			if self.db.insert_many("news",latest_news.get("news")):
				self.__notify_users(latest_news.get("news"))	
		else:
			print("The database was already updated")

	def	confirm_subscription(self):
		print("Running confirm subscription task ...")
		#button	=	self.client.create_button("Olá, nosso robô 🤖 não gostar de ser spam 🚮. Você quer continuar recebendo nosso conteúdos?", "Sim", "SUBSCRIPTION_BTN_YES", "Não", "SUBSCRIPTION_BTN_NO" )
		button	=	self.client.create_button("🤖 Olá, Você quer continuar recebendo nosso conteúdos?", "Sim", "SUBSCRIPTION_BTN_YES", "Não", "SUBSCRIPTION_BTN_NO" )		
		last_30_day	=	 datetime.now()	 -timedelta(days = 30)
		r		=	self.db.find("users", { "$expr": { "$lte": [{ "$last": "$subscription_date" }, last_30_day]}, "active":{ "$eq": True } },{"_id":0} )
		if r.get("success"):
			users =	r.get("docs")
			for user in users:	
				self.db.update_one("users",{"user_id":{"$eq":user.get("user_id")}}, { "$set": { "verified": False} })
				self.client.send_message(user.get("user_id"), "interactive", button)
				print("user",user)

	def	__pre_process(self,user,last_news):
		user_topics_prefs		=	set(	user.get("topics_prefs")	)
		user_locations_prefs	=	set(	user.get("locations_prefs")	)	
		user_all_content		=	user.get("all_content")
		user['news']	=	[]			
		news_locations	=	set()
		urls	=	[]
		titles	=	[]
		for	news in last_news:
			try:
				news_topics	=	set(news.get("News_topics"))
			except:
				news_topics	=	set()
				
			if news['URL'] not in urls and news['Language']=="pt-BR" and  news['Title'] not in titles:
				urls.append(news['URL'])
				titles.append(news['Title'])
				if news.get("location").get("location"):
					try:
						news_locations	=	set([news.get("location").get("state")])
					except:
						news_locations	=	set()		
				
				n	= {
						"Title":news.get("Title") ,
						"Description":news.get("Description"),
						 "Author":news.get("Author"),
						 "Subtopics":news.get("Subtopics"),
						 "URL":news.get("URL"),
						 "news_source":news.get("news_source")
					}

				
				if	user_all_content:
					user['news'].append(n)
				else:
					if user_topics_prefs.intersection(news_topics):
						user['news'].append(n)
					elif user_locations_prefs.intersection(news_locations):
						user['news'].append(n)
		return user
						
	
	def	__create_messages(self,users_db, news):
		users	=	[]
		for user in users_db:
			users.append(self.__pre_process(user,news))
		
		return users



	def __notify_users(self,news):
		r		=	self.db.find("users", {"active":{ "$eq": True }}, {"_id":0} )
		if r.get("success"):
			users =	r.get("docs")
			messages	=	self.__create_messages(users, news)	
			for message in messages:
				user_id = message.get("user_id")
				print("user_id$>",user_id)
				msg	={}
				for n in message.get("news"):
					msg["Title"] 		=	n.get("Title")
					msg["Description"]	=	n.get("Description")
					msg["URL"]			=	n.get("URL")
					msg["Author"]		=	n.get("Author")	
					source				=	n.get("news_source")
					subtopics			=	n.get("Subtopics")
					
					if	source=="plenamata.eco":
						if  ("Opinião" in subtopics):
							r =	self.client.send_message(user_id, "opinion",msg, log=True)
						elif  ("Boas iniciativas" in subtopics):
							r =	self.client.send_message(user_id, "stories",msg, log=True)										
					
					if	source=="infoamazonia.org":
						if  ("Opinião" in subtopics):
							r =	self.client.send_message(user_id, "opinion",msg, log=True)
						else:
							r =	self.client.send_message(user_id, "stories",msg, log=True)		
					
					#print(r)
	
	def start_scheduler(self):
		scheduler = BackgroundScheduler(daemon=True, timezone="America/Sao_Paulo")
		
		#Each X minutes or hours
		scheduler.add_job(self.update_and_notify, trigger="interval", minutes=10) #change to minutes
		
		#default time
		#scheduler.add_job(self.update_and_notify, trigger='cron', hour='9', minute='00')
		
		#confirm_subscription
		scheduler.add_job(self.confirm_subscription, trigger='cron', day=28, hour='1', minute='20')

		#update_subscription
		#scheduler.add_job(self.update_subscription, trigger='cron', hour='9', minute='00')		

		
		scheduler.start()	


	def start(self):
		self.start_scheduler()
		self.update_and_notify()
		self.app.run(debug=True, host='0.0.0.0', port=5000)#,ssl_context=('cert.pem', 'key.pem'))
