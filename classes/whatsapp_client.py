#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-**-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-* 

											"wb.py"
											*********
								
								********************************

		Developed by: Wilson  Ceron		e-mail: wilsonseron@gmail.com 		Date: 05/12/2022
								

-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-**-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-* 
"""

import os
import requests
import json
import pytz

from classes import dataBase
from datetime import datetime, timedelta


class WhatsAppWrapper:

    API_URL = "https://graph.facebook.com/v13.0/"
    API_TOKEN = ""
    NUMBER_ID = ""

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {self.API_TOKEN}",
            "Content-Type": "application/json",
        }
        self.API_URL = self.API_URL + self.NUMBER_ID
        self.db = dataBase.DataBase("db/db.json")

    def get_messages(self, message):

        welcome = "Olá, seja bem-vindo! Sou o robô de notícias da InfoAmazonia 🍃\nEnviamos os conteúdos recém publicados sobre o que mais te interessam sobre a Amazônia. O serviço é *GRATUITO*.\n\n📌 Para voltar a ver essas opções, digite *MENU* a qualquer momento\n📌 Se deseja cancelar sua inscrição, envie *CANCELAR* a qualquer momento e não te enviaremos mais notícias."

        image = "Desculpe não estamos aceitando imagens no momento 😥\nPor favor escolha uma das opções 😃"
        document = "Desculpe não estamos aceitando documentos no momento 😥\nPor favor escolha uma das opções 😃"
        location = "Desculpe não estamos aceitando localizações no momento 😥\nPor favor escolha uma das opções 😃"
        contacts = "Desculpe não envie contatos 😥\n Por favor peça para que seus amigos nos envie diretamente uma mensagem 😃"

        video = "Esse vídeo deve ser super legal, porém não estamos aceitando vídeo no momento 😥\nPor favor escolha uma das opções 😃"
        audio = "Adoraria ouvir esse áudio, porém não estamos aceitando no momento 😥\nPor favor escolha uma das opções 😃"
        sticker = "Seu sticker é muito bonitinho pórem não estamos aceitando no momento 😥\nPor favor escolha uma das opções 😃"
        cancel_1 = "Sua inscrição foi cancelada, não te enviaremos mais notícias 😥. Se você deseja voltar a assinar, só enviar MENU"
        cancel_0 = "Sua inscrição já tinha sido cancelada, já faz tempo que não te enviamos novas notícias 😥"
        all_content = "Obrigado pela sua inscrição! 🙌 Em breve você começará a receber nosso conteúdo no seu WhatsApp 📲. Se quiser ver as opções novamente, só digitar MENU."

        about = "InfoAmazonia é um veículo independente que utiliza dados, mapas e reportagens geolocalizadas para contar histórias sobre a maior floresta tropical contínua do planeta. "
        about = (
            about
            + "As bases de dados usadas pelo InfoAmazonia são renovadas com frequência e estarão sempre disponíveis para download. "
        )
        about = (
            about
            + "O cruzamento das notícias com os dados pretende melhorar a percepção sobre os desafios para a conservação da floresta."
        )

        main_menu = {
            "type": "list",
            "header": {
                "type": "text",
                "text": "Enviamos os conteúdos personalizados sobre a Amazônia",
            },
            "body": {"text": "Como deseja receber nosso conteúdo?"},
            "footer": {"text": "Escolha uma das opções"},
            "action": {
                "button": "Clique aqui!!!",
                "sections": [
                    {
                        "title": "personalize o conteúdo",
                        "rows": [
                            {
                                "id": "MAIN_ALL_CONTENT",
                                "title": "Tudo",
                                "description": "Todos conteúdos sobre a floresta amazônica 🌳",
                            },
                            {
                                "id": "MAIN_LOCATIONS",
                                "title": "Estados",
                                "description": "Receber apenas conteúdos de determinados estados 🇧🇷",
                            },
                            {
                                "id": "MAIN_TOPCIS",
                                "title": "Temas",
                                "description": "Receber apenas conteúdos de determinados temas ✅",
                            },
                            {
                                "id": "MAIN_ABOUT",
                                "title": "Sobre",
                                "description": "Saber mais sobre a InfoAmazonia 🍃",
                            },
                        ],
                    }
                ],
            },
        }

        if message == "main_menu":
            return main_menu

        if message == "welcome":
            return welcome

        if message == "image":
            return image

        if message == "document":
            return document

        if message == "location":
            return location

        if message == "contacts":
            return contacts

        if message == "video":
            return video

        if message == "audio":
            return audio

        if message == "sticker":
            return sticker

        if message == "cancel_0":
            return cancel_0

        if message == "cancel_1":
            return cancel_1

        if message == "ALL_CONTENT":
            return all_content

        if message == "about":
            return about

    def send_message(self, recipient_phone_number, message_type, message):
        print("to aki")
        payload = {"messaging_product": "whatsapp", "to": recipient_phone_number}

        payload["type"] = message_type

        if message_type == "text":
            payload["text"] = {"body": message}

        if message_type == "interactive":
            payload["interactive"] = message

        print(payload)
        print(f"{self.API_URL}/messages", self.headers, payload)

        response = requests.request(
            "POST",
            f"{self.API_URL}/messages",
            headers=self.headers,
            data=json.dumps(payload),
        )

        # print(response.headers)
        # assert response.status_code == 200, "Error sending message"

        return response.status_code

    def process_diff_contents(self, response):
        if response.get("message_type") == "image":
            self.send_message(
                response.get("user_id"), "text", self.get_messages("image")
            )
            return True
        if response.get("message_type") == "document":
            self.send_message(
                response.get("user_id"), "text", self.get_messages("document")
            )
            return True
        if response.get("message_type") == "contacts":
            self.send_message(
                response.get("user_id"), "text", self.get_messages("contacts")
            )
            return True
        if response.get("message_type") == "location":
            self.send_message(
                response.get("user_id"), "text", self.get_messages("location")
            )
            return True
        if response.get("message_type") == "video":
            self.send_message(
                response.get("user_id"), "text", self.get_messages("video")
            )
            return True
        if response.get("message_type") == "audio":
            self.send_message(
                response.get("user_id"), "text", self.get_messages("audio")
            )
            return True
        if response.get("message_type") == "sticker":
            self.send_message(
                response.get("user_id"), "text", self.get_messages("sticker")
            )
            return True

        return False

    def main_menu(self, response):
        self.send_message(response.get("user_id"), "text", self.get_messages("welcome"))
        self.send_message(
            response.get("user_id"), "interactive", self.get_messages("main_menu")
        )

    def __get_user_prefs(self, user_id):
        r = self.db.find("users", {"user_id": {"$eq": user_id}}, {"_id": 0})
        if r.get("success"):
            user = r.get("docs")[0]
            if user.get("topics_prefs") == None:
                user["topics_prefs"] = []

            if user.get("locations_prefs") == None:
                user["locations_prefs"] = []

            if user.get("unsubscribed_date") == None:
                user["unsubscribed_date"] = []

            if user.get("subscription_date") == None:
                user["subscription_date"] = []
            u = {
                "user_id": user.get("user_id"),
                "name": user.get("name"),
                "active": user.get("active"),
                "all_content": user.get("all_content"),
                "topics_prefs": user.get("topics_prefs"),
                "locations_prefs": user.get("locations_prefs"),
                "subscription_date": user.get("subscription_date"),
                "unsubscribed_date": user.get("unsubscribed_date"),
            }
            return {"success": True, "user": u}

        return {"success": False}

    def unsubscribed(self, user):
        if user.get("new"):
            self.send_message(
                user.get("user_id"),
                "text",
                "Você nunca se cadastrou aqui 😥, que tal fazer isso hoje?",
            )
            return True

        if user.get("active") == False:
            self.send_message(
                user.get("user_id"), "text", self.get_messages("cancel_0")
            )
            return True

        if user.get("active") == True:
            unsub_date = datetime.now(pytz.timezone("America/Sao_Paulo"))
            if len(user.get("unsubscribed_date")) == 0:
                user["unsubscribed_date"] = [unsub_date]
            else:
                user.get("unsubscribed_date").append(unsub_date)

            self.db.update_one(
                "users",
                {"user_id": {"$eq": user.get("user_id")}},
                {
                    "$set": {
                        "active": False,
                        "all_content": False,
                        "unsubscribed_date": user.get("unsubscribed_date"),
                        "locations_prefs": [],
                        "topics_prefs": [],
                    }
                },
            )
            self.send_message(
                user.get("user_id"), "text", self.get_messages("cancel_1")
            )

    def __create_user(
        self, user_id, name, active, all_content, topics_prefs, locations_prefs
    ):

        doc = {
            "user_id": user_id,
            "_id": user_id,
            "name": name,
            "active": active,
            "all_content": all_content,
            "topics_prefs": topics_prefs,
            "locations_prefs": locations_prefs,
            "subscription_date": [datetime.now(pytz.timezone("America/Sao_Paulo"))],
            "unsubscribed_date": [],
            "verified": True,
        }
        return doc

    def __choose_all(self, user, response):

        if user["new"]:
            user.pop("new")
            user["all_content"] = True
            self.db.insert_many("users", [user])
            self.send_message(
                user.get("user_id"), "text", self.get_messages("ALL_CONTENT")
            )
            return True

        if user.get("all_content"):
            self.send_message(
                user.get("user_id"),
                "text",
                "Você já estava cadastrado para receber todo nosso conteúdo 😃",
            )
        else:
            self.db.update_one(
                "users",
                {"user_id": {"$eq": user.get("user_id")}},
                {
                    "$set": {
                        "active": True,
                        "all_content": True,
                        "topics_prefs": [],
                        "locations_prefs": [],
                    }
                },
            )
            self.send_message(
                user.get("user_id"), "text", self.get_messages("ALL_CONTENT")
            )

    def create_button(
        self, button_message, response_1, response_1_id, response_2, response_2_id
    ):
        button = {
            "type": "button",
            "header": {"type": "text", "text": button_message},
            "body": {"text": "  ‎   "},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": response_1_id, "title": response_1},
                    },
                    {
                        "type": "reply",
                        "reply": {"id": response_2_id, "title": response_2},
                    },
                ]
            },
        }

        return button

    def __save_user_prefs(self, user):
        if user["new"]:
            user.pop("new")
            self.db.insert_many("users", [user])
        else:
            if user.get("active"):
                self.db.update_one(
                    "users",
                    {"user_id": {"$eq": user.get("user_id")}},
                    {
                        "$set": {
                            "topics_prefs": user.get("topics_prefs"),
                            "locations_prefs": user.get("locations_prefs"),
                        }
                    },
                )
            else:
                sub_date = datetime.now(pytz.timezone("America/Sao_Paulo"))
                user.get("subscription_date").append(sub_date)
                self.db.update_one(
                    "users",
                    {"user_id": {"$eq": user.get("user_id")}},
                    {
                        "$set": {
                            "active": True,
                            "topics_prefs": user.get("topics_prefs"),
                            "locations_prefs": user.get("locations_prefs"),
                            "subscription_date": user.get("subscription_date"),
                        }
                    },
                )

    def create_topic_menu(self, user_topics):

        danos_ambientais = {
            "id": "danos_ambientais",
            "title": "Danos ambientais",
            "description": "             ",
        }
        areas_protegidas = {
            "id": "areas_protegidas",
            "title": "Áreas Protegidas",
            "description": "             ",
        }
        povos = {"id": "povos", "title": "Povos", "description": "             "}
        mudanca_climatica = {
            "id": "mudanca_climatica",
            "title": "Mudança climática",
            "description": "             ",
        }
        conservacao = {
            "id": "conservacao",
            "title": "Conservação",
            "description": "             ",
        }
        politica_economia = {
            "id": "politica_economia",
            "title": "Política e economia",
            "description": "             ",
        }
        all_topics = {
            "id": "all_topics",
            "title": "Todos os temas",
            "description": "             ",
        }
        topic_options = []

        if len(user_topics) < 5:
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

        topics = {
            "type": "list",
            "header": {
                "type": "text",
                "text": "👍Legal! Agora você poderá escolher quais temas te interessam ",
            },
            "body": {"text": "📝 Escolha uma das opções"},
            "footer": {"text": "‎ "},
            "action": {
                "button": "Clique aqui",
                "sections": [
                    {"title": "personalize o conteúdo", "rows": topic_options}
                ],
            },
        }

        return topics

    def __choose_topics(self, user, response, msg_id):
        choose_topics = "👍Legal! Agora você poderá escolher quais temas te interessam 📝. Selecione o primeiro tema?"
        if not user["new"]:
            if user.get("all_content"):
                self.send_message(
                    user.get("user_id"),
                    "text",
                    "Você já estava cadastrado para receber todo nosso conteúdo 😃",
                )
                return True

        if len(user.get("topics_prefs")) < 6:
            menu = self.create_topic_menu(user.get("topics_prefs"))
        else:
            self.send_message(
                user.get("user_id"), "text", "Você já se cadastrou em todos os temas 😃"
            )
            return True

        if msg_id == "MAIN_TOPCIS":
            self.send_message(user.get("user_id"), "text", choose_topics)
            self.send_message(user.get("user_id"), "interactive", menu)
            return True

        if msg_id == "TOPIC_BTN_YES":
            if len(user.get("topics_prefs")) < 6:
                self.send_message(
                    user.get("user_id"),
                    "text",
                    "Vamos escolher outro tema para receber conteúdos sobre a Amazônia 🌳.",
                )
                self.send_message(user.get("user_id"), "interactive", menu)
            else:
                self.send_message(
                    user.get("user_id"), "text", self.get_messages("ALL_CONTENT")
                )
            return True

        if msg_id == "all_topics":
            user["topics_prefs"] = [
                "danos_ambientais",
                "areas_protegidas",
                "povos",
                "mudanca_climatica",
                "conservacao",
                "politica_economia",
            ]
            self.__save_user_prefs(user)
            self.send_message(
                user.get("user_id"), "text", self.get_messages("ALL_CONTENT")
            )

        if msg_id in [
            "danos_ambientais",
            "areas_protegidas",
            "povos",
            "mudanca_climatica",
            "conservacao",
            "politica_economia",
            "TOPIC_BTN_YES",
            "TOPIC_BTN_NO",
        ]:
            if msg_id not in ["TOPIC_BTN_YES", "TOPIC_BTN_NO"]:
                user.get("topics_prefs").append(msg_id)
                self.__save_user_prefs(user)
                if len(user.get("topics_prefs")) == 6:
                    self.send_message(
                        user.get("user_id"), "text", self.get_messages("ALL_CONTENT")
                    )

            if msg_id != "TOPIC_BTN_NO" and len(user.get("topics_prefs")) < 6:
                button = self.create_button(
                    "📝Deseja receber conteúdos de outros temas?",
                    "Sim",
                    "TOPIC_BTN_YES",
                    "Não",
                    "TOPIC_BTN_NO",
                )
                self.send_message(user.get("user_id"), "interactive", button)
                return True
            if msg_id == "TOPIC_BTN_NO":
                self.send_message(
                    user.get("user_id"), "text", self.get_messages("ALL_CONTENT")
                )
                return True

    def __create_location_menu(self, user_locations):

        acre = {"id": "acre", "title": "Acre", "description": "             "}
        amapa = {"id": "amapa", "title": "Amapá", "description": "             "}
        amazonas = {
            "id": "amazonas",
            "title": "Amazonas",
            "description": "             ",
        }
        maranhao = {
            "id": "maranhao",
            "title": "Maranhão",
            "description": "             ",
        }
        mato_grosso = {
            "id": "mato_grosso",
            "title": "Mato Grosso",
            "description": "             ",
        }
        para = {"id": "para", "title": "Pará", "description": "             "}
        rondonia = {
            "id": "rondonia",
            "title": "Rondônia",
            "description": "             ",
        }
        roraima = {"id": "roraima", "title": "Roraima", "description": "             "}
        tocantins = {
            "id": "tocantins",
            "title": "Tocantins",
            "description": "             ",
        }
        all_locations = {
            "id": "all_locations",
            "title": "Amazônia Legal",
            "description": "Engloba os estados brasileiros pertencentes à Bacia amazônica",
        }

        location_options = []

        if len(user_locations) < 8:
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

        locations = {
            "type": "list",
            "header": {
                "type": "text",
                "text": "Selecione qual estado você deseja receber conteúdos 🌳",
            },
            "body": {"text": "📝 Escolha uma das opções"},
            "footer": {"text": "‎ "},
            "action": {
                "button": "Clique aqui",
                "sections": [
                    {"title": "personalize o conteúdo", "rows": location_options}
                ],
            },
        }

        return locations

    def __choose_locations(self, user, response, msg_id):
        choose_locations = "👍Legal! Agora você poderá escolher qual estado deseja receber conteúdos sobre a Amazônia 🌳. Selecione o primeiro estado 🇧🇷? "
        if not user["new"]:
            if user.get("all_content"):
                self.send_message(
                    user.get("user_id"),
                    "text",
                    "Você já estava cadastrado para receber todo nosso conteúdo 😃",
                )
                return True

        if len(user.get("locations_prefs")) < 9:
            menu = self.__create_location_menu(user.get("locations_prefs"))
        else:
            self.send_message(
                user.get("user_id"),
                "text",
                "Você já se cadastrou em todos os estados 😃",
            )
            return True

        if msg_id == "MAIN_LOCATIONS":
            self.send_message(user.get("user_id"), "text", choose_locations)
            self.send_message(user.get("user_id"), "interactive", menu)
            return True

        if msg_id == "LOCATION_BTN_YES":
            if len(user.get("locations_prefs")) < 9:
                self.send_message(
                    user.get("user_id"),
                    "text",
                    "Vamos escolher outro estado para receber conteúdos sobre a Amazônia 🌳",
                )
                self.send_message(user.get("user_id"), "interactive", menu)
            else:
                self.send_message(
                    user.get("user_id"), "text", self.get_messages("ALL_CONTENT")
                )
            return True

        if msg_id == "all_locations":
            user["locations_prefs"] = [
                "acre",
                "amapa",
                "amazonas",
                "maranhao",
                "mato_grosso",
                "para",
                "rondonia",
                "roraima",
                "tocantins",
            ]
            self.__save_user_prefs(user)
            self.send_message(
                user.get("user_id"), "text", self.get_messages("ALL_CONTENT")
            )

        if msg_id in [
            "acre",
            "amapa",
            "amazonas",
            "maranhao",
            "mato_grosso",
            "para",
            "rondonia",
            "roraima",
            "tocantins",
            "LOCATION_BTN_NO",
            "LOCATION_BTN_YES",
        ]:
            if msg_id not in ["LOCATION_BTN_YES", "LOCATION_BTN_NO"]:
                user.get("locations_prefs").append(msg_id)
                self.__save_user_prefs(user)
                if len(user.get("locations_prefs")) == 9:
                    self.send_message(
                        user.get("user_id"), "text", self.get_messages("ALL_CONTENT")
                    )

            if msg_id != "LOCATION_BTN_NO" and len(user.get("locations_prefs")) < 9:
                button = self.create_button(
                    "🇧🇷Deseja receber conteúdos de outros estados",
                    "Sim",
                    "LOCATION_BTN_YES",
                    "Não",
                    "LOCATION_BTN_NO",
                )
                self.send_message(user.get("user_id"), "interactive", button)
                return True
            if msg_id == "LOCATION_BTN_NO":
                self.send_message(
                    user.get("user_id"), "text", self.get_messages("ALL_CONTENT")
                )
                return True

    def __choose_prefs(self, user, response):
        if response["interactive"].get("type") == "list_reply":
            list_reply = response["interactive"].get("list_reply")
            msg_id = list_reply.get("id")

        if response["interactive"].get("type") == "button_reply":
            btn_reply = response["interactive"].get("button_reply")
            msg_id = btn_reply.get("id")

        if msg_id == "MAIN_ALL_CONTENT":
            self.__choose_all(user, response)

        if msg_id == "MAIN_ABOUT":
            self.send_message(user.get("user_id"), "text", self.get_messages("about"))

        if msg_id in [
            "MAIN_TOPCIS",
            "danos_ambientais",
            "areas_protegidas",
            "povos",
            "mudanca_climatica",
            "conservacao",
            "politica_economia",
            "all_topics",
            "TOPIC_BTN_NO",
            "TOPIC_BTN_YES",
        ]:
            self.__choose_topics(user, response, msg_id)

        if msg_id in [
            "MAIN_LOCATIONS",
            "acre",
            "amapa",
            "amazonas",
            "maranhao",
            "mato_grosso",
            "para",
            "rondonia",
            "roraima",
            "tocantins",
            "all_locations",
            "LOCATION_BTN_NO",
            "LOCATION_BTN_YES",
        ]:
            self.__choose_locations(user, response, msg_id)

    def __process_subscription(self, response):
        try:
            user_id = response.get("user_id")
            user_name = response.get("name")
            user_query = self.__get_user_prefs(user_id)
            user = {}
            if user_query.get("success"):
                user = user_query.get("user")
                user["new"] = False
            else:
                user = self.__create_user(user_id, user_name, True, False, [], [])
                user["new"] = True

            if response["subscription"] == False:
                self.unsubscribed(user)
                return True

            if response["message_type"] == "interactive":
                if (
                    response["interactive"].get("type") == "list_reply"
                    or response["interactive"].get("type") == "button_reply"
                ):
                    self.__choose_prefs(user, response)

        except Exception as e:
            print(
                "/////////////////////////////////////////////////////////////////////////////////////"
            )
            print(e)
            print(
                "/////////////////////////////////////////////////////////////////////////////////////"
            )

    def process_webhook_notification(self, data):
        """_summary_: Process webhook notification
        For the moment, this will return the type of notification
        """
        response = {}
        valid_responses = ["cancelar"]
        try:

            for entry in data["entry"]:

                for change in entry["changes"]:

                    response["name"] = change["value"]["contacts"][0]["profile"]["name"]
                    response["user_id"] = change["value"]["messages"][0]["from"]
                    response["message_type"] = change["value"]["messages"][0]["type"]
                    response["subscription"] = True

                    if response["message_type"] == "text":
                        response["client_message"] = change["value"]["messages"][0][
                            "text"
                        ]["body"].lower()
                        if response["client_message"] == "cancelar":
                            response["subscription"] = False
                            self.__process_subscription(response)

                    if response["message_type"] == "interactive":
                        response["interactive"] = change["value"]["messages"][0][
                            "interactive"
                        ]
                        self.__process_subscription(response)

            if self.process_diff_contents(response) or (
                response.get("message_type") == "text"
                and not response.get("client_message") in valid_responses
            ):
                self.main_menu(response)

        except Exception as e:
            print("\n\n**EXCEPTION**\n")
            print(e)
            print("\n\n")

