#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-**-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-* 

										"whatsApp-Bot.py"
										*****************
								-	API's		: WordPress API and WhatsApp API
								-	Database:	: Mongodb
								-	Main		: Flask 	
								*************************************************

		Developed by: Wilson  Ceron		e-mail: wilsonseron@gmail.com 		Date: 15/12/2022
								

-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-**-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-* 
'''

import os



from classes import  manager


if __name__ == "__main__":

	manager	=	manager.Manager()
	manager.start()
	
