# Homepage

In order to develop this bot, it was imperative to integrate the WhatsApp Business API with the WordPress API. Essentially, the bot functions as follows: a scheduler is employed to periodically check for newly published articles on WordPress. Upon discovering a new article, it is stored in the database and initiates a notification to the Manager, who retrieves all active users from the database. Subsequently, the users' preferences are cross-referenced with the article's topics. If the preferences align with the article's themes, a message is dispatched to the user.

## Classes


### App
This class contain the routes for WhatsApp Busines API

#### Webhook

The webhook route is triggered when a new message arrives for the bot. When this happens, the message is sent to the `process_webhook_notification` method of the `whatsapp_client` class.

``` py linenums="1"
	@app.route("/webhook/", methods=["POST", "GET"])
	def webhook_whatsapp():
		"""__summary__: Get message from the webhook"""

		if request.method == "GET":
		    if request.args.get("hub.verify_token") == "":
		        return request.args.get("hub.challenge")
		    return "Authentication failed. Invalid Token."

		client = WhatsAppWrapper()

		response = client.process_webhook_notification(request.get_json())

		# Do anything with the response
		# Sending a message to a phone number to confirm the webhook is working

		return jsonify({"status": "success"}, 200)
```


### Bot

#### Call the Manager


``` py linenums="1"
	manager	= manager.Manager()
	manager.start()
```

### Database

The Database class contains basic methods (save, read, update, and delete) to manage news and users in MongoDB.


#### Check connection

This method check if database is online

``` py linenums="1"
	def checkConnection (self):
		try:
			info    = self.client.server_info()
			return True
		except ServerSelectionTimeoutError:
			return False
```

#### Get last n docs

This method retrieves the last N documents inserted in the database.

``` py linenums="1"
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
```

#### Find a document

This method retrieves a document from the database using a search query.

``` py linenums="1"
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
```

#### Insert a document

This method insert N document to the database.

``` py linenums="1"
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
```

#### Delete a document

This method deletes a document in the database based on the search query.

``` py linenums="1"
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
```

### Manager
The Manager class is responsible for application management, coordinating the collection and storage of news, as well as the message dispatch to users.

#### Get last news and call the nofitification
The update_and_notify method is responsible for updating the database with the latest news obtained from the WordPress API and notifying users if new news is available.

``` py linenums="1"
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
```

#### Get user prefrences and news topics
The __pre_process method is a pre-processing step that takes a user and a list of last news as inputs. It extracts the user's topic and location preferences and filters the news based on these preferences. Unique news items that meet certain conditions are added to the user's news list, considering options for receiving all content or specific topics only. The method ensures uniqueness of URLs and titles, extracts relevant information from the news items, and constructs a dictionary object representing each news item. The updated user object with filtered news items is returned.

``` py linenums="1"
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
```

#### Create a message for each user
The __create_messages method takes user data and news as input. It processes each user's data and the news to create customized messages for each user. The processed user data is stored in a list, which is then returned. The method essentially generates messages tailored to individual users based on their data and the provided news.

``` py linenums="1"
	def	__create_messages(self,users_db, news):
		users	=	[]
		for user in users_db:
			users.append(self.__pre_process(user,news))
		
		return users
```

#### Check for new news 
The start_scheduler method sets up a scheduler object and schedules a recurring task to check for new news. It creates a BackgroundScheduler object with a daemon thread and a specified timezone. The scheduled task, update_and_notify, is triggered at regular intervals of every hour. If desired, the interval can be adjusted to minutes instead of hours by modifying the minutes parameter in the scheduler.add_job line. This method enables the automated execution of the update_and_notify task on a regular schedule.


``` py linenums="1"
	def start_scheduler(self):
		""" Create a scheduler object and schedule a task that check for new news each hour"""
		scheduler = BackgroundScheduler(daemon=True, timezone="America/Sao_Paulo")
		
		#Each X minutes or hours
		scheduler.add_job(self.update_and_notify, trigger="interval", minutes=60) #change to minutes
```

#### Incialization
The start method begins the execution of the application by setting up the scheduler, checking for new news, and initiating the application to run in debug mode. It starts the scheduler to periodically check for new news, immediately checks for updates and notifies users, and then launches the application to listen for incoming requests on port 5000. 

``` py linenums="1"
	def start(self):
		self.start_scheduler()
		self.update_and_notify()
		self.app.run(debug=True, host='0.0.0.0', port=5000)#,ssl_context=('cert.pem', 'key.pem'))
```

### News
The News class is responsible for connecting to the WordPress API and collecting the latest published news. It also handles the storage of news in the database. The get_news method provides the processed news with the most important fields in JSON format.

#### Incialization
 The __init__ method serves as the constructor for a class. It connects to a WordPress API and a database, and if the connections are successful, it returns True. However, if there is an error connecting to the WordPress API or with the database, it prints an error message and returns a dictionary with a "success" key set to False. The method initializes the necessary connections and returns an indicator of success or failure.

``` py linenums="1"
	def __init__( self):
		try:
			response	=	requests.get("https://infoamazonia.org/wp-json/wp/v2/posts")
			response	=	requests.get("https://plenamata.eco/wp-json/wp/v2/posts")
			self.db		=	dataBase.DataBase("db/db.json")
		except requests.exceptions.ConnectionError:
			print("Error connecting to Wordpress API")
			return {"success":False}
```

	
#### Get news

