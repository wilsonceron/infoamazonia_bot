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


### News
### whatsapp_client




