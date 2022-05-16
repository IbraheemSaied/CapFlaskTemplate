from contextlib import redirect_stderr
from app import app
import os
from twilio.rest import Client
from datetime import datetime
from flask import render_template, flash, redirect, url_for
from app.classes.data import Message
from app.utils.secrets import getSecrets

secrets = getSecrets()

account_sid = secrets['TWILIO_SID']
auth_token = secrets['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

message = client.messages \
     .create(
          body='I dont know',
          from_='+19896234883',
          to='+15107763096'
     )

print(message.sid)