The get_news method retrieves the latest news from multiple APIs and returns a list of preprocessed JSON objects containing the most relevant fields. It iterates over a list of API sources, their URLs, and language preferences. The method sends requests to each API, retrieves the response, and extracts the necessary information from the JSON data. It handles pagination if applicable and populates the news dictionary with details such as ID, collection date, location, title, published date, author, description, URL, site, subtopics, keywords, language, and news source. It checks for duplicate news entries and filters out already existing news by comparing the title, URL, and ID with the database records. The method assigns the news source, fetches topics associated with the news, and appends the news to the documents list. Finally, the method returns a dictionary with the success status, the list of news documents, and the total number of news items.
``` py linenums="1"
	def get_news(self):
		apis=[]
		apis.append({"api_source":"infoamazonia_pt","lang":"pt", "api_url":"https://infoamazonia.org/wp-json/wp/v2/posts"})
		apis.append({"api_source":"infoamazonia_en","lang":"en", "api_url":"https://infoamazonia.org/en/wp-json/wp/v2/posts"})		
		apis.append({"api_source":"infoamazonia_es","lang":"es", "api_url":"https://infoamazonia.org/es/wp-json/wp/v2/posts"})		

		apis.append({"api_source":"plenamata_pt","lang":"pt", "api_url":"https://plenamata.eco/wp-json/wp/v2/posts"})
		apis.append({"api_source":"plenamata_en","lang":"en", "api_url":"https://plenamata.eco/en/wp-json/wp/v2/posts"})		
		apis.append({"api_source":"plenamata_es","lang":"es", "api_url":"https://plenamata.eco/es/wp-json/wp/v2/posts"})		
		
		documents	=	[]

		for  api in apis:
			api_source	=	api.get("api_source")
			api_url		=	api.get("api_url")
			lang		=	api.get("lang")		
			response 	=	requests.get(api_url)
			headers		=	response.headers
			
			number_of_pages	= 	 int(headers.get('X-WP-TotalPages'))
			number_of_posts	=	headers.get('X-WP-Total')
			number_of_pages	= 	1		
			stop_update		=	False
			
			for page in iter(range(number_of_pages)):
				if stop_update:
					break
				
				api_url_page	=	api_url+"?_embed=wp:term?per_page=100&page="+str(page+1)
				response		=	requests.get(api_url_page)
				print("API: "+api_source," Page {}".format(page+1))
				if response.ok:
					for idx, item in enumerate(response.json()):
						#if idx==1:
						#	break
						#print("*"*100)
						#print()
						#pp.pprint(item)
						#print()			
						#print("*"*100)			
						news					=	{}
						meta					=	item.get("meta")
						location				=	meta.get("_related_point")
						location_dict			=	{}
						news["success"]			=	True
						news["_id"]				=	api_source+"_"+str(item.get("id"))
						news["collection_date"]	=	datetime.now(pytz.timezone('America/Sao_Paulo'))
						if location:
							try:
								location_dict['location']		=	True
								location_dict['lat']			=	location[0].get('_geocode_lat')
								location_dict['lon']			=	location[0].get('_geocode_lon')

								location_dict['country']		=	location[0].get("_geocode_country")	
								location_dict['region']			=	location[0].get('_geocode_region_level_1')
								location_dict['state']			=	location[0].get('_geocode_region_level_2')
								location_dict['metropolitan']	=	location[0].get('_geocode_region_level_3')
								location_dict['city']			=	location[0].get("_geocode_city")
								location_dict['city_region']	=	location[0].get("_geocode_city_level_1")	
								location_dict['address']		=	location[0].get('_geocode_full_address')
							except:
								location_dict['location']		=	False
						else:
							location_dict['location']			=	False

						news['location']=location_dict


						if(	set(['yoast_head_json']).issubset(set(item.keys()))):					
							yoast = item.get('yoast_head_json')	

							self.__check_news_field(yoast,news,"og_title","Title","")
							self.__check_news_field(yoast,news,"article_published_time","Published_date","")					
							self.__check_news_field(yoast,news,"author","Author","")				
							self.__check_news_field(yoast,news,"description","Description","")
							self.__check_news_field(yoast,news,"og_url","URL","")
							self.__check_news_field(yoast,news,"og_site_name","site","")

							self.__check_news_field(yoast.get('schema').get("@graph")[0],news,"articleSection","Subtopics",[])
							self.__check_news_field(yoast.get('schema').get("@graph")[0],news,"keywords","Keywords",[])
							self.__check_news_field(yoast.get('schema').get("@graph")[0],news,"inLanguage","Language","")						
							self.__set_source(news)
								
							if news["success"]:
								r =	self.db.get_last_n_doc("news", {"$or":[ {"Title":{ "$eq":news['Title']}}, {"URL":{ "$eq": news['URL']} },{"_id":{ "$eq": news['_id'] }}]}, {"Title":1,"URL":1, "_id":1}, [('Published_date', -1)],1)
								if r.get("success"):
									stop_update	= True
									break
											
								print(api_source,news['URL'])
								news["api_source"]	=	api_source
								self.__get_topics(news)
								documents.append(news)	

		
		
		if len(documents)>0:
			return {"success":True, "news":documents, "number_of_news":len(documents)}
		else:	
			return {"success":False}		
		

		return documents						

```

#### Get the news source URL
The __set_source method sets the news_source attribute based on the news URL. If the URL contains "infoamazonia.org", it assigns the value "infoamazonia.org" to the news_source attribute. If the URL contains "plenamata.eco", it assigns the value "plenamata.eco" to the news_source attribute. Otherwise, it sets the news_source attribute to an empty string and marks the success attribute of the news as False.

