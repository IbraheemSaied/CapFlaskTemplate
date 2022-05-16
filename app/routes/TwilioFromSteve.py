# This code does most of the work for the application.  The @app.route code
# "listens" to the websiite to see what page is being requested. If the pages url
# matches the @app.route the it runs the function defined below it.

from app import app
from flask import render_template, redirect, url_for, request, session, flash, Markup
from flask_login import current_user
from mongoengine import Q
from app.classes.data import User, Message
# from app.classes.forms import TxtMessageForm
import datetime as d
import pytz
# This is for the Twilio Credentials
# from .credentials import twilio_account_sid, twilio_auth_token
# Download the helper library from https://www.twilio.com/docs/python/install
from twilio.rest import Client
#import re

from app.utils.secrets import getSecrets
secrets=getSecrets()
account_sid = secrets['TWILIO_AUTH_TOKEN']
auth_token = secrets['TWILIO_SID']
# API Docs: https://www.twilio.com/docs/sms/api/message-resource
client = Client(account_sid, auth_token)

@app.route('/msg/<userID>', methods=['GET', 'POST'])
def msg(userID):
    form = TxtMessageForm()
            
    if form.validate_on_submit():
        
        sentMsg = client.messages.create(
                            body=form.body.data,
                            from_='+19896234883',
                            #status_callback='https://otdata.hsoakland.tech/msgstatus',
                            to=form.to.data
                        )

        # Save sentMsg to OTData
        newMsg = Message(
                twilioid = sentMsg.sid,
                to = sentMsg.to,
                from_ = f'{current_user.fname} {current_user.lname}',
                from_user = current_user,
                body = sentMsg.body,
                datetimesent = d.datetime.utcnow(),
                status = sentMsg.status,
                direction = sentMsg.direction
            )
        newMsg.save()

        form.body.data=''

    msgs = Message.objects(student=student).limit(20)

    return render_template("messages.html", form=form, student=student, msgs=msgs, reloadurl=reloadurl, phoneNumber=phoneNumber )

@app.route('/msgstatus', methods=['GET','POST'])
def msgstatus():

    if request.user_agent == None:
        flash('You are not authorized to access that page because you have no request user agent.')
        return redirect(url_for('index.html'))
    # elif 'TwilioProxy' not in request.user_agent.string:
    #     flash(f'You are not authorized to access that page because you are not Twilio.')
    #     flash(f'You are {request.user_agent.string}')

    #     return redirect(url_for('index'))
            
    # Get the message the user sent our Twilio number
    twilioid = request.values.get('MessageSid', None)
    status = request.values.get('MessageStatus', None)
    try:
        editMsg = Message.objects.get(twilioid = twilioid)
    except:
        return f'{twilioid} status change received from twilio'

    editMsg.update(status=status)

    return f'{twilioid} status change received from twilio'

# https://www.twilio.com/docs/sms/tutorials/how-to-receive-and-reply-python#custom-responses-to-incoming-sms-messages
@app.route('/msgreply', methods=['GET', 'POST'])
def msgreply():

    if request.user_agent == None:
        flash('You are not authorized to access that page because you have no request user agent.')
        return redirect(url_for('index'))
    elif 'TwilioProxy' not in request.user_agent.string:
        flash('You are not authorized to access that page because you are not Twilio.')
        flash(f'You are are {request.user_agent.string}')

        return redirect(url_for('index'))
    '''
    Twilio API Reply parameters
    NoneCombinedMultiDict([ImmutableMultiDict([]), 
    ImmutableMultiDict([('ToCountry', 'US'), 
    ('ToState', 'CA'), 
    ('SmsMessageSid', 'SMd1f0db69422d0ac2c18ada135c3b8e50'), 
    ('NumMedia', '0'), 
    ('ToCity', 'OAKLAND'), 
    ('FromZip', '94608'), 
    ('SmsSid', 'SMd1f0db69422d0ac2c18ada135c3b8e50'), 
    ('FromState', 'CA'), 
    ('SmsStatus', 'received'), 
    ('FromCity', 'OAKLAND'), 
    ('Body', 'Reply to 17th'), 
    ('FromCountry', 'US'), 
    ('To', '+15108043552'), 
    ('ToZip', '94605'), 
    ('NumSegments', '1'), 
    ('MessageSid', 'SMd1f0db69422d0ac2c18ada135c3b8e50'), 
    ('AccountSid', 'ACffcff72d1e02d082d4ce607412b4b5b3'), 
    ('From', '+15107616409'), 
    ('ApiVersion', '2010-04-01')])])Reply to 17th

    '''

    # get the phnum that sent the reply
    replyFrom = request.values.get('From', None)
    # find the last msg sent to that person
    initialMessage = Message.objects(to = replyFrom).first()
    # find the not-student that sent the msg
    notifyNum = '+15107616409'
    try: 
        notifyNum = f"+1{initialMessage.from_user.mobile}"
        reply_to = initialMessage.from_user
    except:
        # TODO hardcoded! Booo!
        notifyNum = '+15107616409'
        reply_to = User.objects.get(otemail='stephen.wright@ousd.org')
    
    replyMsg = Message(
        twilioid = request.values.get('MessageSid', None),
        to = request.values.get('To', None),
        from_ = request.values.get('From', None),
        body = request.values.get('Body', None),
        datetimesent = d.datetime.utcnow(),
        status = request.values.get('SmsStatus', None),
        direction = 'Incoming',
        student = initialMessage.student,
        media = request.values.get('MediaUrl0', None),
        reply_to = reply_to
    )
    replyMsg.save()

    # send notification to the person being replied to
    client = Client(account_sid, auth_token)   
    client.messages.create(
        body=f"New Reply in OTData re {initialMessage.student.fname} {initialMessage.student.lname} From: {request.values.get('From', None)} Body: {request.values.get('Body', None)}",
        from_='+15108043552',
        status_callback='https://otdata-xzxu5z4ybq-uw.a.run.app/msgstatus',
        to=notifyNum
    )

    # TODO Delete this code once I know it is working
    if notifyNum != '+15107616409':
        client.messages.create(
            body=f"New Reply in OTData to {replyMsg.reply_to.fname} {replyMsg.reply_to.lname}",
            from_='+15108043552',
            status_callback='https://otdata-xzxu5z4ybq-uw.a.run.app/msgstatus',
            to='+15107616409'
        )

    return f'sms reply to {reply_to.fname} {reply_to.lname} received from twilio'


