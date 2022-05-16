from app import app, login
import mongoengine.errors
from flask import render_template, flash, redirect, url_for
from flask_login import current_user
from app.classes.data import Scammer
from app.classes.forms import ScammerForm
from flask_login import login_required
import datetime as dt
@app.route('/scammer/<scammerID>')
@login_required
def scammer(scammerID): 
    
    thisScam = Scammer.objects.get(id=scammerID)

    return render_template('scammer.html',scammer=thisScam)


@app.route('/scammer/new',  methods=['GET', 'POST'])
@login_required
def scammerNew():
   
    scammerForm = ScammerForm()

    if scammerForm.validate_on_submit():
        print("valid form")

        newScammer = Scammer(
            scamNumber = scammerForm.scamNumber.data,
            country = scammerForm.country.data,
            intention = scammerForm.intention.data,
            reporter = current_user.id,
            modifydate = dt.datetime.utcnow
        )
       
        newScammer.save()

        return redirect(url_for('scammer',scammerID=newScammer.id))

    return render_template('scammerform.html', scammerForm=scammerForm)

@app.route('/scammer/all')
@login_required
def scammerAll(): 
    scammers = Scammer.objects()
    return render_template('scammers.html',scammers=scammers)

@app.route('/scammer/edit/<scammerID>')
def scammerEdit(): 
    return render_template('scammer.form')