``` py linenums="1"
	def __set_source(self,news):
		if "//infoamazonia.org/" in news["URL"]:
			news["news_source"]	="infoamazonia.org"
		elif "//plenamata.eco/" in news["URL"]:
			news["news_source"]	="plenamata.eco"
		else:
			news["news_source"]	=""
			news["success"]	=	False
```
#### Validate a news
The __check_news_field method validates and retrieves important fields from an api_dict, assigning them to corresponding fields in the news dictionary, while handling exceptions and setting the  success attribute is appropriately set.

``` py linenums="1"
	def __check_news_field(self,api_dict,news,field,field_name,empty):
		try:
			news[field_name] =	api_dict.get(field)			
			if	not news[field_name]:
				news[field_name]	=	empty
				if ( (field=="title") or (field=="description") or (field=="URL") ):
					news["success"]	=	False
		
		except Exception as e:
			print(field+" exception")
			print(e)
			news[field_name]	=	empty
			if ( (field=="title") or (field=="description") or (field=="URL") ):
				news["success"]	=	False
```

#### Getting topics of the news
The __get_topics method assigns a single topic to a news article based on its subtopics. It defines sets of topics related to environmental damage, protected areas, communities, climate change, conservation, and politics/economy. The method checks the intersection between the news article's subtopics and these predefined sets to determine the appropriate topic(s) for the article. The identified topics are stored in the News_topics field of the news dictionary. If an exception occurs during the process, an empty list is assigned to News_topics.
``` py linenums="1"
	def __get_topics(self,news):
		danos_ambientais	=	set(	["Desmatamento","Queimadas","Garimpo","Mineração","Grilagem","Agronegócio","Agropecuária","Madeira","Poluição","Petróleo","Pecuária","Crime ambiental","Estradas","Água","Hidrelétricas","Sistemas de Monitoramento"])
		areas_Protegidas	=	set(	["Áreas Protegidas","Unidades de Conservação","Terras indígenas","Pantanal","Questão fundiária","Indígenas"])
		Povos				=	set(	["Cultura","Covid-19","Saúde","Defensores ambientais","Memória","Quilombolas","Mulher","Emigrar","Educação","Paz e Guerra","Religião","Indígenas"])
		mudanca_climatica	=	set(	["Mudança climática","Crédito de carbono","COP27","COP"])
		conservacao			=	set(	["Biodiversidade","Ciência","Sistemas de Monitoramento","Conservação","Regeneração"])
		politica_economia	=	set(	["Sustentabilidade","Política","Política pública","Bioeconomia","Eleições 2022","Eleições","Corrupção","Produtos sustentáveis","Milícia","Congresso Nacional","Supremo"])
		try:
			news_subtopics	=	set(	news['Subtopics'])
			news_topics=[]
			if news_subtopics.intersection(danos_ambientais) or "plenamata" in news['news_source']:
				news_topics.append("danos_ambientais")
			
			if news_subtopics.intersection(areas_Protegidas):
				news_topics.append("areas_Protegidas")

			if news_subtopics.intersection(Povos):
				news_topics.append("povos")

			if news_subtopics.intersection(mudanca_climatica):
				news_topics.append("mudanca_climatica")

			if news_subtopics.intersection(conservacao):
				news_topics.append("conservacao")

			if news_subtopics.intersection(politica_economia):
				news_topics.append("politica_economia")

			news['News_topics']= news_topics
		except:
			news['News_topics']=[]
```


### whatsapp_client
The Whatsapp_client class is responsible for the communication between the bot and the WhatsApp Business API. It processes user messages and responds to users based on their choices.

#### Dictionary of messages
This method returns the desired message based on the input attribute. 