@app.route('/msgs/<daysago>')
@app.route('/msgs')
def msgs(daysago=7):
    daysago = int(daysago)
    # sync Twilio to Mongo
    # get twilio msgs from the last two weeks
    datesearch = d.datetime.now(pytz.timezone("America/Los_Angeles")) - d.timedelta(days=daysago)
    msgs = Message.objects(datetimesent__gt = datesearch)
    flash(Markup(f"<h3>All messages from the last {daysago} days </h3>or since {datesearch}.<br>"))

    return render_template('msgs.html', msgs=msgs, daysago=daysago)

@app.route('/msgs/undelivered/<daysago>')
@app.route('/msgs/undelivered')
def undelivered(daysago = 7):
    daysago = int(daysago)
    datesearch = d.datetime.now(pytz.timezone("America/Los_Angeles")) - d.timedelta(days=daysago)
    undmsgs = Message.objects(status='undelivered', datetimesent__gt = datesearch)
    flash(Markup(f"<h3>Undelivered messages from the last {daysago} days</h3>or since {datesearch}.<br>"))

    return render_template('msgs.html',msgs=undmsgs)

@app.route('/msgs/replies/<daysago>')
@app.route('/msgs/replies')
def replies(daysago = 7):
    daysago = int(daysago)
    datesearch = d.datetime.now(pytz.timezone("America/Los_Angeles")) - d.timedelta(days=daysago)
    undmsgs = Message.objects(direction='Incoming', datetimesent__gt = datesearch)
    flash(Markup(f"<h3>Replies from the last {daysago} days</h3>or since {datesearch}.<br>"))

    return render_template('msgs.html',msgs=undmsgs)

# Old Code +++++++++++++++++++++++++++++++++++++++++++++++++++


# Scripts

# Delete a test number from both Twilio and Mongo
@app.route('/deletemsgs')
def deletemessages():
    delnum = '+15107616409'
    client = Client(account_sid, auth_token)
    client.messages.get()

    #delete messages from twilio to the number
    twmsgs = client.messages.list(to=delnum)
    for twmsg in twmsgs:
        client.messages(twmsg.sid).delete()
    
    # delete msgs from twilio from the number
    twmsgs = client.messages.list(from_=delnum)
    for twmsg in twmsgs:
        client.messages(twmsg.sid).delete()

    #delete message to and from the number on mongo
    msgs = Message.objects(Q(to=delnum) | Q(from_=delnum))
    for msg in msgs:
        msg.delete()

    flash('I think they are all deleted')
    return redirect(url_for('msgs'))

@app.route('/stm')
def addstudtomsgs():
    msgs = Message.objects()
    for msg in msgs:
        if msg.to == '+19292442593':
            matchPhone = msg.from_
        else:
            matchPhone = msg.to
        mpac = int(matchPhone[2:5])
        mpf3 = int(matchPhone[5:8])
        mpl4 = int(matchPhone[8:])
        query1 = Q( mobileareacode = mpac) & Q(mobilefirstthree = mpf3) & Q(mobilelastfour = mpl4)
        query2 = Q( otherareacode = mpac) & Q(otherfirstthree = mpf3) & Q(otherlastfour = mpl4)
        query3 = Q( adult1mobileareacode = mpac) & Q(adult1mobilefirst3 = mpf3) & Q(adult1mobilelast4 = mpl4)
        query4 = Q( adult2mobileareacode = mpac) & Q(adult2mobilefirst3 = mpf3) & Q(adult2mobilelast4 = mpl4)
        try:
            stud = User.objects.get(query1 | query2 | query3 | query4)
            msg.update(aeries = stud.aeries)

        except:
            mpac = matchPhone[2:5]
            mpf3 = matchPhone[5:8]
            mpl4 = matchPhone[8:]
            aMatchPhone = f'({mpac}) {mpf3}-{mpl4}'
            aquery = Q(aphone = aMatchPhone) | Q(adult1phone = aMatchPhone) | Q(adult2phone = aMatchPhone)
            try:
                astud = User.objects.get_or_404(aquery)
            except Exception as error:
                flash(f'error line 323 msgs.py {error}')
            else:
                msg.update(aeries = astud)

    return redirect('/')
    
