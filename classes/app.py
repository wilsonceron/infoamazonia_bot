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
# https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https

# pip3 install pyopenssl
# pip3 install twilio flask requests

import os

from flask import Flask, jsonify, request
from classes.whatsapp_client import WhatsAppWrapper

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello World!", 200


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