``` py linenums="1"
	def get_messages(self, message):

		welcome="Boas vindas! Sou o robô de notícias da InfoAmazonia 🍃\nEnvio os conteúdos recém-publicados que mais te interessam sobre a Amazônia brasileira. O serviço é *GRATUITO*.\n\n📌 Para voltar a ver estas opções, me envie *MENU* a qualquer momento.\n📌 Se desejar parar de receber meus conteúdos, escreva *CANCELAR* a qualquer momento e não te mandarei mais notícias."
		
		image		=	"Desculpe, mas eu ainda não consigo visualizar imagens. 😥\nPor favor, escolha uma das opções! 😃"
		document	=	"Desculpe, mas eu ainda não consigo ler documentos. 😥\nPor favor, escolha uma das opções! 😃"
		location	=	"Desculpe, mas eu ainda não entendo localizações compartilhadas. 😥\nPor favor, escolha uma das opções! 😃"
		contacts	=	"Desculpe, mas eu ainda não reconheço contatos. 😥\nPara compartilhar este serviço com amigos, por favor, peça que me escrevam diretamente! 😃"

		video		=	"Desculpe, mas eu ainda não consigo assistir vídeos. 😥\nPor favor, escolha uma das opções! 😃"
		audio		=	"Desculpe, mas eu ainda não consigo escutar áudios. 😥\nPor favor, escolha uma das opções! 😃"
		sticker		=	"Desculpe, mas eu ainda não consigo visualizar figurinhas. 😥\nPor favor, escolha uma das opções! 😃"
		cancel_1	=	"Já cancelei sua inscrição e não enviarei novos conteúdos 😥. Se desejar voltar a receber, é só enviar *MENU*."
		cancel_0	=	"Eu já havia cancelado sua inscrição e você vai continuar sem receber novos conteúdos da InfoAmazonia 😥. Quando quiser voltar a receber, é só escrever *MENU*."
		all_content	=	"Obrigado pela sua inscrição! 🙌 Em breve você começará a receber nosso conteúdo no seu WhatsApp 📲. Se quiser ver as opções outra vez, é só digitar *MENU*."
		
		about		=	"InfoAmazonia é um meio de comunicação que utiliza dados, mapas e reportagens geolocalizadas para revelar a importância global da maior floresta tropical do planeta. " 
		about		=	about +"Vislumbramos um mundo onde a informação e o conhecimento transformam a forma como nos relacionamos com os territórios amazônicos em toda a sua  diversidade, ampliando a compreensão do papel vital desempenhado pela  Amazônia por todos."
		about		=	about +"Trazemos contexto e aprofundamento à cobertura jornalística, indo além das notícias imediatas e buscando compreender as causas dos temas reportados para fomentar o debate público e estimular ações transformadoras."
	
		main_menu =	{
					"type": "list",
					"header": {
					  "type": "text",
					  "text": "Envio apenas os conteúdos do seu interesse."
					},
					"body": {
					  "text": "Você quer ser informado sobre novos conteúdos de quais temas ou estados?"
					},
					"footer": {
					  "text": "Escolha uma das opções"
					},
					"action": {
					  "button": "Toque aqui!",
					  "sections": [
						{
						  "title": "personalize o conteúdo",
						  "rows": [
							{
							  "id": "MAIN_ALL_CONTENT",
							  "title": "Tudo",
							  "description": "Todos os conteúdos da InfoAmazonia 🌳"
							},
							{
							  "id": "MAIN_LOCATIONS",
							  "title": "Estados",
							  "description": "Escolha conteúdos sobre determinados estados 🇧🇷"
							},
							{
							  "id": "MAIN_TOPCIS",
							  "title": "Temas",
							  "description": "Escolha conteúdos sobre determinados temas ✅"
							},
							{
							  "id": "MAIN_ABOUT",
							  "title": "Sobre",
							  "description": "Saiba mais sobre a InfoAmazonia 🍃"
							},
						  ]
						}
				 
					  ]
					}
				  }
		if message=="main_menu":
			return main_menu

		if message=="welcome":
			return welcome

		if message=="image":
			return image

		if message=="document":
			return document
			
		if message=="location":
			return location
			
			
		if message=="contacts":
			return contacts						


		if message=="video":
			return video
			
		if message=="audio":
			return audio			
			
		if message=="sticker":
			return sticker		

		if message=="cancel_0":
			return cancel_0	

		if message=="cancel_1":
			return cancel_1	

		if message=="ALL_CONTENT":
			return all_content	

		if message=="about":
			return about				  
```

#### Saving the state of conversation

This method saves on database if the message was sent, deliverd or read

``` py linenums="1"
	def save_conversation_state(self, response,message):
		
		response_date	=	datetime.strptime(response.headers.get("DATE"), '%a, %d %b %Y %H:%M:%S GMT')
		response		=	response.json()
		user_id			=	response.get('contacts')[0].get("wa_id")
		wamid			=	response.get('messages')[0].get('id')
		print("  wamid$>",wamid)
		url				=	message.get("URL")
		
		self.db.insert_many("messages",[{"response_date": response_date, "_id": wamid, "wamid":wamid, "user_id":user_id, "sent":False,"delivered":False,"read":False, "message":url}])
```
		
#### Stories message template
This method return  the json of the template

``` py linenums="1"
	def get_stories_template(self,payload, message):
		payload["template"] =   {
									"name": "posts_stories",
									"language": {
									  "code": "pt_BR"
									},
									"components": [
									  {
										"type": "body",
										"parameters": [
										  {
											"type": "text",
											"text": message.get("Title")
										  },
										  {
											"type": "text",
											"text": message.get("Description")
										  },
										   {
											"type": "text",
											"text": message.get("Author")
										  },
										  {
											"type": "text",
											"text": message.get("URL")
										  }
										]
									  }
									]
								  }
		
		return payload
	
```


#### Opinion message template
This method return  the json of the template

``` py linenums="1"
	def get_opinion_template(self,payload, message):
		payload["template"] =   {
									"name": "posts_opinion",
									"language": {
									  "code": "pt_BR"
									},
									"components": [
									  {
										"type": "body",
										"parameters": [
										  {
											"type": "text",
											"text": message.get("Title")
										  },
										  {
											"type": "text",
											"text": message.get("Description")
										  },
										   {
											"type": "text",
											"text": message.get("Author")
										  },
										  {
											"type": "text",
											"text": message.get("URL")
										  }
										]
									  }
									]
								  }
		
		return payload
	
```

#### Sending a message

This method is responsible for sending a WhatsApp message to the user. It takes parameters such as the recipient's phone number, message type, and the actual message content. The method constructs a payload with the necessary information and determines the appropriate message type based on the input. If the message type is "text", the payload is set accordingly with the text body. For "interactive" messages, the payload includes the interactive message content. In the case of "stories" or "opinion" message types, the payload is modified by calling helper methods to generate the appropriate templates. The method then makes a POST request to the WhatsApp API's messages endpoint, passing the payload as JSON data. If the response status code is 200 (indicating a successful request), the method may save the conversation state and returns the response. Otherwise, it prints the response JSON and waits briefly before returning the response.

