# Download the helper library from https://www.twilio.com/docs/python/install
from contextlib import redirect_stderr

from flask_login import login_required
from app import app
import os
from twilio.rest import Client
from datetime import datetime
from flask import render_template, flash, redirect, url_for
from app.classes.data import Message
from app.classes.forms import MessageForm, SendMessageForm
from app.utils.secrets import getSecrets

secrets = getSecrets()


# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure

account_sid = secrets['TWILIO_SID']
auth_token = secrets['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

@app.route('/msgs/get')
@login_required
def msgsGet():
    firstMsg = Message.objects().first()
    year = datetime.date(firstMsg.date_sent).year
    month = datetime.date(firstMsg.date_sent).month
    day = datetime.date(firstMsg.date_sent).day
    messages = client.messages.list(
                                date_sent_after = datetime(int(year), int(month), int(day), 0, 0, 0),
                                limit=20
                            )

    for msg in messages:
        try:
            newMsg = Message(
                date_sent = msg.date_sent,
                to = msg.to,
                from_ = msg.from_,
                body=msg.body,
                sid=msg.sid
            )
            newMsg.save()
        except Exception as error:
            flash(f'Msg with sid #{msg.sid} has error {error}.')

    return redirect(url_for('msgsList'))

@app.route("/msg/edit/<msgId>", methods=["GET","POST"])
def msgEdit(msgId):
    editMsg = Message.objects.get(id=msgId)
    form = MessageForm()
    if form.validate_on_submit():
        editMsg.update(
            status = form.status.data
        )
        return redirect(url_for('msgsList'))
    return render_template("msgForm.html",form=form, msg=editMsg)

@app.route('/msgs/list',methods=["GET","POST"])
def msgsList():
    
    form = MessageForm()
    if form.validate_on_submit():
        if form.status.data == "":
            msgs = Message.objects()
        else:      
            msgs = Message.objects(status=form.status.data)
    else:
        msgs = Message.objects()

    return render_template('msgs.html',msgs=msgs,form=form)

# message = client.messages \
#     .create(
#          body='Wassup',
#          from_='+19896234883',
#          to='+15107763096'
#     )

# print(message.sid)

# call = client.calls.create(
#                         twiml='<Response><Say>Ahoy, World!</Say></Response>',
#                         from_='+19896234883',
#                         to='+15107763096'
#                     )

# print(call.sid)

@app.route('/sendMsg',methods=["GET","POST"])
def sendMsg():
    form = SendMessageForm()
    if form.validate_on_submit():
        message = client.messages.create(
            body=form.body.data,
            from_='+19896234883',
            to=form.to.data
        )
        flash("Message Sent!")
        return redirect(url_for('msgsList'))

    return render_template ('sendMsgform.html',form=form)
    
