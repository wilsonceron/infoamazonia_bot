import csv
import datetime
import json
import sys, os
import time


from apscheduler.schedulers.background import BackgroundScheduler
from bson import ObjectId
from collections import Counter
from collections import defaultdict

from classes import dataBase
from classes import news
from classes.app import app
from classes.whatsapp_client import WhatsAppWrapper

from datetime import datetime, timedelta

# pip3 install apscheduler


class Manager:
    def __init__(self):

        self.db = dataBase.DataBase("db/db.json")
        self.news = news.News()
        self.app = app
        self.client = WhatsAppWrapper()

    def update_and_notify(self):
        """Get lastest news from Wordpress API"""
        print("Database update running...")

        db_news = self.__get_db_last_news()
        latest_news = self.news.get_news(db_news)
        if latest_news.get("success"):
            print("Number of new news:" + str(latest_news.get("number_of_news")))
            self.db.insert_many("news", latest_news.get("news"))
            self.__notify_users(latest_news.get("news"))
        else:
            print("The database was already updated")

    def __get_db_last_news(self):
        if self.db.checkConnection():
            sources = [
                "infoamazonia_pt",
                "infoamazonia_en",
                "infoamazonia_es",
                "plenamata_pt",
                "plenamata_en",
                "plenamata_es",
            ]
            last = {}
            for source in sources:
                # print(source)
                r = self.db.get_last_n_doc(
                    "news",
                    {"api_source": {"$eq": source}},
                    {"URL": 1, "_id": 0},
                    [("Published_date", -1)],
                    5,
                )

                if r.get("success"):
                    urls = []
                    docs = r.get("docs")
                    for news in docs:
                        urls.append(news["URL"])
                        # print(news["URL"])
                    if urls:
                        last[source] = urls
            if last:
                return {"success": True, "last_news": last}

        return {"success": False}

    def confirm_subscription(self):
        print("Running confirm subscription task ...")
        # button	=	self.client.create_button("Olá, nosso robô 🤖 não gostar de ser spam 🚮. Você quer continuar recebendo nosso conteúdos?", "Sim", "SUBSCRIPTION_BTN_YES", "Não", "SUBSCRIPTION_BTN_NO" )
        button = self.client.create_button(
            "🤖 Olá, Você quer continuar recebendo nosso conteúdos?",
            "Sim",
            "SUBSCRIPTION_BTN_YES",
            "Não",
            "SUBSCRIPTION_BTN_NO",
        )
        last_30_day = datetime.now() - timedelta(days=30)
        r = self.db.find(
            "users",
            {
                "$expr": {"$lte": [{"$last": "$subscription_date"}, last_30_day]},
                "active": {"$eq": True},
            },
            {"_id": 0},
        )
        if r.get("success"):
            users = r.get("docs")
            for user in users:
                self.db.update_one(
                    "users",
                    {"user_id": {"$eq": user.get("user_id")}},
                    {"$set": {"verified": False}},
                )
                self.client.send_message(user.get("user_id"), "interactive", button)
                print("user", user)

    def __pre_process(self, user, last_news):
        user_topics_prefs = set(user.get("topics_prefs"))
        user_locations_prefs = set(user.get("locations_prefs"))
        user_all_content = user.get("all_content")
        user["news"] = []
        news_locations = set()
        urls = []
        titles = []
        for news in last_news:
            try:
                news_topics = set(news.get("News_topics"))
            except:
                news_topics = set()

            if (
                news["URL"] not in urls
                and news["Language"] == "pt-BR"
                and news["Title"] not in titles
            ):
                urls.append(news["URL"])
                titles.append(news["Title"])
                if news.get("location").get("location"):
                    try:
                        news_locations = set([news.get("location").get("state")])
                    except:
                        news_locations = set()

                if user_all_content:
                    user["news"].append(
                        {
                            "Title": news.get("Title"),
                            "Description": news.get("Description"),
                            "URL": news.get("URL"),
                        }
                    )
                else:
                    if user_topics_prefs.intersection(news_topics):
                        user["news"].append(
                            {
                                "Title": news.get("Title"),
                                "Description": news.get("Description"),
                                "URL": news.get("URL"),
                            }
                        )
                    elif user_locations_prefs.intersection(news_locations):
                        user["news"].append(
                            {
                                "Title": news.get("Title"),
                                "Description": news.get("Description"),
                                "URL": news.get("URL"),
                            }
                        )

        return user

    def __create_messages(self, users_db, news):
        users = []
        for user in users_db:
            users.append(self.__pre_process(user, news))

        return users

    def __notify_users(self, news):
        r = self.db.find("users", {"active": {"$eq": True}}, {"_id": 0})
        if r.get("success"):
            users = r.get("docs")
            messages = self.__create_messages(users, news)
            for message in messages:
                user_id = message.get("user_id")
                msg = ""
                for n in message.get("news"):
                    title = n.get("Title")
                    description = n.get("Description")
                    url = n.get("URL")
                    msg = (
                        "💭 Exclusivo: "
                        + title
                        + "\n\n"
                        + description
                        + " ➡️Leia aqui: "
                        + url
                        + "\n\n"
                    )
                    msg = (
                        msg
                        + "Recebeu esta mensagem de um amigo? Acesse o link para assinar esse boletim no WhatsApp: http://bit.ly/zap_MZ"
                    )
                    self.client.send_message(user_id, "text", msg)

    def start_scheduler(self):
        scheduler = BackgroundScheduler(daemon=True, timezone="America/Sao_Paulo")

        # Each X minutes or hours
        scheduler.add_job(
            self.update_and_notify, trigger="interval", minutes=5
        )  # change to minutes

        # default time
        # scheduler.add_job(self.update_and_notify, trigger='cron', hour='9', minute='00')

        # confirm_subscription
        scheduler.add_job(
            self.confirm_subscription, trigger="cron", day=28, hour="1", minute="20"
        )

        # update_subscription
        # scheduler.add_job(self.update_subscription, trigger='cron', hour='9', minute='00')

        scheduler.start()

    def start(self):
        self.start_scheduler()
        self.update_and_notify()
        self.app.run(
            debug=True, host="0.0.0.0", port=5000
        )  # ,ssl_context=('cert.pem', 'key.pem'))