``` py linenums="1"
def send_message(self, recipient_phone_number, message_type, message, log=None):
		payload = { 
			"messaging_product": "whatsapp", 
			"to": recipient_phone_number 
		}

		if message_type=="text":
			payload['type'] = "text"
			payload['text'] =  {"body": message}
			
		if message_type=="interactive":
			payload['type'] = "interactive"
			payload['interactive'] = message

		if message_type=="stories":
			payload['type'] = "template"
			payload	=	self.get_stories_template(payload,message)

		if message_type=="opinion":
			payload['type'] = "template"
			payload	=	self.get_opinion_template(payload,message)

		
		#print(payload)
		#print(f"{self.API_URL}/messages",self.headers, payload)	
		response = requests.post(f"{self.API_URL}/messages", headers=self.headers, data=json.dumps(payload), timeout=10)
		time.sleep(3)
		if (response.status_code==200):
			if log:
				self.save_conversation_state(response,message)
			return response
		else:
			print(response.json())
			time.sleep(0.5)
	
		return response
```

#### Processing other types of contents

This method returns a message to the user based on the type of content they send, such as audio, location, contact, or image.

``` py linenums="1"
	def	process_diff_contents(self,response):
		if response.get("message_type")=="image":
			self.send_message(response.get("user_id"), "text", self.get_messages("image"))						
			return True	
		if response.get("message_type")=="document":
			self.send_message(response.get("user_id"), "text", self.get_messages("document"))	
			return True			
		if response.get("message_type")=="contacts":
			self.send_message(response.get("user_id"), "text", self.get_messages("contacts"))	
			return True	
		if response.get("message_type")=="location":
			self.send_message(response.get("user_id"), "text", self.get_messages("location"))	
			return True	
		if response.get("message_type")=="video":
			self.send_message(response.get("user_id"), "text", self.get_messages("video"))	
			return True	
		if response.get("message_type")=="audio":
			self.send_message(response.get("user_id"), "text", self.get_messages("audio"))	
			return True	
		if response.get("message_type")=="sticker":
			self.send_message(response.get("user_id"), "text", self.get_messages("sticker"))	
			return True	

		return False	

```

#### Main menu

Main menu and welcome messages

``` py linenums="1"
	def main_menu(self,response):
		self.send_message(response.get("user_id"), "text", self.get_messages("welcome"))
		self.send_message(response.get("user_id"), "interactive", self.get_messages("main_menu"))

```

#### Get user preferences

Get user preferences from database

``` py linenums="1"
	def __get_user_prefs(self, user_id):
		r		=	self.db.find("users", {"user_id":{ "$eq": user_id }}, {"_id":0} )
		if r.get("success"):
			user =	r.get("docs")[0]
			if user.get("topics_prefs")==None:
				user["topics_prefs"]	=	[]
			
			if user.get("locations_prefs")==None:
				user["locations_prefs"]		=	[]
			
			if	user.get("unsubscribed_date")==None:
				user["unsubscribed_date"]	=	[]
			
			if	user.get("subscription_date")==None:
				user["subscription_date"]=	[]
			u =  {
						"user_id"				:	user.get("user_id"),
						"name"					:	user.get("name"),
						"active"				:	user.get("active"),
						"all_content"			:	user.get("all_content"),
						"topics_prefs"			:	user.get("topics_prefs"),
						"locations_prefs"		:	user.get("locations_prefs"),
						"subscription_date"		:	user.get("subscription_date"),
						"unsubscribed_date"		:	user.get("unsubscribed_date"),
					}
			return {"success":True, "user":u}
		
		return	{"success":False}

```


#### Create a user

Create a user json object

``` py linenums="1"
	def __create_user(self, user_id, name, active, all_content, topics_prefs,  locations_prefs):

		doc =  {
					"user_id"				:	user_id,
					"_id"					:	user_id,
					"name"					:	name,
					"active"				:	active,
					"all_content"			:	all_content,
					"topics_prefs"			:	topics_prefs,
					"locations_prefs"		:	locations_prefs,
					"subscription_date"		:	[datetime.now(pytz.timezone('America/Sao_Paulo'))],
					"unsubscribed_date"		:	[],
					"verified"				:	True,
				}
		return doc
		
```

#### Choose all content

Set user preference and send a message

``` py linenums="1"
	def __choose_all(self, user, response):

		if user["new"]:
			user.pop("new")
			user["all_content"]	= True
			self.db.insert_many("users",[user])
			self.send_message(user.get("user_id"), "text", self.get_messages("ALL_CONTENT"))
			return True
		
		if user.get("all_content"):
			self.send_message(user.get("user_id"), "text", "Você já estava cadastrado para receber todo nosso conteúdo 😃")
		else:
			self.db.update_one("users",{"user_id":{"$eq":user.get("user_id")}}, { "$set": { "active": True, "all_content": True, "topics_prefs":[],  "locations_prefs":[]  } })				
			self.send_message(user.get("user_id"), "text", self.get_messages("ALL_CONTENT"))	
		
```

#### Create a single button 

Create a button based on input parameters

``` py linenums="1"
	def create_button(self, button_message, response_1, response_1_id, response_2, response_2_id ):
		button	= {
		"type": "button",
		"header": {
		  "type": "text",
		  "text": button_message
		},
		"body": {
		  "text": "  ‎   "
		},
		"action": {
		  "buttons": [
			{
			  "type": "reply",
			  "reply": {
				"id": response_1_id,
				"title": response_1 
			  }
			},
			{
			  "type": "reply",
			  "reply": {
				"id": response_2_id,
				"title": response_2
			  }
			}
		  ] 
		}   
		}

		return button	
		
```


#### Saving user prefrences

This method salve user's preferences on database

