#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pprint
import pytz
import requests

from datetime import datetime

from classes import  dataBase

pp = pprint.PrettyPrinter(indent=4)

class News:

	def __init__( self):
		try:
			response	=	requests.get("https://infoamazonia.org/wp-json/wp/v2/posts")
			response	=	requests.get("https://plenamata.eco/wp-json/wp/v2/posts")
			self.db		=	dataBase.DataBase("db/db.json")
		except requests.exceptions.ConnectionError:
			print("Error connecting to Wordpress API")
			return {"success":False}
			

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
	



	def __set_source(self,news):
		if "//infoamazonia.org/" in news["URL"]:
			news["news_source"]	="infoamazonia.org"
		elif "//plenamata.eco/" in news["URL"]:
			news["news_source"]	="plenamata.eco"
		else:
			news["news_source"]	=""
			news["success"]	=	False




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

	