``` py linenums="1"
	def __save_user_prefs(self, user):
		if user["new"]:
			user.pop("new")
			self.db.insert_many("users",[user])	
		else:
			if user.get("active"):
				self.db.update_one("users",{"user_id":{"$eq":user.get("user_id")}}, { "$set": {"topics_prefs": user.get("topics_prefs"), "locations_prefs":user.get("locations_prefs") } })				
			else:
				sub_date	=	datetime.now(pytz.timezone('America/Sao_Paulo'))
				user.get("subscription_date").append(sub_date)
				self.db.update_one("users",{"user_id":{"$eq":user.get("user_id")}}, { "$set": { "active": True,  "topics_prefs": user.get("topics_prefs"), "locations_prefs":user.get("locations_prefs"),"subscription_date":user.get("subscription_date") } })
	
```


#### Topics menu

This method create a WhatsApp menu for the topics
``` py linenums="1"
	def create_topic_menu(self, user_topics):

		danos_ambientais	=	{ "id": "danos_ambientais"	,"title": "Danos ambientais"	,"description": "             "}	
		areas_protegidas	=	{ "id": "areas_protegidas"	,"title": "Áreas Protegidas"	,"description": "             "}
		povos				=	{ "id": "povos"				,"title": "Povos"				,"description": "             "}
		mudanca_climatica	=	{ "id": "mudanca_climatica"	,"title": "Mudança climática"	,"description": "             "}
		conservacao			=	{ "id": "conservacao"		,"title": "Conservação"			,"description": "             "}
		politica_economia	=	{ "id": "politica_economia"	,"title": "Política e economia"	,"description": "             "} 							
		all_topics			=	{ "id": "all_topics"		,"title": "Todos os temas"		,"description": "             "} 
		topic_options		=	[]

		if	len(user_topics)<5:
			topic_options.append(all_topics)

		if "danos_ambientais" not in user_topics:
			topic_options.append(danos_ambientais)

		if "areas_protegidas" not in user_topics:
			topic_options.append(areas_protegidas)

		if "povos" not in user_topics:
			topic_options.append(povos)

		if "mudanca_climatica" not in user_topics:
			topic_options.append(mudanca_climatica)

		if "conservacao" not in user_topics:
			topic_options.append(conservacao)			

		if "politica_economia" not in user_topics:
			topic_options.append(politica_economia)

				
			

		topics =	{
		
					"type": "list",
					"header": {
					  "type": "text",
					  "text": "Escolha os temas:"
					},
					"body": {
					  "text": "📝 Selecione uma das opções."
					},
					"footer": {
					  "text": "‎ "
					},
					"action": {
					  "button": "Clique aqui",
					  "sections": [
						{
						  "title": "personalize o conteúdo",
						  "rows": topic_options
						}
				 
					  ]
					}
				  }


		return topics
```

#### Topics options

This method show to user the topcis options

``` py linenums="1"
	def __choose_topics(self, user, response,msg_id):
		choose_topics	=	"👍Legal! Agora você poderá escolher quais temas te interessam 📝. Selecione o primeiro tema. Você poderá escolher outros em seguida."
		if not user['new']:
			if user.get("all_content"):
				self.send_message(user.get("user_id"), "text", "Você já estava cadastrado para receber todo nosso conteúdo 😃")
				return True		
		
		if len(user.get("topics_prefs"))<6:
			menu	=	self.create_topic_menu(user.get("topics_prefs"))
		else:
			self.send_message(user.get("user_id"), "text", "Você já se cadastrou em todos os temas 😃")
			return True
		
		if msg_id =="MAIN_TOPCIS":
			self.send_message(user.get("user_id"), "text", choose_topics)
			self.send_message(user.get("user_id"), "interactive", menu) 
			return True

		if  msg_id=="TOPIC_BTN_YES":
			if len(user.get("topics_prefs"))<6:
				self.send_message(user.get("user_id"), "text", "Escolha agora outro tema de conteúdos sobre a Amazônia 🌳")
				self.send_message(user.get("user_id"), "interactive", menu) 
			else:
				self.send_message(user.get("user_id"), "text", self.get_messages("ALL_CONTENT"))
			return True

		
		if msg_id =="all_topics":
			user["topics_prefs"]	=	["danos_ambientais","areas_protegidas","povos","mudanca_climatica","conservacao","politica_economia"]		
			self.__save_user_prefs(user)
			self.send_message(user.get("user_id"), "text", self.get_messages("ALL_CONTENT"))
				
		
		if msg_id in ["danos_ambientais","areas_protegidas","povos","mudanca_climatica","conservacao","politica_economia", "TOPIC_BTN_YES","TOPIC_BTN_NO"]:
			if	msg_id not	in ["TOPIC_BTN_YES","TOPIC_BTN_NO"]:
				user.get("topics_prefs").append(msg_id)	
				self.__save_user_prefs(user)
				if len(user.get("topics_prefs"))==6:
					self.send_message(user.get("user_id"), "text", self.get_messages("ALL_CONTENT"))

			
			if	msg_id!= "TOPIC_BTN_NO" and len(user.get("topics_prefs"))<6:	
				button	=	self.create_button("📝Deseja receber conteúdos de outros temas?", "Sim", "TOPIC_BTN_YES", "Não", "TOPIC_BTN_NO" )
				self.send_message(user.get("user_id"), "interactive", button)
				return True	
			if	msg_id== "TOPIC_BTN_NO":		
				self.send_message(user.get("user_id"), "text", self.get_messages("ALL_CONTENT"))			
				return True
	
```

#### Location menu

This method create a WhatsApp menu for the locations
``` py linenums="1"
def __create_location_menu(self, user_locations):

		acre			=	{ "id": "acre"			,"title": "Acre"					,	"description": "             "}	
		amapa			=	{ "id": "amapa"			,"title": "Amapá"					,	"description": "             "}
		amazonas		=	{ "id": "amazonas"		,"title": "Amazonas"				,	"description": "             "}
		maranhao		=	{ "id": "maranhao"		,"title": "Maranhão"				,	"description": "             "}
		mato_grosso		=	{ "id": "mato_grosso"	,"title": "Mato Grosso"				,	"description": "             "}
		para			=	{ "id": "para"			,"title": "Pará"					,	"description": "             "} 							
		rondonia		=	{ "id": "rondonia"		,"title": "Rondônia"				,	"description": "             "}
		roraima			=	{ "id": "roraima"		,"title": "Roraima"					,	"description": "             "}
		tocantins		=	{ "id": "tocantins"		,"title": "Tocantins"				,	"description": "             "}
		all_locations	=	{ "id": "all_locations"	,"title": "Amazônia Legal"			,	"description": "Engloba os estados brasileiros pertencentes à Bacia amazônica"} 

		location_options	=	[]

		if	len(user_locations)<8:
			location_options.append(all_locations)

		if "acre" not in user_locations:
			location_options.append(acre)

		if "amapa" not in user_locations:
			location_options.append(amapa)

		if "amazonas" not in user_locations:
			location_options.append(amazonas)

		if "maranhao" not in user_locations:
			location_options.append(maranhao)

		if "mato_grosso" not in user_locations:
			location_options.append(mato_grosso)			

		if "para" not in user_locations:
			location_options.append(para)

		if "rondonia" not in user_locations:
			location_options.append(rondonia)

		if "roraima" not in user_locations:
			location_options.append(roraima)

		if "tocantins" not in user_locations:
			location_options.append(tocantins)


		locations =	{
		
					"type": "list",
					"header": {
					  "type": "text",
					  "text": "Escolha os estados:"
					},
					"body": {
					  "text": "📝 Selecione uma das opções."
					},
					"footer": {
					  "text": "‎ "
					},
					"action": {
					  "button": "Clique aqui",
					  "sections": [
						{
						  "title": "personalize o conteúdo",
						  "rows":location_options
						}
				 
					  ]
					}
				  }


		return locations
```

#### Locations options

This method show to user the locations options

``` py linenums="1"
	def __choose_locations(self, user, response,msg_id):
		choose_locations	=	"👍Legal! Agora você poderá escolher de qual estado deseja receber conteúdos sobre a Amazônia 🌳. Selecione o primeiro estado 🇧🇷."
		if not user['new']:
			if user.get("all_content"):
				self.send_message(user.get("user_id"), "text", "Você já estava cadastrado para receber todo nosso conteúdo 😃")
				return True		
		
		if len(user.get("locations_prefs"))<9:
			menu	=	self.__create_location_menu(user.get("locations_prefs"))
		else:
			self.send_message(user.get("user_id"), "text", "Você já se cadastrou em todos os estados 😃")
			return True
	
		if msg_id =="MAIN_LOCATIONS":
			self.send_message(user.get("user_id"), "text", choose_locations)
			self.send_message(user.get("user_id"), "interactive", menu) 
			return True

		if  msg_id=="LOCATION_BTN_YES":
			if len(user.get("locations_prefs"))<9:
				self.send_message(user.get("user_id"), "text", "Vamos escolher outro estado para receber conteúdos sobre a Amazônia 🌳")
				self.send_message(user.get("user_id"), "interactive", menu) 
			else:
				self.send_message(user.get("user_id"), "text", self.get_messages("ALL_CONTENT"))
			return True

		
		if msg_id =="all_locations":
			user["locations_prefs"]	=	["Acre", "Amapá", "Amazonas", "Maranhão", "Mato Grosso", "Pará", "Rondônia", "Roraima", "Tocantins"]		
			self.__save_user_prefs(user)
			self.send_message(user.get("user_id"), "text", self.get_messages("ALL_CONTENT"))
				
		
		if msg_id in ["acre","amapa","amazonas","maranhao","mato_grosso","para","rondonia", "roraima","tocantins", "LOCATION_BTN_NO", "LOCATION_BTN_YES"]:
			if	msg_id not	in ["LOCATION_BTN_YES","LOCATION_BTN_NO"]:
				states_dict= {"acre":"Acre", "amapa":"Amapá", "amazonas":"Amazonas", "maranhao":"Maranhão", "mato_grosso":"Mato Grosso"}
				states_dict.update({"para":"Pará", "rondonia":"Rondônia", "roraima":"Roraima", "tocantins":"Tocantins"})
				user.get("locations_prefs").append(states_dict.get(msg_id))	
				self.__save_user_prefs(user)
				if len(user.get("locations_prefs"))==9:
					self.send_message(user.get("user_id"), "text", self.get_messages("ALL_CONTENT"))

			
			if	msg_id!= "LOCATION_BTN_NO" and len(user.get("locations_prefs"))<9:	
				button	=	self.create_button("🇧🇷 Quer receber conteúdos de outros estados?", "Sim", "LOCATION_BTN_YES", "Não", "LOCATION_BTN_NO" )
				self.send_message(user.get("user_id"), "interactive", button)
				return True	
			if	msg_id== "LOCATION_BTN_NO":		
				self.send_message(user.get("user_id"), "text", self.get_messages("ALL_CONTENT"))			
				return True
	
```

#### Manage the user's choices

This method manage of the users messages.

``` py linenums="1"
	def __choose_prefs(self,user,response):
		if	response["interactive"].get("type")== "list_reply":
			list_reply	=	response["interactive"].get("list_reply")	
			msg_id		=	list_reply.get("id")
		
		if	response["interactive"].get("type")== "button_reply":
			btn_reply	=	response["interactive"].get("button_reply")	
			msg_id		=	btn_reply.get("id")		

		if 	msg_id	=="MAIN_ALL_CONTENT":
			self.__choose_all(user, response)

		if 	msg_id	=="MAIN_ABOUT":
			self.send_message(user.get("user_id"), "text", self.get_messages("about"))

		if 	msg_id	in ["MAIN_TOPCIS", "danos_ambientais","areas_protegidas","povos","mudanca_climatica","conservacao","politica_economia","all_topics","TOPIC_BTN_NO", "TOPIC_BTN_YES"]:
			self.__choose_topics(user, response, msg_id)		

		if 	msg_id	in ["MAIN_LOCATIONS", "acre","amapa","amazonas","maranhao","mato_grosso","para","rondonia", "roraima","tocantins", "all_locations","LOCATION_BTN_NO", "LOCATION_BTN_YES"]:
			self.__choose_locations(user, response, msg_id)

```

#### Process subscriptions
This method is responsible for processing user messages. It retrieves the user ID and name from the response and queries the user preferences from the database. If the user preferences exist, it retrieves the existing user data; otherwise, it creates a new user with the provided ID and name. The method then checks the subscription status of the user. If the subscription is set to False, it performs an action to handle unsubscribed users. If the message type is "interactive" and the interactive type is either "list_reply" or "button_reply," it proceeds to choose the user preferences based on the response. In case of any exceptions, an error message is printed.

``` py linenums="1"
	def __process_subscription(self,response):
		try:
			user_id		=	response.get("user_id")
			user_name	=	response.get("name")
			user_query	=	self.__get_user_prefs(user_id)
			user		=	{}
			if user_query.get("success"):
				user			=	user_query.get("user")
				user['new']		=	False
			else:
				user			=	self.__create_user( user_id, user_name, True, False, [],  [])			
				user['new']		=	True
			
			if response["subscription"]==False:
				self.unsubscribed(user)		
				return True
			
			if response["message_type"]=="interactive":
				if	response["interactive"].get("type")=="list_reply" or response["interactive"].get("type")=="button_reply":
					self.__choose_prefs(user,response)

		except Exception as e:
			print("/////////////////////////////////////////////////////////////////////////////////////")
			print (e)
			print("/////////////////////////////////////////////////////////////////////////////////////")
```

#### Process statuses
This method is responsible for processing the statuses of user messages, specifically whether they have been sent, delivered, or read, and saving the status information in the database. It iterates through the provided data and retrieves the message ID (wamid) for each status. It then queries the database to find the corresponding message based on the wamid. If the message is found, it retrieves the status information from the data and the recipient ID. The method updates the message document in the database based on the status. For example, if the status is "sent," it sets the 'sent' field to True and records the send date. Similarly, for "delivered," "read," and "failed" statuses, corresponding fields are updated with the respective values and dates. If any exceptions occur, an error message is printed.
``` py linenums="1"
	def __process_subscription(self,response):
		try:
			user_id		=	response.get("user_id")
			user_name	=	response.get("name")
			user_query	=	self.__get_user_prefs(user_id)
			user		=	{}
			if user_query.get("success"):
				user			=	user_query.get("user")
				user['new']		=	False
			else:
				user			=	self.__create_user( user_id, user_name, True, False, [],  [])			
				user['new']		=	True
			
			if response["subscription"]==False:
				self.unsubscribed(user)		
				return True
			
			if response["message_type"]=="interactive":
				if	response["interactive"].get("type")=="list_reply" or response["interactive"].get("type")=="button_reply":
					self.__choose_prefs(user,response)

		except Exception as e:
			print("/////////////////////////////////////////////////////////////////////////////////////")
			print (e)
			print("/////////////////////////////////////////////////////////////////////////////////////")
```

#### Process webhook notification
This method is responsible for processing a webhook notification. It receives data as input and performs various operations based on the contents of the data. It iterates through the data entries and their changes. If the value contains "statuses," it calls the process_statuses method. Otherwise, it extracts information such as the name, user ID, message type, and subscription status from the data. If the message type is "text," it checks if the client's message is "cancelar" and updates the subscription status accordingly. For interactive messages, it extracts the interactive content. After processing the data, it calls other methods based on the content and message type, such as process_diff_contents and main_menu.
``` py linenums="1"
		"""_summary_: Process webhook notification
		For the moment, this will return the type of notification
		"""
		response={}
		valid_responses=['cancelar']
		try:
			print(data)
			for entry in data["entry"]:

				for change in entry["changes"]:
					
					value						=	change.get("value")
					if "statuses" in value:
						return self.process_statuses(data,value)
					response["name"]			=	value["contacts"][0]["profile"]["name"]
					response["user_id"]			=	value["messages"][0]["from"]			
					response["message_type"]	=	value["messages"][0]["type"]
					response["subscription"]	=	True
					
					if response["message_type"]=="text":
						response["client_message"]	=	value["messages"][0]["text"]["body"].lower()	
						if	response["client_message"]=="cancelar":
							response["subscription"]	=	False
							self.__process_subscription(response)

					if response["message_type"]=="interactive":
						response["interactive"]	=	value["messages"][0]["interactive"]
						self.__process_subscription(response)

			if	self.process_diff_contents(response) or (response.get("message_type")=="text" and not response.get("client_message") in valid_responses):
				self.main_menu(response)

```
