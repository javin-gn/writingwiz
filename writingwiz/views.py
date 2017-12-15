import os
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse

from . import database
from .models import PageView

import django.db
import string
import random
import hashlib

# Create your views here.

import re
import urllib
import time
import datetime
from nltk.corpus import stopwords
from django.http import Http404
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from django.db import connection
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.template import RequestContext
from django.contrib.auth import login
from django.contrib.auth import logout
from settings import MEDIA_ROOT
from django.core.management import call_command
from django.core.mail import send_mail
from django.shortcuts import render
from wordnik import *


#User Management Modules

#Request Register Page
def registerPage(request):
    if request.user.is_authenticated():
        usr = request.session["username"]
        superuser = request.session["superuser"] 
        return render(request, 'register.html', {'user': usr, 'superuser': superuser }, context_instance=RequestContext(request))
    return render(request, 'register.html', {'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    
#Request Login Page
def loginPage(request):
    if request.user.is_authenticated():
        usr = request.session["username"]
        superuser = request.session["superuser"] 
        return render(request, 'login.html', {'user': usr, 'superuser': superuser }, context_instance=RequestContext(request))
    return render(request, 'login.html', {'user': "", 'superuser': ""}, context_instance=RequestContext(request))

#Request Forgot Password Page
def forgetPasswordPage(request):
    if request.user.is_authenticated():
        usr = request.session["username"]
        superuser = request.session["superuser"] 
        return render(request, 'forgotpassword.html', {'user': usr, 'superuser': superuser }, context_instance=RequestContext(request))
    return render(request, 'forgotpassword.html', {'user': "", 'superuser': ""}, context_instance=RequestContext(request))

#Request password change to server verifying email address by sending verification code
def requestPasswordChange(request):
    errors = []
    if request.method == 'POST':
        if not request.POST.get('email'):
            errors.append('Email address is empty.')
        else:
            if  '@' not in request.POST['email']:
                errors.append('Email address is not valid.')
            else:
                if not User.objects.filter(username = request.POST['email']).exists():
                    errors.append('Email address does not exists')
        
        if not errors:
            confirmation_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for x in range(33))
            username = request.POST.get('email', '')
            user = User.objects.get(username=username)
            p = user.get_profile()
            p.user = user
            p.confirmation_code = confirmation_code
            p.save()
            title = "astarcompo Request Password Change"
            message = "Dear User,\n\nYou recieved this email because you or someone else requested to change your password. If you requested to change your password please click on the link below, otherwise ignore this email.\n\n" + "http://" + request.get_host() + "/verifyPasswordChange/?code=" + str(p.confirmation_code) + "&user=" + user.username + "\n\nBest Regards,\nastarcompo admin"
            send_mail(title, message, 'astarcompo@gmail.com', [user.email], fail_silently=False)
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>A notification had been send to your email account. </strong><br/> To change your password, click on the link provided in the notification.</div>'
            return render(request, 'forgotpassword.html', {'content': content, 'user': "", 'superuser': "", 'email': request.POST['email']}, context_instance=RequestContext(request))
        else:
            return render(request, 'forgotpassword.html', {'errors': errors, 'user': "", 'superuser': "", 'email': request.POST['email']}, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect('/404/')

#Verify the verification code send by the email, redirect to change password form
def verifyPasswordChange(request):
    errors = []
    try:
        username = request.GET['user']
        confirmation_code = request.GET['code']
        user = User.objects.get(username=username)
        profile = user.get_profile()
        if profile.confirmation_code == confirmation_code:
            change = True
            profile.confirmation_code = ""
            profile.save()
            return render(request, 'changepassword.html', {'canchange': change, 'username': username, 'user': "", 'superuser': "" }, context_instance=RequestContext(request))
        else:
            return render(request, 'changepassword.html', {'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    except:
        return HttpResponseRedirect('/404/')

#Change the password requested
def passwordChange(request):
    errors = []
    if request.method == 'POST':
        username = request.POST.get('username', '')
        if not request.POST.get('password', ''):
            errors.append('Password is empty.')
        if not request.POST.get('cfmpassword', ''):
            errors.append('Confirm Password is empty.')
        if(request.POST.get('password') != request.POST.get('cfmpassword')):
            errors.append('Password does not match.')
        if not errors: 
            user = User.objects.get(username=username)
            user.set_password(request.POST.get('cfmpassword'))
            user.save()
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Your Password has been change. </strong><br/> You can login now with your new password.</div>'
            return render(request, 'login.html', {'content': content, 'next': '/', 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
        else:
            return render(request, 'changepassword.html', {'errors': errors, 'canchange': True, 'username': username, 'password': request.POST['password'], 'cfmpassword': request.POST['cfmpassword'], 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect('/404/')

#Register an account with an email address and password to the server and send confirmation code to the email address specify 
def register(request):
    errors = []
    if request.method == 'POST':
       if not request.POST.get('username'):
           errors.append('Email address is empty.')
       else:
           if '@' not in request.POST['username']:
               errors.append('Email address is not valid.')
       if not request.POST.get('password', ''):
           errors.append('Password is empty.')
       if not request.POST.get('cfmpassword', ''):
           errors.append('Confirm Password is empty.')
       if(request.POST.get('password') != request.POST.get('cfmpassword')):
           errors.append('Password does not match.')
       if User.objects.filter(username = request.POST['username']).exists(): 
           errors.append('Username already exists.')
       if not errors:
           user = User.objects.create_user(request.POST['username'], request.POST['username'], request.POST['password'])
           user.is_active = False
           user.save()
           confirmation_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for x in range(33))
           p = user.get_profile()
           p.user = user
           p.confirmation_code = confirmation_code
           p.save()
           title = "astarcompo Account Confirmation"
           message = "Welcome to astarcompo,\n\nPlease click the link below to activate your account\n\n" + "http://" + request.get_host() + "/verifyAccount/?code=" + str(p.confirmation_code) + "&user=" + user.username + "\n\nBest Regards,\nastarcompo admin"
           send_mail(title, message, 'astarcompo@gmail.com', [user.email], fail_silently=False)
           content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>A notification had been send to your email account. </strong><br/> Please verify your account by clicking on the link provided in the notification. If you cannot recieved the notification, click on the "Resend Notification" Button.</div>'
           con = True
           return render(request, 'confirmation.html', {'con': con, 'content': content, 'code': confirmation_code, 'email': request.POST['username'], 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
       else:
           return render(request, 'register.html', {'errors': errors, 'username': request.POST['username'], 'password': request.POST['password'], 'cfmpassword': request.POST['cfmpassword'],   'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect('/404/')
        
#Verify the account by checking the confirmation code together with the username
def verifyAccount(request):
    try:
        username = request.GET['user']
        confirmation_code = request.GET['code']
        user = User.objects.get(username=username)
        profile = user.get_profile()
        if profile.confirmation_code == confirmation_code:
            profile.confirmation_code = ""
            profile.save()
            user.is_active = True
            user.save()
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Your Account had been activated. </strong><br/> You can login now.</div>'
            return render(request, 'login.html', {'content': content, 'next': '/', 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
        else:
            return HttpResponseRedirect('/404/')
    except:
        return HttpResponseRedirect('/404/')

#Request to resend confirmation code
def resendverifyAccount(request):
    if request.method == 'POST':
        code = request.POST.get('code', '')
        email = request.POST.get('email', '')
        user = request.POST.get('user', '')
        title = "astarcompo Account Confirmation"
        message = "Welcome to asstarcompo,\n\nPlease click the link below to activate your account\n\n" + "http://" + request.get_host() + "/verifyAccount/?code=" + str(code) + "&user=" + user + "\n\nBest Regards,\nastarcompo admin"
        send_mail(title, message, 'astarcompo@gmail.com', [email], fail_silently=False)
        content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>A notification had been send to your email account. </strong><br/> Please verify your account by clicking on the link provided in the notification. If you cannot recieved the notification, click on the "Resend Notification" Button.</div>'
        con = True
        return render(request, 'confirmation.html', {'con': con, 'content': content, 'code': code, 'email': email, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect('/404/')

#Login
def user_login(request):
    errors = []
    if request.method == 'POST':
        url = request.GET['url']
        if not request.POST.get('username'):
           errors.append('Email address is empty.')
        else:
            if '@' not in request.POST['username']:
                errors.append('Email address is not valid.')
        if not request.POST.get('password', ''):
           errors.append('Enter a password.')
        if not errors:
            user = authenticate(username=request.POST['username'], password=request.POST['password'])
            if user is not None:
                # Is the account active? It could have been disabled.
                if user.is_active:
                    # If the account is valid and active, we can log the user in.
                    # We'll send the user back to the homepage.
                    login(request, user)
                    if user.is_superuser:
                        #login as superuser will auto rebuild the index
                        call_command('update_index')
                        request.session["superuser"] = "superuser";
                    else:
                        request.session["superuser"] = "";
                    request.session["username"] = request.POST['username'];
                    return HttpResponseRedirect(url)

                else:
                     errors.append("Your account is inactive. Please Verify your account")
                     return render(request, 'login.html', {'next': url, 'errors': errors, 'user': "", 'superuser': "", 'username': request.POST['username'], 'password': request.POST['password']}, context_instance=RequestContext(request))
            else:
                 errors.append("Invalid Username/password")
                 return render(request, 'login.html', {'next': url,'errors': errors, 'user': "", 'superuser': "", 'username': request.POST['username'], 'password': request.POST['password']}, context_instance=RequestContext(request))
        return render(request, 'login.html', {'next': url,'errors': errors, 'user': "", 'superuser': "", 'username': request.POST['username'], 'password': request.POST['password']}, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect('/404/')
        
#Logout     
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)
    try:
        del request.session["username"]
        del request.session["superuser"];

    except KeyError:
        pass
    # Take the user back to the homepage.
    content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Your are logged out! </strong><br/> You can login again!</div>'
    return render(request, 'login.html', {'content': content, 'next': '/', 'user': ""}, context_instance=RequestContext(request))
    

#Question Management Modules

#Insert Question into the Database
def insertQuestion(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    
    errors = []
    
    if request.method == 'POST':
        superuser = request.session["superuser"];
        if not request.POST.get('question', ''):
           errors.append('Question is empty.')
        if not request.POST.get('type', ''):
           errors.append('Question Type is empty')
        if not request.POST.get('cat', ''):
           errors.append('Question Category is empty')
        if not request.POST.get('answer', ''):
           errors.append('Answer is empty.')
        if request.POST['question'] == "Type your question here":
           errors.append('Question is not in the correct format')
        if request.POST['answer'] == "Type your answer here":
           errors.append('Answer is not in the correct format')
        
        q = request.POST.get('question', '') 
        qt = request.POST.get('type', '') 
        qc = request.POST.get('cat', '') 
        qa = request.POST.get('answer', '')
        th = request.POST.get('theme', '')
        tem = request.POST.get('tem', '')
        
        #print request.POST.get('havetem', '')
        if request.POST.get('havetem', ''):
            if not request.POST.get('tem', ''):
               errors.append('Template is empty')
        
        if not errors:
            if 'pic' in request.FILES:
                ext = os.path.splitext(request.FILES['pic'].name)[1]
                if ext in (".jpg", ".png", ".JPG", ".PNG"):
                    f = str(os.path.splitext(request.FILES['pic'].name)[0]).join(random.choice(string.ascii_uppercase) for i in range(12))
                    hash_object = hashlib.md5(f.encode())
                    save_file(request.FILES['pic'], hash_object.hexdigest(), ext)
                else:
                    errors.append('Only file types of PNG and JPG are supported')
                    return render(request, 'add_question.html', {'errors': errors, 'superuser': superuser}, context_instance=RequestContext(request))
    
            
            cur = connection.cursor()
            cur.execute("SET autocommit=1")
            

            cur.execute("INSERT INTO astarcompo_questions(question, questionCategory, questionType, theme) VALUES(%s, %s, %s, %s)", (q, qc, qt, th))
            
                
            rowid = cur.lastrowid
            
            if tem:
               cur.execute("INSERT INTO astarcompo_situationalTemplates(template, category) VALUES(%s, %s)", (tem, qc))
            
            cur.execute("INSERT INTO astarcompo_model_ans(questionID, ans, userid) VALUES(%s, %s, 1)", (rowid, qa))
                 
            
            if 'pic' in request.FILES:
                cur.execute("INSERT INTO astarcompo_pictorial(questionID, url) VALUES(%s, %s)", (rowid, hash_object.hexdigest() + ext))
            cur.close()
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Question Added Sucessfully! </strong><br/>You can add another below!</div>'
            
            catcontent = '<span id="c"><select class="form-control" name="cat" id="cat">'
            cur1 = connection.cursor()
            cur1.execute("SELECT DISTINCT questionCategory from astarcompo_questions where questionType='%s'" % (qt))
            cats = cur1.fetchall()  
            for cat in cats:
                if cat[0] == qc:
                    catcontent = catcontent + '<option value="%s" selected>%s</option>' % (cat[0], cat[0])
                else:
                    catcontent = catcontent + '<option value="%s">%s</option>' % (cat[0], cat[0])
                    
            catcontent = catcontent + '<option value="Others">Others</option></select></span>'
            cur1.close() 
            typecontent = '<input type="text" value=%s class="form-control" name="type" readonly=true/>' %(qt.title())   
            
            if qt.title()=="Continuous":
                
                paragraphs = qa.split("\n")
                print paragraphs
                counter = 0
                mb = ""
                for i in range(1, len(paragraphs) - 1):
                    mb = mb + paragraphs[i].strip() + "\n"
                    if counter == 0:
                        mb = mb.replace("\n", "")
                    counter = counter + 1
                           
                c = connection.cursor()
                c.execute("SET autocommit=1")
                c.execute("INSERT INTO astarcompo_templates(template, templateType, theme) VALUES(%s, %s, %s)", (paragraphs[0], 'Introduction', th))
                c.execute("INSERT INTO astarcompo_templates(template, templateType, theme) VALUES(%s, %s, %s)", (mb, 'Main Body', th))
                c.execute("INSERT INTO astarcompo_templates(template, templateType, theme) VALUES(%s, %s, %s)", (paragraphs[len(paragraphs)-1], 'Conclusion', th)) 
                c.close()
            
                #theme
                cur2 = connection.cursor()
                cur2.execute("SELECT theme from astarcompo_themes")
                themes = cur2.fetchall()
                cur2.close()
                
                themeddl = '''
                <div class="form-group">
                 <label for="theme" class="col-lg-2 control-label">Theme</label>
                 <div class="col-lg-10">
                   <select class="form-control" name="theme" id="theme">
                '''
   
                for theme in themes:
                   
                    if theme[0]==th:
                        themeddl = themeddl + '<option value="%s" selected>%s</option>' % (th, th)
                    else:
                        themeddl = themeddl + '<option value="%s">%s</option>' % (theme[0], theme[0])
                themeddl = themeddl + '</select></div></div>'
                
                call_command('update_index')
                return render(request, 'add_question.html', {'content': content, 'question': q, 'answer': qa, 'cat': catcontent, 'type': typecontent, 'themes': themeddl, 'superuser': superuser}, context_instance=RequestContext(request))
            
            else:
                
                call_command('update_index')
                return render(request, 'add_question.html', {'content': content, 'question': q, 'answer': qa, 'cat': catcontent, 'type': typecontent, 'superuser': superuser}, context_instance=RequestContext(request))
                
        
        else:
            
            catcontent = '<span id="c"><select class="form-control" name="cat" id="cat">'
            cur3 = connection.cursor()
            cur3.execute("SELECT DISTINCT questionCategory from astarcompo_questions where questionType='%s'" % (qt))
            cats = cur3.fetchall()  
            for cat in cats:
                if cat[0] == qc:
                    catcontent = catcontent + '<option value="%s" selected>%s</option>' % (cat[0], cat[0])
                else:
                    catcontent = catcontent + '<option value="%s">%s</option>' % (cat[0], cat[0])
            catcontent = catcontent + '<option value="Others">Others</option></select></span>'
            cur3.close() 
            typecontent = '<input type="text" value=%s class="form-control" name="type" readonly=true/>' %(qt.title())
            
            if qt.title()=="Continuous":
                #theme
                cur4 = connection.cursor()
                cur4.execute("SELECT theme from astarcompo_themes")
                themes = cur4.fetchall()
                cur4.close()
            
                themeddl = '''
                <div class="form-group">
                 <label for="theme" class="col-lg-2 control-label">Theme</label>
                 <div class="col-lg-10">
                   <select class="form-control" name="theme" id="theme">
                '''
   
                for theme in themes:
                    if theme[0]==th:
                       
                        themeddl = themeddl + '<option value="%s" selected>%s</option>' % (th, th)
                    else:
                        themeddl = themeddl + '<option value="%s">%s</option>' % (theme[0], theme[0])
                themeddl = themeddl + '</select></div></div>'
                return render(request, 'add_question.html', {'errors': errors, 'question': q, 'answer': qa, 'cat': catcontent, 'type': typecontent, 'themes': themeddl, 'superuser': superuser  }, context_instance=RequestContext(request))
            else:
                sit =   '''
                        <div class="form-group" id="sittem">
			         
        			    </div>
                
                        '''
                return render(request, 'add_question.html', {'errors': errors, 'sit': sit, 'question': q, 'answer': qa, 'cat': catcontent, 'type': typecontent, 'superuser': superuser  }, context_instance=RequestContext(request))
           

    return render(request, '404.html', {}, context_instance=RequestContext(request))

#Request page to edit question
def editQuestion(request):
    
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    superuser = request.session["superuser"];
    username = request.session["username"]
    qid = request.GET.get('id', '')   
 
    cur2 = connection.cursor()
    cur3 = connection.cursor()
    cur2.execute("SELECT question, questionCategory, questionType, theme from astarcompo_questions where questionID = '"+qid+"'")
    cur3.execute("SELECT url from astarcompo_pictorial where questionID = '"+qid+"'")

    content = ""
    if cur2.rowcount == 0:
        return render(request, '404.html', {}, context_instance=RequestContext(request))
    else:
        question = cur2.fetchone()
        
        cur4 = connection.cursor()
        cur4.execute("SELECT DISTINCT questionCategory from astarcompo_questions where questionType='%s'" % (question[2]))
        cats = cur4.fetchall()
        catcontent=""
        if cur4.rowcount==0:
            return render(request, '404.html', {}, context_instance=RequestContext(request))
        catcontent = '<span id="c"><select class="form-control" name="cat" id="cat">'
        

        for cat in cats:
            if cat[0]==question[1]:
                catcontent = catcontent + '<option value ="%s" selected>%s</option>' % (cat[0], cat[0])
            else:
                catcontent = catcontent + '<option value ="%s">%s</option>' % (cat[0], cat[0])
        
        catcontent = catcontent + '<option value="Others">Others</option></select></span>'
        
     
        
        cur4.close()
    
        #catcontent = '<input type="text" class="form-control" id="cat" name="cat" value="%s">' %(question[1])
        ques = question[0]
        qtheme = question[3]
        
        typecontent = '<input type="text" class="form-control" id="type" readonly="true"  name="type" value="%s">' %(question[2])
        
        '''
        if question[2]=="Continuous":
            typecontent = '<select class="form-control" name="type" id="type"><option value="Continuous" selected>Continuous</option><option value="Situational">Situational</option></select>'
        elif question[2]=="Situational":
            typecontent = '<select class="form-control" name="type" id="type"><option value="Continuous">Continuous</option><option value="Situational" selected>Situational</option></select>'
        
        '''
        
        pic = cur3.fetchone()
        picture=""
        if cur3.rowcount!=0:
            picture ='<div class="form-group"><label for="picture" class="col-lg-2 control-label">Current Picture</label><div class="col-lg-10"><div class="panel panel-default"><div class="panel-body"><img src="%s/%s"/></div></div></div><label for="picture" class="col-lg-2 control-label">Picture</label><div class="col-lg-10"><input name="pic" class="form-control" type="file"/></div></div>' % ("/static/pictures", (pic[0]))
        cur2.close()    
        cur3.close()
        
        if question[2]=="Continuous":
            #theme
            cur5 = connection.cursor()
            cur5.execute("SELECT theme from astarcompo_themes")
            themes = cur5.fetchall()
            cur5.close()
    
            themeddl = '''
            <div class="form-group">
 	         <label for="theme" class="col-lg-2 control-label">Theme</label>
 	         <div class="col-lg-10">
             <select class="form-control" name="theme" id="theme">'
            
            '''
    
            for theme in themes:
                if qtheme == theme[0]:
                    themeddl = themeddl + '<option value="%s" selected>%s</option>' % (qtheme, qtheme)
                else:
                    themeddl = themeddl + '<option value="%s">%s</option>' % (theme[0], theme[0])
    
            themeddl = themeddl + '</select></div></div>'
            
        
            return render(request, 'edit_question.html', {'qid': qid, 'question': ques, 'themes': themeddl, 'picture': picture, 'cat': catcontent, 'type': typecontent, 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
        else:
            sit =   '''
                    <div class="form-group" id="sittem">
			         
    			    </div>
                
                    '''
            
            return render(request, 'edit_question.html', {'qid': qid, 'sit': sit, 'question': ques, 'picture': picture, 'cat': catcontent, 'type': typecontent, 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))

#Request page to edit answer
def editAnswer(request):
    
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    superuser = request.session["superuser"];
    username = request.session["username"]
    qid = request.GET.get('qid', '')  
    aid = request.GET.get('aid', '')
 
    cur = connection.cursor()
    cur.execute("SELECT ans FROM astarcompo_model_ans where ansID = '"+aid+"'")

    cur2 = connection.cursor()
    cur3 = connection.cursor()
    content = ""
    cur2.execute("SELECT question, questionCategory, questionType, theme from astarcompo_questions where questionID = '"+qid+"'")
    cur3.execute("SELECT url from astarcompo_pictorial where questionID = '"+qid+"'")

    if cur.rowcount == 0:
        return render(request, '404.html', {}, context_instance=RequestContext(request))
    else:
        answer = cur.fetchone()
        question = cur2.fetchone()
        cat = '<span class="label label-default">%s</span>' % (question[1])
        ty = '<span class="label label-primary">%s</span>' % (question[2])
        theme = '<span class="label label-primary">%s</span>' % (question[3])
        
        if theme:
            content = '<h3>Question: </h3><br/> <p class="text-success">%s</p> <br/><br/>' % (question[0].replace('\n','<br/>')) + 'Category: ' + cat + ' Type: ' + ty + ' Theme: ' + theme + '<br/><br/>'
        else:
            content = '<h3>Question: </h3><br/> <p class="text-success">%s</p> <br/><br/>' % (question[0].replace('\n','<br/>')) + 'Category: ' + cat + ' Type: ' + ty + '<br/><br/>'
        
        pic = cur3.fetchone()
        if cur3.rowcount!=0:
           content = content + '<img src=%s/%s class="img-responsive"/>' % ("/static/pictures", (pic[0]))
        cur.close()
        cur2.close()    
        cur3.close()
        return render(request, 'edit_answer.html', {'qid': qid, 'content': content, 'aid': aid, 'answer': answer[0], 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))


#Update the question to the database
def updateQuestion(request):
    errors = []

    if request.method == 'POST':
        superuser = request.session["superuser"];
        if not request.POST.get('question', ''):
           errors.append('Question is empty.')
        if not request.POST.get('type', ''):
           errors.append('Question Type is empty')
        if not request.POST.get('cat', ''):
           errors.append('Question Category is empty')
        if not errors:
            if 'pic' in request.FILES:
                ext = os.path.splitext(request.FILES['pic'].name)[1]
                if ext in (".jpg", ".png", ".JPG", ".PNG"):
                    f = str(os.path.splitext(request.FILES['pic'].name)[0]).join(random.choice(string.ascii_uppercase) for i in range(12))
                    hash_object = hashlib.md5(f.encode())
                    save_file(request.FILES['pic'], hash_object.hexdigest(), ext)
                else:
                    errors.append('Only file types of PNG and JPG are supported')
                    return render(request, 'edit_question.html', {'errors': errors, 'superuser': superuser}, context_instance=RequestContext(request))
            
            qid = request.POST.get('qid', '') 
            q = request.POST.get('question', '') 
            qt = request.POST.get('type', '') 
            qc = request.POST.get('cat', '') 
            qtheme = request.POST.get('theme', '')
            tem = request.POST.get('tem', '')


            cur = connection.cursor()
            cur.execute("SET autocommit=1")
            cur.execute("UPDATE astarcompo_questions SET question=%s, questionCategory=%s, questionType=%s, theme=%s WHERE questionID=%s" , (q, qc, qt, qtheme, qid))
         
            if tem:
                cur.execute("INSERT INTO astarcompo_situationalTemplates(template, category) VALUES(%s, %s)", (tem, qc))
            
            if 'pic' in request.FILES:
                cur.execute("UPDATE astarcompo_pictorial SET urL = %s WHERE questionID=%s" , ((hash_object.hexdigest() + ext), qid))
            
            cur.close()
            
            call_command('update_index')
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Question Updated! </strong></div>'
            
            catcontent = '<span id="c"><select class="form-control" name="cat" id="cat">'
            cur1 = connection.cursor()
            cur1.execute("SELECT DISTINCT questionCategory from astarcompo_questions where questionType='%s'" % (qt))
            cats = cur1.fetchall()  
            
            for cat in cats:
                if cat[0]==qc:
                    catcontent = catcontent + '<option value="%s" selected>%s</option>' % (cat[0], cat[0])
                else:
                    catcontent = catcontent + '<option value="%s">%s</option>' % (cat[0], cat[0])
                    
            catcontent = catcontent + '<option value="Others">Others</option></select></span>'
            cur1.close() 
            

            typecontent = '<input type="text" class="form-control" id="type" readonly="true" name="type" value="%s">' %(qt)
            
            if qt=="Continuous":
                #theme
                cur2 = connection.cursor()
                cur2.execute("SELECT theme from astarcompo_themes")
                themes = cur2.fetchall()
                cur2.close()
            
            
                themeddl = '''
                <div class="form-group">
                 <label for="theme" class="col-lg-2 control-label">Theme</label>
                 <div class="col-lg-10">
                   <select class="form-control" name="theme" id="theme">
                '''
   
                for theme in themes:
                    if qtheme==theme[0]:
                        themeddl = themeddl + '<option value="%s" selected>%s</option>' % (qtheme, qtheme)
                    else:
                        themeddl = themeddl + '<option value="%s">%s</option>' % (theme[0], theme[0])
                themeddl = themeddl + '</select></div></div>'
                
            
                return render(request, 'edit_question.html', {'qid': qid, 'question': q, 'content': content, 'errors': errors, 'cat': catcontent, 'type': typecontent, 'themes': themeddl, 'superuser': superuser}, context_instance=RequestContext(request))
            else:
                
                return render(request, 'edit_question.html', {'qid': qid, 'question': q, 'content': content, 'errors': errors, 'cat': catcontent, 'type': typecontent, 'superuser': superuser}, context_instance=RequestContext(request))
            
        else:
            qid = request.POST.get('qid', '') 
            q = request.POST.get('question', '') 
            qt = request.POST.get('type', '') 
            qc = request.POST.get('cat', '')
            
            catcontent = '<span id="c"><select class="form-control" name="cat" id="cat">'
            cur3 = connection.cursor()
            cur3.execute("SELECT DISTINCT questionCategory from astarcompo_questions where questionType='%s'" % (qt))
            cats = cur3.fetchall()  
            
            for cat in cats:
                if cat[0]==qc:
                    catcontent = catcontent + '<option value="%s" selected>%s</option>' % (cat[0], cat[0])
                else:
                    catcontent = catcontent + '<option value="%s">%s</option>' % (cat[0], cat[0])
                    
            catcontent = catcontent + '<option value="Others">Others</option></select></span>'
            cur3.close() 
    
            if qt=="Continuous":
                typecontent = '<select class="form-control" name="type" id="type"><option value="Continuous" selected>Continuous</option><option value="Situational">Situational</option></select>'
            elif qt=="Situational":
                typecontent = '<select class="form-control" name="type" id="type"><option value="Continuous">Continuous</option><option value="Situational" selected>Situational</option></select>'
            
            
            #theme
            cur4 = connection.cursor()
            cur4.execute("SELECT theme from astarcompo_themes")
            themes = cur4.fetchall()
            cur4.close()
            
            themeddl = '''
            <div class="form-group">
             <label for="theme" class="col-lg-2 control-label">Theme</label>
             <div class="col-lg-10">
               <select class="form-control" name="theme" id="theme">
            '''
            for theme in themes:
               themeddl = themeddl + '<option value="%s">%s</option>' % (theme[0], theme[0])
            themeddl = themeddl + '</select></div></div>'
            
            
            return render(request, 'edit_question.html', {'qid': qid, 'question': q, 'errors': errors, 'cat': catcontent, 'type': typecontent, 'themes': themeddl, 'superuser': superuser}, context_instance=RequestContext(request))
  
    return render(request, '404.html', {}, context_instance=RequestContext(request))

#Update the answer to the database
def updateAnswer(request):
    errors = []
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    
    if request.method == 'POST':
        aid = request.POST.get('aid', '')
        qid = request.POST.get('qid', '')
        superuser = request.session["superuser"];
        username = request.session["username"]
        
        
        if not request.POST.get('answer', ''):
           errors.append('Answer is empty.')

        if not errors:
            qa = request.POST.get('answer', '')
     
            cur = connection.cursor()
            cur.execute("SET autocommit=1")
            cur.execute("UPDATE astarcompo_model_ans SET ans=%s WHERE ansID=%s" , (qa, aid))
            cur.close()
            call_command('update_index')
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Answer Updated! </strong></div>'
            
            cur2 = connection.cursor()
            cur3 = connection.cursor()
            cur4 = connection.cursor()
            cur2.execute("SELECT question, questionCategory, questionType, theme from astarcompo_questions where questionID = '"+qid+"'")
            cur3.execute("SELECT url from astarcompo_pictorial where questionID = '"+qid+"'")
            cur4.execute("SELECT ans from astarcompo_model_ans where ansID = '"+aid+"'")
            
            question = cur2.fetchone()
            ans = cur4.fetchone()
            cat = '<span class="label label-default">%s</span>' % (question[1])
            ty = '<span class="label label-primary">%s</span>' % (question[2])
            theme = '<span class="label label-primary">%s</span>' % (question[3])
            if theme:
                content = content + '<h3>Question: </h3><br/> <p class="text-success">%s</p> <br/><br/>' % (question[0].replace('\n','<br/>')) + 'Category: ' + cat + ' Type: ' + ty + ' Theme: ' + theme + '<br/></br>'
            else:
                content = content + '<h3>Question: </h3><br/> <p class="text-success">%s</p> <br/><br/>' % (question[0].replace('\n','<br/>')) + 'Category: ' + cat + ' Type: ' + ty + '<br/></br>'
            pic = cur3.fetchone()
            if cur3.rowcount!=0:
               content = content + '<div class="panel panel-default"><div class="panel-body"><img src=%s/%s class="img-responsive"/></div></div>' % ("/static/pictures", (pic[0]))
            cur2.close()    
            cur3.close()
            cur4.close()
            return render(request, 'edit_answer.html', {'qid': qid, 'aid': aid, 'errors': errors, 'content': content, 'answer': ans[0], 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))
            
        else:
            cur5 = connection.cursor()
            cur5.execute("SELECT ans from astarcompo_model_ans where ansID = '"+aid+"'")
            ans = cur5.fetchone()
            cur5.close()
            return render(request, 'edit_answer.html', {'qid': qid, 'aid': aid, 'errors': errors, 'answer': ans[0], 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))
    return render(request, '404.html', {}, context_instance=RequestContext(request))


#Delete Question
def deleteQuestion(request):
    superuser = request.session["superuser"]
    if superuser:
        qid = request.GET.get('id', '')
        qtype = request.GET.get('type', '')
        cur = connection.cursor()
        cur.execute("SET autocommit=1")
        cur.execute("DELETE FROM astarcompo_questions WHERE questionID='%s'"% (qid))
        cur.execute("SELECT ansid FROM astarcompo_model_ans WHERE questionID='%s'"% (qid))
        aid = cur.fetchone()
        cur.execute("DELETE FROM astarcompo_model_ans WHERE questionID='%s'"% (qid))
        cur.execute("DELETE FROM astarcompo_pictorial WHERE questionID='%s'"% (qid))
        cur.execute("DELETE FROM astarcompo_modelAnswerComments WHERE ansid='%s'"% (aid[0]))

        cur.close()
        return HttpResponseRedirect('/%s/' %(qtype.lower()))
    return render(request, '404.html', {'user': user}, context_instance=RequestContext(request))
    
        
#Browse Question Modules


def questions(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next': request.path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    
    ty = request.GET['type']
    query = request.GET['query']
    cur = connection.cursor()
    content = "<ol>"
    numrows = 0
    if ty == 'Category':
        cur.execute("SELECT questionID, question from astarcompo_questions where questionType='Continuous' AND questionCategory='%s'" %(query))
        questions = cur.fetchall()
        numrows = cur.rowcount
        for question in questions:
            content = content + '<li><p class="text-info"><a href="javascript:loadQuestion(\'/browse_mini/?id=%s\');">%s</a></p><p class="text-success">http://%s/browse/?id=%s</p></li>' % (question[0], question[1].replace('\n','<br/>'), request.get_host(), question[0])         
    elif ty == "Theme":
        cur.execute("SELECT theme from astarcompo_themes where themeID='%s'" %(query))
        theme = cur.fetchone()
        cur.execute("SELECT questionID, question from astarcompo_questions where questionType='Continuous' AND theme='%s'" %(theme[0]))
        questions = cur.fetchall()
        numrows = cur.rowcount
        for question in questions:
            content = content + '<li><p class="text-info"><a href="javascript:loadQuestion(\'/browse_mini/?id=%s\');">%s</a></p><p class="text-success">http://%s/browse/?id=%s</p></li>' % (question[0], question[1].replace('\n','<br/>'), request.get_host(), question[0])
    cur.close()    
    content = content + "</ol>"
    
    if numrows == 0:
        content = "<h1>No Questions</h1>"
    t = get_template('questions.html')
    c = Context({'content': content })
    html = t.render(c)
    return HttpResponse(html)    


#Request composition category of "Continuous" type
def continuous(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next': request.path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    username = request.session["username"]
    superuser = request.session["superuser"]
    
    content = ""
    
    #get all categories
    cur = connection.cursor()
    cur.execute("SELECT DISTINCT questionCategory from astarcompo_questions where questionType='Continuous'")
    cats = cur.fetchall() 
    
    #get all themes
    cur.execute("SELECT theme FROM astarcompo_themes")
    themes = cur.fetchall()
    
    if len(cats) == 0 or len(themes)==0:
        content = '<p class="text-warning">No Questions found in the Database for this category</p>'
    else:    
        catlist = '<ul class="list-group">'    
        for cat in cats:
            cur.execute("SELECT COUNT(*) from astarcompo_questions where questionType='Continuous' AND questionCategory='%s'" % (cat[0]))
            row = cur.fetchone()
            catlist = catlist  + "<a href=\"javascript:loadQuestions('%s', 'Category')\"><li class=\"list-group-item\"><span class=\"badge\">%s</span>%s</li></a>" % (cat[0], row[0], cat[0])
        catlist = catlist + '</ul>'
        
        themelist = '<ul class="list-group">'
        for theme in themes:
            cur.execute("SELECT COUNT(*) from astarcompo_questions where theme='%s'" % (theme[0]))
            row = cur.fetchone()
            cur.execute("SELECT themeID from astarcompo_themes where theme='%s'" % (theme[0]))
            t = cur.fetchone()
            themelist =  themelist + "<a href=\"javascript:loadQuestions('%s', 'Theme')\"><li class=\"list-group-item\"><span class=\"badge\">%s</span>%s</li></a>" % (t[0], row[0], theme[0])
        themelist = themelist + '</ul>'
        content = '<div id="questions"></div>'
    
    #display add question button if is super user
    addQuestionBtn = ""
    if superuser:
        addQuestionBtn = '<button type="button" onclick="window.location.href=\'/add_question/?type=Continuous\'" class="btn btn-primary">Add Question</button><br/>'
    
    cur.close()    
    t = get_template('continuous.html')
    c = Context({'content': content, 'user': username, 'superuser': superuser, 'catlist': catlist, 'themelist': themelist, 'addQuestionBtn': addQuestionBtn })
    html = t.render(c)
    return HttpResponse(html)
    
#Request composition category of "Situational" type
def situational(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next': request.path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    username = request.session["username"]
    superuser = request.session["superuser"]
    lists=""
    cur = connection.cursor()
    cur.execute("SELECT DISTINCT questionCategory from astarcompo_questions where questionType='Situational'")
    cats = cur.fetchall() 
    cur.close()
    content = ""
    if len(cats) == 0:
        content = '<p class="text-warning">No Questions found in the Database for this category</p>'
        if superuser:
            lists = '<button type="button" onclick="window.location.href=\'/add_question/?type=Situational\'" class="btn btn-primary">Add Question</button><br/>'
        t = get_template('situational.html')
        c = Context({'content': content, 'user': username, 'superuser': superuser, 'list': lists })
        html = t.render(c)
    else:
        lists = '<ul class="list-group">'
        fullcontent = '<div id="main">'
        for cat in cats:
            cur1 = connection.cursor()
            cur1.execute("SELECT * from astarcompo_questions where questionType='Situational' AND questionCategory='%s'" % (cat[0]))
            cur2 = connection.cursor()
            cur2.execute("SELECT questionID, question from astarcompo_questions where questionType='Situational' AND questionCategory='%s'" % (cat[0]))
            questions = cur2.fetchall() 
            cur2.close()

            if len(questions) == 0:
                content = '<p class="text-warning">There are currently no questions in the database</p>'
            else:
                content = '<div id="question" style="display:none"></div><div id="%s" style="display:none"><ol>' % (cat[0])
                for question in questions:
                    content = content  + '<li><p class="text-info"><a href="javascript:loadQuestion(\'/browse_mini/?id=%s\');">%s</a></p><p class="text-success">http://%s/browse/?id=%s</p></li>' % (question[0], question[1].replace('\n','<br/>'), request.get_host(), question[0])
                content = content + "</ol></div>"
                fullcontent = fullcontent + content
            lists = lists  + "<a href=\"javascript:getQuestions('%s')\"><li class=\"list-group-item\"><span class=\"badge\">%s</span>%s</li></a>" % (cat[0], cur1.rowcount, cat[0])
        lists = lists + '</ul>'
        if superuser:
            lists = lists + '<button type="button" onclick="window.location.href=\'/add_question/?type=Situational\'" class="btn btn-primary">Add Question</button>'
        cur1.close()
        fullcontent = fullcontent + "</div>"
        t = get_template('situational.html')
        c = Context({'content': fullcontent, 'user': username, 'superuser': superuser, 'list': lists })
        html = t.render(c)
    return HttpResponse(html)
    
    
#Display a question specifying the Question ID
def browse(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    superuser = request.session["superuser"];
    username = request.session["username"]
    qid = request.GET.get('id', '')     
    cur = connection.cursor()
    cur2 = connection.cursor()
    cur3 = connection.cursor()
    cur.execute("SELECT a.ans, a.ansID, a.userid from astarcompo_questions q, astarcompo_model_ans a where q.questionID = '"+qid+"' and q.questionID = a.questionID")
    cur2.execute("SELECT question, questionCategory, questionType, theme from astarcompo_questions where questionID = '"+qid+"'")
    cur3.execute("SELECT url from astarcompo_pictorial where questionID = '"+qid+"'")
    quesAndAns = cur.fetchall()
    cur.close()
    count = 1
    content = ""
    editq=""
    edita=""
    if cur2.rowcount == 0:
        content = "<h1>The Question does not exist!</h1>"
        return render(request, 'browse.html', {'content': content, 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
    else:
        question = cur2.fetchone()
        cat = '<span class="label label-default">%s</span>' % (question[1])
        ty = '<span class="label label-primary">%s</span>' % (question[2])
        
        theme = '<span class="label label-primary">%s</span>' % (question[3])
        
        
        if superuser:
            editq = '<a href="/edit_question/?id=%s"><button type="button" class="btn btn-primary">Edit Question</button></a>&nbsp;<a href="/confirmDelete/?dtype=question&id=%s&type=%s"><button type="button" class="btn btn-primary">Delete Question</button></a>' % (qid, qid ,question[2])
            
        if question[3]:
            content = '<p>&nbsp;</p><p class="text-success">%s</p>' % (question[0].replace('\n','<br/>')) + '<p>Category: ' + cat + '&nbsp;Type: ' + ty + '&nbsp;Theme: ' + theme + '</p>'
        else:
            content = '<p>&nbsp;</p><p class="text-success">%s</p>' % (question[0].replace('\n','<br/>')) + '<p>Category: ' + cat + '&nbsp;Type: ' + ty + '</p>'
            
        content = content + '<br/><p><button type="button"  onclick="window.location.href=\'/try/?id=%s\'" class="btn btn-info">Try this question</button>&nbsp;' % (qid) +  editq +'</p><br/>'
        pic = cur3.fetchone()
        if cur3.rowcount!=0:
            content = content + '<br/><br/><div class="panel panel-default"><div class="panel-body"><img src=%s/%s class="img-responsive"/></div></div><div id="accordion">' % ("/static/pictures", (pic[0]))
        else:
            content = content +  '<div class="panel-group" id="accordion">'
  
        for q in quesAndAns:
            
            vps = commonPhrasesVocabs(q[0].replace('\n',' '))
            vpss = ""
            for vp in vps:
                if vp:
                    if re.match(r'\A[\w-]+\Z', vp):
                        word = '<a href="#myModal" data-toggle="modal" data-load-remote="/dictionary/?word=%s" data-remote-target="#myModal .modal-body">%s</a>' %(vp, vp)
                        #word = '<a href="javascript:window.open(\'/dictionary/?word=%s\', \'_blank\', \'toolbar=no, scrollbars=no, resizable=no, width=400, height=400\');">%s</a>' %(vp, vp)
                        vpss = vpss + word + "<br/>"   
                    else:
                        vpss = vpss + '<a href="https://www.google.com.sg/#q=%s" target="_blank">' %(vp) + vp + "</a><br/>" 
                    
            if superuser:
                edita = '<a href="/edit_answer/?qid=%s&aid=%s"><button type="button" class="btn btn-primary">Edit Answer</button></a><br/>' % (qid, q[1])
            
            cr = connection.cursor()
            cr.execute("SELECT username FROM auth_user WHERE id = '%s'" %(q[2]))
            uname = cr.fetchone()
            print q[2]
            u = uname[0].split("@")
            cr.close()
            comments = retrieveComments(request, q[1])
            #if count == 1:
                #content = content + '<div class="panel panel-default"><div class ="panel-heading"><h3 class="panel-title"><a data-toggle="collapse" data-parent="#accordion" href="#collapse%s"> Sample %s ' % (count, count) + '</a></h3></div><div id="collapse%s" class="panel-collapse collapse in"><div class="panel-body">' %(count) + edita + '<br/>Submitted by: %s <br/><br/>%s <br/><br/><div class="panel panel-primary"><div class="panel-heading"><h3 class="panel-title">Useful Vocabularies & Phrases</h3></div><div class="panel-body">%s</div></div><div class="panel panel-primary"><div class="panel-heading"><h3 class="panel-title">Comments</h3></div><div class="panel-body">%s</div></div></div></div></div>' % ( u[0], (q[0].replace('\n','<br/>')), vpss, comments)
            #else:
            content = content + '<div class="panel panel-default"><div class ="panel-heading"><h3 class="panel-title"><a data-toggle="collapse" data-parent="#accordion" href="#collapse%s"> Sample %s ' % (count, count) + '</a></h3></div><div id="collapse%s" class="panel-collapse collapse"><div class="panel-body">' %(count) + edita + '<br/>Submitted by: %s <br/><br/>%s <br/><br/><div class="panel panel-primary"><div class="panel-heading"><h3 class="panel-title">Vivid Vocabulary used in this composition</h3></div><div class="panel-body"><p>Click on the word to view its definition!</p>%s</div></div><div class="panel panel-primary"><div class="panel-heading"><h3 class="panel-title">Comments</h3></div><div class="panel-body">%s</div></div></div></div></div>' % ( u[0], (q[0].replace('\n','<br/>')), vpss, comments)
            count = count + 1; 
        content = content + '</div>';

    cur2.close()    
    cur3.close()
    return render(request, 'browse.html', {'content': content, 'cat': cat, 'type': ty, 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
    
#Display Questions based on the question category and type
def browse_mini(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    superuser = request.session["superuser"];
    username = request.session["username"]
    qid = request.GET.get('id', '')     
    cur = connection.cursor()
    cur2 = connection.cursor()
    cur3 = connection.cursor()
    cur.execute("SELECT a.ans, a.ansID, a.userid from astarcompo_questions q, astarcompo_model_ans a where q.questionID = '"+qid+"' and q.questionID = a.questionID")
    cur2.execute("SELECT question, questionCategory, questionType, theme from astarcompo_questions where questionID = '"+qid+"'")
    cur3.execute("SELECT url from astarcompo_pictorial where questionID = '"+qid+"'")
    quesAndAns = cur.fetchall()
    cur.close()
    count = 1
    content = ""
    editq=""
    edita=""
    if cur2.rowcount == 0:
        content = "<h1>The Question does not exist!</h1>"
        return render(request, 'browsemini.html', {'content': content, 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
    else:
        question = cur2.fetchone()
        cat = '<span class="label label-default">%s</span>' % (question[1])
        ty = '<span class="label label-primary">%s</span>' % (question[2])
        theme = '<span class="label label-primary">%s</span>' % (question[3])
        
        if superuser:
            editq = '<a href="/edit_question/?id=%s"><button type="button" class="btn btn-primary">Edit Question</button></a>&nbsp;<a href="/confirmDelete/?dtype=question&id=%s&type=%s"><button type="button" class="btn btn-primary">Delete Question</button></a>' % (qid, qid, question[2])
            
        if question[3]:
            content = '<p class="text-success">%s</p>' % (question[0].replace('\n','<br/>')) + '<p>Category: ' + cat + '&nbsp;Type: ' + ty + '&nbsp;Theme: ' + theme +  '</p>'
        else:
            content = '<p class="text-success">%s</p>' % (question[0].replace('\n','<br/>')) + '<p>Category: ' + cat + '&nbsp;Type: ' + ty + '</p>'
        
        content = content + '<br/><p><button type="button"  onclick="window.location.href=\'/try/?id=%s\'" class="btn btn-info">Try this question</button>&nbsp;' % (qid) +  editq +'</p><br/>'
        pic = cur3.fetchone()
        if cur3.rowcount!=0:
            content = content + '<br/><br/><div class="panel panel-default"><div class="panel-body"><img src=%s/%s class="img-responsive"/></div></div><div id="accordion">' % ("/static/pictures", (pic[0]))
        else:
            content = content +  '<div id="accordion">'

      
        for q in quesAndAns:
           
            vps = commonPhrasesVocabs(q[0].replace('\n',' '))
            vpss = ""
            for vp in vps:
                if vp:
                    if re.match(r'\A[\w-]+\Z', vp):
                        word = '<a href="#myModal" data-toggle="modal" data-load-remote="/dictionary/?word=%s" data-remote-target="#myModal .modal-body">%s</a>' %(vp, vp)
                        #word = '<a href="javascript:window.open(\'/dictionary/?word=%s\', \'_blank\', \'toolbar=no, scrollbars=no, resizable=no, width=400, height=400\');">%s</a>' %(vp, vp)
                        vpss = vpss + word + "<br/>" 
                    else:
                        vpss = vpss + '<a href="https://www.google.com.sg/#q=%s" target="_blank">' %(vp) + vp + "</a><br/>" 
            

            if superuser:
                edita = '<a href="/edit_answer/?qid=%s&aid=%s"><button type="button" class="btn btn-primary">Edit Answer</button></a><br/>' % (qid, q[1])
            
            cr = connection.cursor()
            cr.execute("SELECT username FROM auth_user WHERE id = '%s'" %(q[2]))
            uname = cr.fetchone()
            u = uname[0].split("@")
            cr.close()
            comments = retrieveComments(request, q[1])
            #if count == 1:
                #content = content + '<div class="panel panel-default"><div class ="panel-heading"><h3 class="panel-title"><a data-toggle="collapse" data-parent="#accordion" href="#collapse%s"> Sample %s ' % (count, count) + '</a></h3></div><div id="collapse%s" class="panel-collapse collapse in"><div class="panel-body">' %(count) + edita + '<br/>Submitted by: %s <br/><br/>%s <br/><br/><div class="panel panel-primary"><div class="panel-heading"><h3 class="panel-title">Useful Vocabularies & Phrases</h3></div><div class="panel-body">%s</div></div><div class="panel panel-primary"><div class="panel-heading"><h3 class="panel-title">Comments</h3></div><div class="panel-body">%s</div></div></div></div></div>' % ( u[0], (q[0].replace('\n','<br/>')), vpss, comments)
            #else:
            content = content + '<div class="panel panel-default"><div class ="panel-heading"><h3 class="panel-title"><a data-toggle="collapse" data-parent="#accordion" href="#collapse%s"> Sample %s ' % (count, count) + '</a></h3></div><div id="collapse%s" class="panel-collapse collapse"><div class="panel-body">' %(count) + edita + '<br/>Submitted by: %s <br/><br/>%s <br/><br/><div class="panel panel-primary"><div class="panel-heading"><h3 class="panel-title">Vivid Vocabulary used in this composition</h3></div><div class="panel-body"><p>Click on the word to view its definition!</p>%s</div></div><div class="panel panel-primary"><div class="panel-heading"><h3 class="panel-title">Comments</h3></div><div class="panel-body">%s</div></div></div></div></div>' % ( u[0], (q[0].replace('\n','<br/>')), vpss, comments)
            count = count + 1; 
        content = content + '</div>';
 
           
    cur2.close()    
    cur3.close()
    return render(request, 'browsemini.html', {'content': content, 'cat': cat, 'type': ty, 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
    
#Insert answer into Database
def insertAnswer(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    
    errors = []
    if request.method == 'POST':
        qid = request.POST.get('qid', '')
        superuser = request.session["superuser"];
        username = request.session["username"]
        if not request.POST.get('answer', ''):
           errors.append('Answer is empty.')
        if request.POST['answer'] == "Type your answer here":
           errors.append('Answer is not in a correct format')
        qa = request.POST.get('answer', '')
        
        if not errors:
           
     
            cu = connection.cursor()
            cu.execute("SELECT id from auth_user where username = '%s'" %(username))
            userid = cu.fetchone()
            cu.close()
            
            cur = connection.cursor()
            cur.execute("SET autocommit=1")
            cur.execute("INSERT INTO astarcompo_model_ans(questionID, ans, userid) VALUES(%s, %s, %s)", (qid, qa, userid[0]))
            cur.close()
          
            cur2 = connection.cursor()
            cur3 = connection.cursor()
            #cur.execute("SELECT a.ans, a.ansID from astarcompo_questions q, astarcompo_model_ans a where q.questionID = '"+qid+"' and q.questionID = a.questionID")
            cur2.execute("SELECT question, questionCategory, questionType, theme from astarcompo_questions where questionID = '"+qid+"'")
            cur3.execute("SELECT url from astarcompo_pictorial where questionID = '"+qid+"'")
     
            question = cur2.fetchone()
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Answer Submitted! </strong><br/>Your answer will be review soon</div>'
            content = content + '<h3>Question: </h3><br/> %s <br/><br/>' % (question[0])
            pic = cur3.fetchone()
            if cur3.rowcount!=0:
                content = content + '<img src=%s/%s/><br/><br/>' % ("/static/pictures", (pic[0]))
            #content = content + '<label>Model Answers: </label>'
            #for q in quesAndAns:
                #content = content + '<br/> %s <br/><a href=%s>View Analysis</a><br/><br/>' % (q[0].replace('\n','<br/>'), q[1])
            #cur2.close()    
            #cur3.close()
        
            c = question[1]
            t = question[2]
            th = question[3]
            
            cat = '<span class="label label-default">%s</span>' % (question[1])
            ty = '<span class="label label-primary">%s</span>' % (question[2])
            theme = '<span class="label label-primary">%s</span>' % (question[3])
       
               
            cur2.close()    
            cur3.close()
            
            cur4 = connection.cursor()
            cur4.execute("SELECT a.ans from astarcompo_questions q, astarcompo_model_ans a where q.questionID = '"+qid+"' and q.questionID = a.questionID")
            templates = cur4.fetchone()
            cur4.close()
    
            vps = commonPhrasesVocabs(templates[0].replace('\n',' '))
            vpss = ""
            prevlist = []
            for vp in vps:
                if vp:
                    if re.match(r'\A[\w-]+\Z', vp):
                        word = '<a href="javascript:window.open(\'/dictionary/?word=%s\', \'_blank\', \'toolbar=no, scrollbars=no, resizable=no, width=400, height=400\');">%s</a>' %(vp, vp)
                        vpss = vpss + word + "<br/>"  
                    else:
                        vpss = vpss + '<a href="https://www.google.com.sg/#q=%s" target="_blank">' %(vp) + vp + "</a><br/>" 
                        prevlist.append(vp)  
    
            #get related phrase use for theme
     
            if th:
                cur5 = connection.cursor()
                cur5.execute("SELECT phrase FROM astarcompo_phrases WHERE theme = '%s'" %(th))
                phrases = cur5.fetchall()
                for phrase in phrases:
                    for prev in prevlist:
                        if phrase[0] != prev:
                            vpss = vpss + '<a href="https://www.google.com.sg/#q=%s" target="_blank">' %(phrase[0]) + phrase[0] + "</a><br/>"
                            break  

                cur5.close()    
    
            if t =='Continuous':
                return render(request, 'try.html', {'answer': qa, 'continuous': 'yes', 'vp': vpss, 'con': 'con', 'content': content, 'qid': qid, 'cat': cat, 'type': ty, 'theme': theme, 'user': username, 'superuser': superuser, 'th': th  }, context_instance=RequestContext(request))
            else:
       
                points = re.findall('- (.*)', q)
                pf = ""
                if len(points)>0:
                    pf = "<ul>"
                    for point in points:
                        pf = pf + "<li>" + point + "<input type=\"checkbox\"> </li>"
                    pf = pf + "</ul>"
        
                cur6 = connection.cursor()
                cur6.execute("SELECT template FROM astarcompo_situationalTemplates WHERE category = '%s'" %(c))
                tem = cur6.fetchone()
                cur6.close()
        
            return render(request, 'try.html', {'answer': qa, 'continuous': 'yes', 'vp': vpss, 'con': 'con', 'content': content, 'qid': qid, 'cat': cat, 'type': ty, 'theme': theme, 'user': username, 'superuser': superuser, 'th': th  }, context_instance=RequestContext(request))
        
            #return render(request, 'try.html', {'qid': qid, 'content': content, 'user': username, 'superuser': superuser}, context_instance=RequestContext(request))
        
        else:
            cur2 = connection.cursor()
            cur3 = connection.cursor()
            #cur.execute("SELECT a.ans, a.ansID from astarcompo_questions q, astarcompo_model_ans a where q.questionID = '"+qid+"' and q.questionID = a.questionID")
            cur2.execute("SELECT question, questionCategory, questionType, theme from astarcompo_questions where questionID = '"+qid+"'")
            cur3.execute("SELECT url from astarcompo_pictorial where questionID = '"+qid+"'")
     
            question = cur2.fetchone()
            content = '<h3>Question: </h3><br/> %s <br/><br/>' % (question[0])
            pic = cur3.fetchone()
            if cur3.rowcount!=0:
                content = content + '<img src=%s/%s/><br/><br/>' % ('/static/pictures', (pic[0]))
          
            #cur2.close()    
            #cur3.close()
            c = question[1]
            t = question[2]
            th = question[3]
            
            cat = '<span class="label label-default">%s</span>' % (question[1])
            ty = '<span class="label label-primary">%s</span>' % (question[2])
            theme = '<span class="label label-primary">%s</span>' % (question[3])
  
               
            cur2.close()    
            cur3.close()
            
            cur4 = connection.cursor()
            cur4.execute("SELECT a.ans from astarcompo_questions q, astarcompo_model_ans a where q.questionID = '"+qid+"' and q.questionID = a.questionID")
            templates = cur4.fetchone()
            cur4.close()
    
            vps = commonPhrasesVocabs(templates[0].replace('\n',' '))
            vpss = ""
            prevlist = []
            for vp in vps:
                if vp:
                    if re.match(r'\A[\w-]+\Z', vp):
                        word = '<a href="javascript:window.open(\'/dictionary/?word=%s\', \'_blank\', \'toolbar=no, scrollbars=no, resizable=no, width=400, height=400\');">%s</a>' %(vp, vp)
                        vpss = vpss + word + "<br/>"  
                    else:
                        vpss = vpss + '<a href="https://www.google.com.sg/#q=%s" target="_blank">' %(vp) + vp + "</a><br/>" 
                        prevlist.append(vp)  
    
            #get related phrase use for theme
     
            if th:
                cur5 = connection.cursor()
                cur5.execute("SELECT phrase FROM astarcompo_phrases WHERE theme = '%s'" %(th))
                phrases = cur5.fetchall()
                for phrase in phrases:
                    for prev in prevlist:
                        if phrase[0] != prev:
                            vpss = vpss + '<a href="https://www.google.com.sg/#q=%s" target="_blank">' %(phrase[0]) + phrase[0] + "</a><br/>"
                            break  

                cur5.close()    
    
            if t =='Continuous':
                print content
                return render(request, 'try.html', {'answer': qa, 'errors': errors, 'continuous': 'yes', 'vp': vpss, 'con': 'con', 'content': content, 'qid': qid, 'cat': cat, 'type': ty, 'theme': theme, 'user': username, 'superuser': superuser, 'th': th  }, context_instance=RequestContext(request))
            else:
       
                points = re.findall('- (.*)', q)
                pf = ""
                if len(points)>0:
                    pf = "<ul>"
                    for point in points:
                        pf = pf + "<li>" + point + "<input type=\"checkbox\"> </li>"
                    pf = pf + "</ul>"
        
                cur6 = connection.cursor()
                cur6.execute("SELECT template FROM astarcompo_situationalTemplates WHERE category = '%s'" %(c))
                tem = cur6.fetchone()
                cur6.close()
                
                return render(request, 'try.html', {'answer': qa, 'errors': errors, 'continuous': '', 'vp': vpss, 'con': 'con', 'content': content, 'qid': qid, 'cat': cat, 'type': ty, 'theme': theme, 'user': username, 'superuser': superuser, 'th': th  }, context_instance=RequestContext(request))
            
            #return render(request, 'try.html', {'errors': errors, 'qid': qid, 'content': content, 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))
    return HttpResponseRedirect('/404/')    
    

#Get Question Type from Question Category 
def getCatandType(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path}, context_instance=RequestContext(request))
    ty = request.GET.get('type', '')  
    superuser = request.session["superuser"];
    username = request.session["username"]
    catcontent = '<span id="c"><select class="form-control" name="cat" id="cat">'
             
    cur = connection.cursor()
    cur.execute("SELECT DISTINCT questionCategory from astarcompo_questions where questionType='%s'" % (ty))
    cats = cur.fetchall()
    if cur.rowcount==0:
        return render(request, '404.html', {}, context_instance=RequestContext(request))
    for cat in cats:
        catcontent = catcontent + '<option value="%s">%s</option>' % (cat[0], cat[0])
    catcontent = catcontent + '<option value="Others">Others</option></select></span>'
    cur.close() 
    typecontent = '<input type="text" value=%s class="form-control" name="type" readonly=true/>' %(ty.title()) 
    
    
    if ty.title() == "Continuous":
        #theme
        cur = connection.cursor()
        cur.execute("SELECT theme from astarcompo_themes")
        themes = cur.fetchall()
        cur.close()
    
        themeddl = '''
        <div class="form-group">
         <label for="theme" class="col-lg-2 control-label">Theme</label>
         <div class="col-lg-10">
           <select class="form-control" name="theme" id="theme">
        '''
   
        for theme in themes:
            if theme[0]==theme:
                themeddl = themeddl + '<option value="%s" selected>%s</option>' % (theme[0], theme[0])
            else:
                themeddl = themeddl + '<option value="%s">%s</option>' % (theme[0], theme[0])
        themeddl = themeddl + '</select></div></div>'
        
    
        return render(request, 'add_question.html', {'cat': catcontent, 'type': typecontent, 'themes': themeddl, 'user': username, 'superuser': superuser}, context_instance=RequestContext(request))
    else:
        sit =   '''
                <div class="form-group" id="sittem">
			         
			    </div>
                
                '''
        return render(request, 'add_question.html', {'cat': catcontent, 'sit': sit, 'type': typecontent, 'user': username, 'superuser': superuser}, context_instance=RequestContext(request))
        

#Practice Question Modules

#Request to the try the question specifying the Question ID
def tryexcercise(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    superuser = request.session["superuser"];
    username = request.session["username"]
    qid = request.GET.get('id', '')     
    #cur = connection.cursor()
    cur2 = connection.cursor()
    cur3 = connection.cursor()
    #cur.execute("SELECT a.ans, a.ansID from astarcompo_questions q, astarcompo_model_ans a where q.questionID = '"+qid+"' and q.questionID = a.questionID")
    cur2.execute("SELECT question, questionCategory, questionType, theme from astarcompo_questions where questionID = '"+qid+"'")
    cur3.execute("SELECT url from astarcompo_pictorial where questionID = '"+qid+"'")
    #quesAndAns = cur.fetchall()
    #cur.close()
    content = ""
    q = ""
    th=""
    c=""
    if cur2.rowcount == 0:
        content = "<h1>The Question does not exist!</h1>"
        t = get_template('try.html')
        c = Context({'content': content, 'user': username, 'superuser': superuser  })
        html = t.render(c)
        return HttpResponse(html)
    else:
        question = cur2.fetchone()
        t = question[2]
        c = question[1]
        cat = '<span class="label label-default">%s</span>' % (question[1])
        ty = '<span class="label label-primary">%s</span>' % (question[2])
        theme = ""
        if question[2] == "Continuous":
            theme = '<span class="label label-primary">%s</span>' % (question[3])
        content = '<h3>Question: </h3><br/> <p class="text-success">%s</p> <br/><br/>' % (question[0].replace('\n','<br/>'))
        q = question[0];
        th = question[3]

        pic = cur3.fetchone()
        if cur3.rowcount!=0:
            content = content + '<div class="panel panel-default"><div class="panel-body"><img src=%s/%s class="img-responsive"/></div></div>' % ("/static/pictures", (pic[0]))
        #content = content + '<label>Model Answers: </label>'
        #for q in quesAndAns:
            #content = content + '<br/> %s <br/><a href=%s>View Analysis</a><br/><br/>' % (q[0].replace('\n','<br/>'), q[1])
    cur2.close()    
    cur3.close()
    
    cur4 = connection.cursor()
    cur4.execute("SELECT a.ans from astarcompo_questions q, astarcompo_model_ans a where q.questionID = '"+qid+"' and q.questionID = a.questionID")
    templates = cur4.fetchone()
    cur4.close()
    
    vps = commonPhrasesVocabs(templates[0].replace('\n',' '))
    vpss = ""
    prevlist = []
    for vp in vps:
        if vp:
            if re.match(r'\A[\w-]+\Z', vp):
                word = '<a href="#dict" data-toggle="modal" data-load-remote="/dictionary/?word=%s" data-remote-target="#dict .modal-body">%s</a>' %(vp, vp)
                #word = '<a href="javascript:window.open(\'/dictionary/?word=%s\', \'_blank\', \'toolbar=no, scrollbars=no, resizable=no, width=400, height=400\');">%s</a>' %(vp, vp)
                vpss = vpss + word + "<br/>"  
            else:
                vpss = vpss + '<a href="https://www.google.com.sg/#q=%s" target="_blank">' %(vp) + vp + "</a><br/>" 
                prevlist.append(vp)  
    
    #get related phrase use for theme
     
    if th:
        cur5 = connection.cursor()
        cur5.execute("SELECT phrase FROM astarcompo_phrases WHERE theme = '%s'" %(th))
        phrases = cur5.fetchall()
        for phrase in phrases:
            for prev in prevlist:
                if phrase[0] != prev:
                    vpss = vpss + '<a href="https://www.google.com.sg/#q=%s" target="_blank">' %(phrase[0]) + phrase[0] + "</a><br/>"
                    break  

        cur5.close()    
    
    if t =='Continuous':
        th = th.replace(" ", "%20")
        return render(request, 'try.html', {'continuous': 'yes', 'vp': vpss, 'con': 'con', 'content': content, 'qid': qid, 'cat': cat, 'type': ty, 'theme': theme, 'user': username, 'superuser': superuser, 'th': th  }, context_instance=RequestContext(request))
    else:
       
        points = re.findall('- (.*)', q)
        pf = ""
        if len(points)>0:
            pf = "<ul>"
            for point in points:
                pf = pf + "<li>" + point + "<input type=\"checkbox\"> </li>"
            pf = pf + "</ul>"
        
        cur6 = connection.cursor()
        cur6.execute("SELECT template FROM astarcompo_situationalTemplates WHERE category = '%s'" %(c))
        tem = cur6.fetchone()
        cur6.close()
      
        return render(request, 'try.html', {'continuous': '', 'points': pf, 'template': tem[0], 'vp': vpss, 'con': 'con', 'content': content, 'qid': qid, 'cat': cat, 'type': ty, 'theme': theme, 'user': username, 'superuser': superuser, 'th': th  }, context_instance=RequestContext(request))
        
    return HttpResponse(html)

#Theme Management Modules

#Get all themes
def getThemes(request):
    
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    superuser = request.session["superuser"];
    username = request.session["username"]  
    cur = connection.cursor()
    cur.execute("SELECT themeID, theme from astarcompo_themes")
   
    content = ""
    if cur.rowcount == 0:
        content = "<p>No Themes</p>"
        return render(request, 'themes.html', {'content': content, 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
 
    else:
        themes = cur.fetchall()
        content = "<table id=\"themetable\"class=\"table table-striped table-hover\"><thead><tr><th>Theme</th><th>&nbsp;</th><th>&nbsp;</th></tr></thead><tbody>"
        for theme in themes:
            
            cur.execute("SELECT COUNT(*) FROM astarcompo_questions WHERE theme='%s'" %(theme[1]))
            norows = cur.fetchone()
            if norows[0] == 0:
                content = content + "<tr><td>%s</td><td><button type=\"button\" onclick=\"window.location='/theme/?theme=%s'\" class=\"btn btn-primary btn-xs\">Edit</button></td><td><button type=\"button\" onclick=\"window.location='/confirmDelete/?dtype=theme&themeID=%s'\" class=\"btn btn-primary btn-xs\">Delete</button></td></tr>" %(theme[1], theme[1], theme[0])
            else :
                content = content + "<tr><td>%s</td><td><button type=\"button\" onclick=\"window.location='/theme/?theme=%s'\" class=\"btn btn-primary btn-xs\">Edit</button></td><td><button type=\"button\" onclick=\"window.location='/confirmDelete/?dtype=theme&themeID=%s'\" class=\"btn btn-primary btn-xs\" disabled>Delete</button></td></tr>" %(theme[1], theme[1], theme[0])
                
        content = content +   "</tbody></table>" 
        return render(request, 'themes.html', {'content': content, 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
    cur.close()
 
#Request theme page 
def themePage(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    
    superuser = request.session["superuser"];
    username = request.session["username"]
    theme = request.GET.get('theme', '')   
    
    #check if there is parameter 'theme'
    if theme:
        cur = connection.cursor()
        cur.execute("SELECT templateID, template, templateType from astarcompo_templates WHERE theme = '"+theme+"'")
        cur1 = connection.cursor()
        cur1.execute("SELECT themeID from astarcompo_themes WHERE theme = '"+theme+"'")
        themes = cur1.fetchone()
        
        if not themes:
            return render(request, '404.html', {}, context_instance=RequestContext(request))
        
        content = ""
        if cur.rowcount == 0:
            content = "<p>List of Templates:</p><p>No Templates found!</p>"
            return render(request, 'create_theme.html', {'cu': "/editTheme/", 'content': content, 'edit': "true", 'theme': theme, 'tid': themes[0], 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))
        else:
            templates = cur.fetchall()
            content = "<p>List of Templates:</p><table id=\"templatetable\" class=\"table table-striped table-hover\"><thead><tr><th>Template</th><th>Template Type</th><th>&nbsp;</th><th>&nbsp;</th></tr></thead><tbody>"
            for template in templates:
                content = content + "<tr><td>%s</td><td>%s</td><td><button type=\"button\" onclick=\"window.location='/template/?template=%s'\" class=\"btn btn-primary btn-xs\">Edit</button></td><td><button type=\"button\" onclick=\"window.location='/confirmDelete/?dtype=template&template=%s&theme=%s'\" class=\"btn btn-primary btn-xs\">Delete</button></td></tr>" %(template[1], template[2], template[0], template[0], theme)
            
            content = content +   "</tbody></table>" 
            return render(request, 'create_theme.html', {'cu': "/editTheme/", 'content': content, 'edit': "true", 'theme': theme, 'tid': themes[0], 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))
            
    #else: create new theme page
    else:
        return render(request, 'create_theme.html', {'cu': "/createTheme/", 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))
    cur1.close()
    cur.close()
    
#Insert theme into database
def createTheme(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    errors = []
    if request.method == 'POST':
        superuser = request.session["superuser"];
        username = request.session["username"]
        
        if not request.POST.get('theme', ''):
           errors.append('Theme cannot empty.')
        
        theme = request.POST.get('theme', '')
        
        #check if theme exists
        cur = connection.cursor()
        cur.execute("SELECT COUNT(*) from astarcompo_themes WHERE theme='%s'" %(theme))
        row = cur.fetchone()
        cur.close()

        if row[0] == 1:
            errors.append('Theme already exists.')
        
        if not errors:   
            cur1 = connection.cursor()
            cur1.execute("SET autocommit=1")
            cur1.execute("INSERT INTO astarcompo_themes(theme) VALUES('%s')" %(theme))
            cur1.close()
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Theme Created! </strong></div>'
            return render(request, 'create_theme.html', {'success': content, 'theme': theme, 'user': username, 'superuser': superuser}, context_instance=RequestContext(request))
       
        else:
            return render(request, 'create_theme.html', {'errors': errors, 'theme': theme, 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))
    
        cur.close()
    return render(request, '404.html', {}, context_instance=RequestContext(request))
       
    
#Update theme in database
def editTheme(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    errors = []
    if request.method == 'POST':
        
        themeID = request.POST.get('tid', '')
        theme = request.POST.get('theme', '')
        superuser = request.session["superuser"];
        username = request.session["username"]
    
        if not request.POST.get('theme', ''):
           errors.append('Theme cannot be empty.')
        
        #check if theme exists
        cur = connection.cursor()
        cur.execute("SELECT COUNT(*) from astarcompo_themes WHERE theme='%s'" %(theme))
        row = cur.fetchone()
        cur.close()

        if row[0] == 1:
            errors.append('Theme already exists.')

        if not errors:
            template = request.POST.get('theme', '')
            cur = connection.cursor()
            cur.execute("SET autocommit=1")
            #Get the theme before update to update those in the templates
            cur1 = connection.cursor()
            cur1.execute("SELECT theme FROM astarcompo_themes WHERE themeID='%s'" % (themeID))
            oldtheme = cur1.fetchone()
            cur1.close()
            cur.execute("UPDATE astarcompo_themes SET theme='%s' WHERE themeID='%s'" % (theme, themeID))
            cur.execute("UPDATE astarcompo_templates SET theme='%s' WHERE theme='%s'" % (theme, oldtheme[0]))
            cur.execute("UPDATE astarcompo_questions SET theme='%s' WHERE theme='%s'" % (theme, oldtheme[0]))
            cur.close()
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Theme Updated! </strong></div>'
            return render(request, 'create_theme.html', {'tid': themeID, 'theme': theme, 'success': content, 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))
        else:
            return render(request, 'create_theme.html', {'tid': themeID, 'theme': theme, 'errors': errors, 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))
    
    return render(request, '404.html', {}, context_instance=RequestContext(request))

#Delete theme from database
def deleteTheme(request):
    superuser = request.session.get('superuser')
    if superuser:
        themeID = request.GET.get('id', '')
        cur = connection.cursor()
        cur.execute("SELECT theme FROM astarcompo_themes WHERE themeID='%s'"% (themeID))
        theme = cur.fetchone()      
        cur.execute("SET autocommit=1")
        cur.execute("DELETE FROM astarcompo_themes WHERE themeID='%s'"% (themeID))
        
        cur.execute("DELETE FROM astarcompo_templates WHERE theme='%s'"% (theme[0]))
        cur.close()
        return HttpResponseRedirect('/themes/')
    return render(request, '404.html', {'user': ''}, context_instance=RequestContext(request))  
    

#Template Managemwent Module

#Request Template Page
def templatePage(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    
    superuser = request.session["superuser"];
    username = request.session["username"]
    template = request.GET.get('template', '') 
    theme = request.GET.get('theme', '')  
    
    #check if there is parameter 'template'
    if template:
        cur = connection.cursor()
        cur.execute("SELECT templateID, template, templateType, theme from astarcompo_templates WHERE templateID = '"+template+"'")
        templates = cur.fetchone()
        
        if not templates:
            return render(request, '404.html', {}, context_instance=RequestContext(request))

        return render(request, 'template.html', {'cu': "/editTemplate/", 'tid': templates[0], 'template': templates[1], 'templateType': templates[2], 'theme': templates[3], 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))    
    
    #else: create new theme page
    else:
        return render(request, 'template.html', {'cu': "/createTemplate/", 'user': username, 'theme': theme, 'superuser': superuser }, context_instance=RequestContext(request))
    cur.close()
    
#Insert template into database
def createTemplate(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    errors = []
    if request.method == 'POST':
        superuser = request.session["superuser"];
        username = request.session["username"] 
        theme = template = request.POST.get('theme', '')
        if not request.POST.get('template', ''):
           errors.append('Template is empty.')
           
        template = request.POST.get('template', '')
        templateType = request.POST.get('templateType', '')   
        
        if not errors:
            cur = connection.cursor()
            cur.execute("SET autocommit=1")
            cur.execute("INSERT INTO astarcompo_templates(template, templateType, theme) VALUES(%s, %s, %s)", (template, templateType, theme))
            cur.close()
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Template Created! </strong></div>'
            return render(request, 'template.html', {'success': content, 'template': template, 'templateType': templateType, 'theme': theme, 'user': username, 'superuser': superuser}, context_instance=RequestContext(request))
        else:
            return render(request, 'template.html', {'errors': errors, 'template': template, 'templateType': templateType, 'theme': theme, 'user': username, 'superuser': superuser}, context_instance=RequestContext(request))
            
    return render(request, '404.html', {}, context_instance=RequestContext(request))

#Update template in database
def editTemplate(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    errors = []
    if request.method == 'POST':
           
        templateID = request.POST.get('tid', '')
        templateType = request.POST.get('templateType', '')
        superuser = request.session["superuser"];
        username = request.session["username"]
    
        if not request.POST.get('template', ''):
           errors.append('Template cannnot be empty.')

        if not errors:
            template = request.POST.get('template', '')
            cur = connection.cursor()
            cur.execute("SET autocommit=1")
            cur.execute("UPDATE astarcompo_templates SET template='%s', templateType='%s' WHERE templateID='%s'" % (template, templateType, templateID))
            cur.close()
            cur1 = connection.cursor()
            cur1.execute("SELECT theme FROM astarcompo_templates WHERE templateID='%s'" % (templateID))
            theme = cur1.fetchone()
            cur1.close()
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Template Updated! </strong></div>'

            return render(request, 'template.html', {'tid': templateID, 'template': template, 'theme': theme[0], 'success': content, 'templateType': templateType, 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))

        else:
            return render(request, 'template.html', {'tid': templateID, 'template': template, 'errors': errors, 'templateType': templateType, 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))
    return render(request, '404.html', {}, context_instance=RequestContext(request))

#Delete Temeplate from database
def deleteTemplate(request):
    superuser = request.session.get('superuser')
    if superuser:
        tid = request.GET.get('template', '')
        theme = request.GET.get('theme', '')
        cur = connection.cursor()
        cur.execute("SET autocommit=1")
        cur.execute("DELETE FROM astarcompo_templates WHERE templateID='%s'"% (tid))
        cur.close()
        return HttpResponseRedirect('/theme/?theme=%s'%(theme))
    
    return render(request, '404.html', {'user': ''}, context_instance=RequestContext(request))

#Insert Introduction
def introduction(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    theme = request.GET.get('theme', '')
   
    content = ''
    
    cur = connection.cursor()
    cur.execute("SELECT template FROM astarcompo_templates WHERE templateType='Introduction' AND theme='%s'" %(theme))
    intros = cur.fetchall()
    counter = 1
    for intro in intros:
        content = content +  '<div class="panel panel-default"><div class="panel-heading">Introduction %s</div><div class="panel-body">' % (counter) + intro[0] + "</div></div>"
        counter = counter + 1
      

    return render(request, 'introduction.html', {'content': content}, context_instance=RequestContext(request))
    
#Insert Main Body
def mb(request):
     if not request.user.is_authenticated():
         return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
     theme = request.GET.get('theme', '')
     content = ''
     
     cur = connection.cursor()
     cur.execute("SELECT template FROM astarcompo_templates WHERE templateType='Main Body' AND theme='%s'" % (theme))
     mbs = cur.fetchall()
     counter = 1
     for mb in mbs:
         content = content +  '<div class="panel panel-default"><div class="panel-heading">Plot %s</div><div class="panel-body">' % (counter) + (mb[0].replace('\n','<br/>')) + "</div></div>"
         counter = counter + 1
       
     return render(request, 'mb.html', {'content': content}, context_instance=RequestContext(request))
    
#Insert Conclusion
def conclusion(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    theme = request.GET.get('theme', '')
    content = ''
    
    cur = connection.cursor()
    cur.execute("SELECT template FROM astarcompo_templates WHERE templateType='Conclusion' AND theme='%s'" %(theme))
    cons = cur.fetchall()
    counter = 1
    for con in cons:
        content = content +  '<div class="panel panel-default"><div class="panel-heading">Conclusion %s</div><div class="panel-body">' % (counter) + con[0] + "</div></div>"
        counter = counter + 1
    return render(request, 'conclusion.html', {'content': content }, context_instance=RequestContext(request))
    

#Help Modules
        
#Vocabulary/Phrase Management   

def getVPlist(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    superuser = request.session["superuser"];
    username = request.session["username"]  
    cur = connection.cursor()
    cur.execute("SELECT phrase, category, theme from astarcompo_phrases")
    
    cur1 = connection.cursor()
    cur1.execute("SELECT vocabulary, category, theme from astarcompo_vocabularies")
   
    content = ""
    if cur.rowcount == 0 or cur1.rowcount ==0 :
        content = "<p>No Vocabulary or Phrase</p>"
        return render(request, 'vplist.html', {'content': content, 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
 
    else:
        vs = cur1.fetchall()
        ps = cur.fetchall()
        content = "<table id=\"vptable\" class=\"table table-striped table-hover\"><thead><tr><th>Vocabulary/Phrase</th><th>Category</th><th>Vocabulary or Phrase?</th><th>Theme</th><th>&nbsp;</th><th>&nbsp;</th></tr></thead><tbody>"
        for v in vs:
            content = content + "<tr><td>%s</td><td>%s</td><td>Vocabulary</td><td>%s</td><td><button type=\"button\" onclick=\"window.location='/vpPage/?vp=%s&type=Vocabulary'\" class=\"btn btn-primary btn-xs\">Edit</button></td><td><button type=\"button\" onclick=\"window.location='/confirmDelete/?dtype=vp&vp=%s&type=Vocabulary'\" class=\"btn btn-primary btn-xs\">Delete</button></td></tr>" %(v[0], v[1], v[2], v[0], v[0])
        for p in ps:
            content = content + "<tr><td>%s</td><td>%s</td><td>Phrase</td><td>%s</td><td><button type=\"button\" onclick=\"window.location='/vpPage/?vp=%s&type=Phrase&theme'\" class=\"btn btn-primary btn-xs\">Edit</button></td><td><button type=\"button\" onclick=\"window.location='/confirmDelete/?dtype=vp&vp=%s&type=Phrase'\" class=\"btn btn-primary btn-xs\">Delete</button></td></tr>" %(p[0], p[1], p[2], p[0], p[0])
        
        content = content +   "</tbody></table>" 
        
        return render(request, 'vplist.html', {'content': content, 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
    cur.close()
    cur1.close()
    
 
#Request Vocabulary/Phrase Page
def VPpage(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next': request.path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    
    vp = request.GET.get('vp', '')
    ty = request.GET.get('type', '')
        
    superuser = request.session["superuser"]
    theme = ""
    cat = ""
    cr = connection.cursor()
    
    
    if(ty=="Vocabulary"):
        cr.execute("SELECT category, theme FROM astarcompo_vocabularies WHERE vocabulary='%s'" %(vp))
        v = cr.fetchone()
        if not v:
            return render(request, '404.html', {}, context_instance=RequestContext(request))
        cat = v[0]
        theme = v[1]
    elif (ty=="Phrase"):
        cr.execute("SELECT category, theme FROM astarcompo_phrases WHERE phrase='%s'" %(vp))
        p = cr.fetchone()
        if not p:
            return render(request, '404.html', {}, context_instance=RequestContext(request))
        cat = p[0]
        theme = p[1]
        
    cr.close() 
    
    
    if vp: 
        catlst = '''
        <div class="form-group">
            <label for="select" class="col-lg-2 control-label">Category</label>
            <div class="col-lg-12">
              <select class="form-control" name="cat">  
        '''
        cur = connection.cursor()
        cur.execute("SELECT category FROM astarcompo_vpcat")
        cats = cur.fetchall()
 
        for ct in cats:
            if ct[0]==cat:
                catlst = catlst + '<option value="%s" selected>' %(ct[0]) + ct[0] + '</option>'
            else:
                catlst = catlst + '<option value="%s">' %(ct[0]) + ct[0] + '</option>'
        
        catlst = catlst + "</select></div></div>"
        
        typelst= '<input type="text" class="form-control" id="type" readonly="true" name="type" value="%s">' %(ty) 
        
        '''
        typelst = """
        <div class="form-group">
            <label for="select" class="col-lg-2 control-label">Type</label>
            <div class="col-lg-12">
              <select class="form-control" name="type">  
        """
  
        if ty=="Phrase":
            typelst = typelst + '<option value="Phrase" selected>Phrase</option><option value="Vocabulary">Vocabulary</option>'
        elif ty=="Vocabulary":
            typelst = typelst + '<option value="Phrase">Phrase</option><option value="Vocabulary" selected>Vocabulary</option>'
        
        typelst = typelst + "</select></div></div>"

        '''
        themelst = '''
        <div class="form-group">
            <label for="select" class="col-lg-2 control-label">Theme</label>
            <div class="col-lg-12">
              <select class="form-control" name="theme">  
        '''

        cur.execute("SELECT theme FROM astarcompo_themes")
        themes = cur.fetchall()
        for th in themes:
            if th[0]==theme:
                themelst = themelst + '<option value="%s" selected>' %(theme) + theme + '</option>'
            else:
                themelst = themelst + '<option value="%s">' %(th[0]) + th[0] + '</option>'
        
        if theme:
            themelst = themelst + '<option value=""></option></select></div></div>'
        else:
            themelst = themelst + '<option value="" selected></option></select></div></div>'
         
        cur.close()
          
        return render(request, 'create_vp.html', {'cu': '/editVP/', 'catlst': catlst, 'typelst': typelst, 'themelst': themelst, 'vp': vp, 'superuser': superuser}, context_instance=RequestContext(request))
    
    else:
        catlst = '''
        <div class="form-group">
            <label for="select" class="col-lg-2 control-label">Category</label>
            <div class="col-lg-12">
              <select class="form-control" name="cat">  
        '''
        cur = connection.cursor()
        cur.execute("SELECT category FROM astarcompo_vpcat")
        cats = cur.fetchall()
        for ct in cats:
            catlst = catlst + '<option value="%s">' %(ct[0]) + ct[0] + '</option>'
        catlst = catlst + "</select></div></div>"
     
        typelst = '''
        <div class="form-group">
            <label for="select" class="col-lg-2 control-label">Type</label>
            <div class="col-lg-12">
              <select class="form-control" name="type">  
              <option value="Phrase">Phrase</option><option value="Vocabulary">Vocabulary</option>'
        '''
        typelst = typelst + "</select></div></div>"
        
        themelst = '''
        <div class="form-group">
            <label for="select" class="col-lg-2 control-label">Theme</label>
            <div class="col-lg-12">
              <select class="form-control" name="theme">  
        '''
    
        cur.execute("SELECT theme FROM astarcompo_themes")
        themes = cur.fetchall()
        for th in themes:
            themelst = themelst + '<option value="%s">' %(th[0]) + th[0] + '</option>'
        themelst = themelst + '<option value=""></option></select></div></div>'
        cur.close()
        
        print themelst
        
        return render(request, 'create_vp.html', {'cu': '/createVP/', 'catlst': catlst, 'typelst': typelst, 'themelst': themelst, 'superuser': superuser}, context_instance=RequestContext(request))
 

#Insert Vocabulary into database
def createVP(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next': request.path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    errors = []
    if request.method == 'POST':
        superuser = request.session["superuser"];
        username = request.session["username"]
        
        vp = request.POST.get('vp', '')
        ty = request.POST.get('type', '')
        cat = request.POST.get('cat', '')
        theme = request.POST.get('theme', '')
          
        row=""
        
        if not request.POST.get('vp', ''):
            errors.append('Vocabulary/Phrase cannot empty.')
            
        
        #check if vp exists
        if ty == "Phrase":
            cr1 = connection.cursor()
            cr1.execute("SELECT COUNT(*) FROM astarcompo_phrases WHERE phrase='%s'" %(vp))
            row = cr1.fetchone()
            cr1.close()
        
        elif ty == "Vocabulary":
            cr2 = connection.cursor()
            cr2.execute("SELECT COUNT(*) FROM astarcompo_vocabularies WHERE vocabulary='%s'" %(vp))
            row = cr2.fetchone()
            cr2.close()
        
        if row[0] == 1:
          errors.append('Vocabulary/Phrase already exists.') 
      
  
        if not errors: 
            cur = connection.cursor()
            cur.execute("SET autocommit=1")
            if ty == "Phrase":
                cur.execute("INSERT INTO astarcompo_phrases(phrase, category, theme) VALUES('%s', '%s', '%s')" % (vp, cat, theme))
            elif ty == "Vocabulary":
                cur.execute("INSERT INTO astarcompo_vocabularies(vocabulary, category, theme) VALUES('%s', '%s', '%s')" % (vp, cat, theme))
            
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Phrase/Vocabulary Created! </strong></div>'
            
            catlst = '''
            <div class="form-group">
                <label for="select" class="col-lg-2 control-label">Category</label>
                <div class="col-lg-12">
                  <select class="form-control" name="cat">  
            '''
           
            cur.execute("SELECT category FROM astarcompo_vpcat")
            cats = cur.fetchall()
            for ct in cats:
                if ct[0]==cat:
                    catlst = catlst + '<option value="%s" selected>' %(ct[0]) + ct[0] + '</option>'
                else:
                    catlst = catlst + '<option value="%s">' %(ct[0]) + ct[0] + '</option>'
            catlst = catlst + "</select></div></div>"
            
            
            typelst = '''
            <div class="form-group">
                <label for="select" class="col-lg-2 control-label">Type</label>
                <div class="col-lg-12">
                  <select class="form-control" name="type">  
            '''
      
            if ty=="Phrase":
                typelst = typelst + '<option value="Phrase" selected>Phrase</option><option value="Vocabulary">Vocabulary</option>'
            elif ty=="Vocabulary":
                typelst = typelst + '<option value="Phrase">Phrase</option><option value="Vocabulary" selected>Vocabulary</option>'
            
            typelst = typelst + "</select></div></div>"
            
            
            themelst = '''
            <div class="form-group">
                <label for="select" class="col-lg-2 control-label">Theme</label>
                <div class="col-lg-12">
                  <select class="form-control" name="theme">  
            '''
      
            cur.execute("SELECT theme FROM astarcompo_themes")
            themes = cur.fetchall()
            for th in themes:
                if th[0]==theme:
                    themelst = themelst + "<option value=%s selected>" %(theme) + theme + "</option>"   
                else:
                    themelst = themelst + "<option value=%s>" %(th[0]) + th[0] + "</option>"
            
            if theme:
                themelst = themelst + '<option value=""></option></select></div></div>'
            else:
                themelst = themelst + '<option value="" selected></option></select></div></div>'
            cur.close()
    
            return render(request, 'create_vp.html', {'success': content, 'catlst': catlst, 'typelst': typelst, 'themelst': themelst, 'vp': vp, 'user': username, 'superuser': superuser}, context_instance=RequestContext(request))
       
        else:
            
            catlst = '''
            <div class="form-group">
                <label for="select" class="col-lg-2 control-label">Category</label>
                <div class="col-lg-12">
                  <select class="form-control" name="cat">  
            '''
            cur = connection.cursor()
            cur.execute("SELECT category FROM astarcompo_vpcat")
            cats = cur.fetchall()
            for ct in cats:
                if ct[0]==cat:
                    catlst = catlst + '<option value=%s selected>' %(ct[0]) + ct[0] + '</option>'
                else:
                    catlst = catlst + '<option value="%s">' %(ct[0]) + ct[0] + '</option>'
            catlst = catlst + "</select></div></div>"
            
            typelst = '''
            <div class="form-group">
                <label for="select" class="col-lg-2 control-label">Type</label>
                <div class="col-lg-12">
                  <select class="form-control" name="type">  
            '''
      
            if ty=="Phrase":
                typelst = typelst + '<option value="Phrase" selected>Phrase</option><option value="Vocabulary">Vocabulary</option>'
            elif ty=="Vocabulary":
                typelst = typelst + '<option value="Phrase">Phrase</option><option value="Vocabulary" selected>Vocabulary</option>'
            
            typelst = typelst + "</select></div></div>"
            
            
            themelst = '''
            <div class="form-group">
                <label for="select" class="col-lg-2 control-label">Theme</label>
                <div class="col-lg-12">
                  <select class="form-control" name="theme">  
            '''
            
            cur.execute("SELECT theme FROM astarcompo_themes")
            themes = cur.fetchall()
            for th in themes:
                if th[0]==theme:
                    themelst = themelst + '<option value="%s" selected>' %(theme) + theme + '</option>'
                else:
                    themelst = themelst + '<option value="%s">' %(th[0]) + th[0] + '</option>'
            
            if theme:
                themelst = themelst + '<option value=""></option></select></div></div>'
            else:
                themelst = themelst + '<option value="" selected></option></select></div></div>'
            cur.close()
            
            return render(request, 'create_vp.html', {'errors': errors, 'catlst': catlst, 'typelst': typelst, 'themelst': themelst, 'vp': vp, 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))
           
    return render(request, '404.html', {}, context_instance=RequestContext(request))

#Update Vocabulary in database
def editVP(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next': request.path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    errors = []
    if request.method == 'POST':
        superuser = request.session["superuser"];
        username = request.session["username"]
        
        vp = request.POST.get('vp', '')
        ty = request.POST.get('type', '')
        cat = request.POST.get('cat', '')
        theme  = request.POST.get('theme', '')
        oldvp = request.POST.get('oldvp', '') 
    
        row = ""
    
   
        if not request.POST.get('vp', ''):
            errors.append('Vocabulary/Phrase cannot empty.')
            
        #check if vp exists
  
        if ty == "Phrase":
            cr1 = connection.cursor()
            cr1.execute("SELECT COUNT(*) FROM astarcompo_phrases WHERE phrase='%s'" %(vp))
            row = cr1.fetchone()
            cr1.close()
        
        elif ty == "Vocabulary":

            cr2 = connection.cursor()
            cr2.execute("SELECT COUNT(*) FROM astarcompo_vocabularies WHERE vocabulary='%s'" % (vp))
            row = cr2.fetchone()
            cr2.close()
       
        if row[0] == 1 and oldvp != vp:
            errors.append('Vocabulary/Phrase already exists.') 

        
        if not errors:      
            cur = connection.cursor()
            cur.execute("SET autocommit=1")
            if ty == "Phrase":
                cur.execute("UPDATE astarcompo_phrases SET phrase='%s', category='%s', theme='%s' WHERE phrase='%s'" %(vp, cat, theme, oldvp))
            elif ty == "Vocabulary":
                cur.execute("UPDATE astarcompo_vocabularies SET vocabulary='%s', category='%s', theme='%s' WHERE vocabulary='%s'" %(vp, cat, theme, oldvp))
            
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Phrase/Vocabulary Updated !</strong></div>'
        
            
            catlst = '''
            <div class="form-group">
                <label for="select" class="col-lg-2 control-label">Category</label>
                <div class="col-lg-12">
                  <select class="form-control" name="cat">  
            '''

            cur.execute("SELECT category FROM astarcompo_vpcat")
            cats = cur.fetchall()
            for ct in cats:
                if ct[0]==cat:
                    catlst = catlst + '<option value="%s" selected>' %(ct[0]) + ct[0] + '</option>'
                else:
                    catlst = catlst + '<option value="%s">' %(ct[0]) + ct[0] + '</option>'
            catlst = catlst + "</select></div></div>"
            
            typelst= '<input type="text" class="form-control" id="type" readonly="true" name="type" value="%s">' %(ty) 
            
            '''
            typelst = """
            <div class="form-group">
                <label for="select" class="col-lg-2 control-label">Type</label>
                <div class="col-lg-12">
                  <select class="form-control" name="type">  
            """
      
            if ty=="Phrase":
                typelst = typelst + '<option value="Phrase" selected>Phrase</option><option value="Vocabulary">Vocabulary</option>'
            elif ty=="Vocabulary":
                typelst = typelst + '<option value="Phrase">Phrase</option><option value="Vocabulary" selected>Vocabulary</option>'
            
            typelst = typelst + "</select></div></div>"
            '''
    
            themelst = '''
            <div class="form-group">
                <label for="select" class="col-lg-2 control-label">Theme</label>
                <div class="col-lg-12">
                  <select class="form-control" name="theme">  
            '''
       
            cur.execute("SELECT theme FROM astarcompo_themes")
            themes = cur.fetchall()
            for th in themes:
                if th[0]==theme:
                    themelst = themelst + '<option value="%s" selected>' %(theme) + theme + '</option>'            
                else:
                    themelst = themelst + '<option value="%s">' %(th[0]) + th[0] + '</option>'
            
            if theme:
                themelst = themelst + '<option value=""></option></select></div></div>'
            else:
                themelst = themelst + '<option value="" selected></option></select></div></div>'
            
            cur.close()
            
            return render(request, 'create_vp.html', {'success': content, 'catlst': catlst, 'typelst': typelst, 'themelst': themelst, 'vp': vp, 'user': username, 'superuser': superuser}, context_instance=RequestContext(request))
       
        else:

            catlst = '''
            <div class="form-group">
                <label for="select" class="col-lg-2 control-label">Category</label>
                <div class="col-lg-12">
                  <select class="form-control" name="cat">  
            '''
            cur = connection.cursor()
            cur.execute("SELECT category FROM astarcompo_vpcat")
            cats = cur.fetchall()
            for ct in cats:
                if ct[0]==cat:
                    catlst = catlst + '<option value="%s" selected>' %(ct[0]) + ct[0] + '</option>'
                else:
                    catlst = catlst + '<option value="%s">' %(ct[0]) + ct[0] + '</option>'
            catlst = catlst + "</select></div></div>"
            

            typelst= '<input type="text" class="form-control" id="type" readonly="true" name="type" value="%s">' %(ty) 
            
            '''
            typelst = """
            <div class="form-group">
                <label for="select" class="col-lg-2 control-label">Type</label>
                <div class="col-lg-12">
                  <select class="form-control" name="type">  
            """
      
            if ty=="Phrase":
                typelst = typelst + '<option value="Phrase" selected>Phrase</option><option value="Vocabulary">Vocabulary</option>'
            elif ty=="Vocabulary":
                typelst = typelst + '<option value="Phrase">Phrase</option><option value="Vocabulary" selected>Vocabulary</option>'
            
            typelst = typelst + "</select></div></div>"
    
            '''
            
            
            themelst = '''
            <div class="form-group">
                <label for="select" class="col-lg-2 control-label">Theme</label>
                <div class="col-lg-12">
                  <select class="form-control" name="theme">  
            '''
        
            cur.execute("SELECT theme FROM astarcompo_themes")
            themes = cur.fetchall()
            for th in themes:
                if th[0]==theme:
                    themelst = themelst + '<option value="%s" selected>' %(theme) + theme + '</option>'
                else:
                    themelst = themelst + '<option value="%s">' %(th[0]) + th[0] + '</option>'
            
            if theme:
                themelst = themelst + '<option value=""></option></select></div></div>'
            else:
                themelst = themelst + '<option value="" selected></option></select></div></div>'
            
            cur.close()
            
            return render(request, 'create_vp.html', {'errors': errors, 'catlst': catlst, 'typelst': typelst, 'themelst': themelst, 'vp': vp, 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))
           
    return render(request, '404.html', {}, context_instance=RequestContext(request))
    
#Delete Vocabulary for database
def deleteVP(request):
    superuser = request.session.get('superuser')
    if superuser:
        vp = request.GET.get('vp', '')
        vtype = request.GET.get('type', '')
        cur = connection.cursor()
        cur.execute("SET autocommit=1")
        if vtype == "Vocabulary":
            cur.execute("DELETE FROM astarcompo_vocabularies WHERE vocabulary='%s'"% (vp))
        elif vtype=="Phrase":
            cur.execute("DELETE FROM astarcompo_phrases WHERE phrase='%s'"% (vp))
        cur.close()
        return HttpResponseRedirect('/vplist/')
    return render(request, '404.html', {'user': ''}, context_instance=RequestContext(request))  
    
        
def confirmDelete(request):
    
    superuser = request.session.get('superuser')
    if superuser:
        if request.GET.get('dtype', ''):
            dtype = request.GET.get('dtype', '')
            if dtype  == "question":
                if (request.GET.get('id', '')) or (request.GET.get('type', '')):
                    prevURL = "/%s/" % (request.GET.get('type', '').lower())
                    deleteURL = "/deleteQuestion/?id=%s&type=%s" % ((request.GET.get('id', '')), (request.GET.get('type', '')))
                else:
                    return render(request, '404.html', {}, context_instance=RequestContext(request))
            elif dtype  == "template":
                if (request.GET.get('template', '')) or (request.GET.get('theme', '')):
                    prevURL = "/theme/?theme=%s'/"% (request.GET.get('theme', ''))
                    deleteURL = "/deleteTemplate/?template=%s&theme=%s" % ((request.GET.get('template', '')), (request.GET.get('theme', '')))
                else:
                    return render(request, '404.html', {}, context_instance=RequestContext(request))
            elif dtype  == "vp":
                if (request.GET.get('vp', '')) or (request.GET.get('type', '')):
                    prevURL = "/vplist/"
                    deleteURL = "/deleteVP/?vp=%s&type=%s" % ((request.GET.get('vp', '')), (request.GET.get('type', '')))
                else:
                    return render(request, '404.html', {}, context_instance=RequestContext(request))
    
            elif dtype  == "theme":
                if (request.GET.get('themeID', '')):
                    prevURL = "/themes/"
                    deleteURL = "/deleteTheme/?id=%s" % ((request.GET.get('themeID', '')))
                else:
                    return render(request, '404.html', {}, context_instance=RequestContext(request))
            
            elif dtype  == "video":
                if (request.GET.get('vid', '')):
                    prevURL = "/videolist/"
                    deleteURL = "/deleteVideo/?id=%s" % ((request.GET.get('vid', '')))
                else:
                    return render(request, '404.html', {}, context_instance=RequestContext(request))
            
            return render(request, 'deleteConfirmation.html', {'deleteURL': deleteURL, 'prevURL': prevURL, 'superuser': superuser }, context_instance=RequestContext(request))
          
        else:
            return render(request, '404.html', {}, context_instance=RequestContext(request))
 
        
    return render(request, '404.html', {'user': ''}, context_instance=RequestContext(request))


#Video Learning

#Request Create Video Page
def createVideoPage(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    superuser = request.session["superuser"];
    username = request.session["username"]  
    return render(request, 'create_video.html', {'cu': "/createVideo/", 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
    
    
#Insert Video into database
def createVideo(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next': request.path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    errors = []
    if request.method == 'POST':
        superuser = request.session["superuser"];
        username = request.session["username"] 
        
        if not request.POST.get('title', ''):
           errors.append('Title is empty.')
        if not request.POST.get('url', ''):
           errors.append('URL is empty.')
           
        if not errors:
            url = request.POST.get('url', '')
            title = request.POST.get('title', '')
            cur = connection.cursor()
            cur.execute("SET autocommit=1")
            cur.execute("INSERT INTO astarcompo_learningvideos(url, title, noOfViews, dateCreated) VALUES(%s, %s, %s,%s)", (url, title, 0, datetime.datetime.now()))
            cur.close()
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Video Created! </strong></div>'
            return render(request, 'create_video.html', {'success': content, 'url': url, 'title': title, 'user': username, 'superuser': superuser}, context_instance=RequestContext(request))
        else:
            return render(request, 'create_video.html', {'errors': errors, 'url': url, 'title': title, 'user': username, 'superuser': superuser}, context_instance=RequestContext(request))
            
    return render(request, '404.html', {}, context_instance=RequestContext(request))

#Retrieve list of vidoes
def listVideos(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    superuser = request.session["superuser"];
    username = request.session["username"]  
    cur = connection.cursor()
    cur.execute("SELECT id, title from astarcompo_learningvideos")
    
    content = ""
    if cur.rowcount == 0:
        content = "<p>No Videos Available</p>"
        return render(request, 'videos.html', {'content': content, 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
 
    else:
        videos = cur.fetchall()
     
        
        if superuser:
            content = "<table id=\"vtable\" class=\"table table-striped table-hover\"><thead><tr><th>Title</th><th>&nbsp;</th><th>&nbsp;</th><th>&nbsp;</th></tr></thead><tbody>"
            for video in videos:
                content = content + "<tr><td>%s</td><td><button type=\"button\" onclick=\"window.location='/video/?id=%s'\" class=\"btn btn-primary btn-xs\">View</button></td><td><button type=\"button\" onclick=\"window.location='/editVideoPage/?id=%s'\" class=\"btn btn-primary btn-xs\">Edit</button></td><td><button type=\"button\" onclick=\"window.location='/confirmDelete/?dtype=video&vid=%s&type=Videos'\" class=\"btn btn-primary btn-xs\">Delete</button></td></tr>" %(video[1], video[0], video[0], video[0])
        else:
            content = "<table id=\"vtable\" class=\"table table-striped table-hover\"><thead><tr><th>Title</th><th>&nbsp;</th></tr></thead><tbody>"
            for video in videos:
                content = content + "<tr><td>%s</td><td><button type=\"button\" onclick=\"window.location='/video/?id=%s'\" class=\"btn btn-primary btn-xs\">View</button></td></tr>" %(video[1], video[0])
            
        content = content +   "</tbody></table>" 
        return render(request, 'videos.html', {'content': content, 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
    cur.close()

    
#Request Edit Video Page
def editVideoPage(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    superuser = request.session["superuser"];
    username = request.session["username"]  
    vid = request.GET.get('id', '')
    cur = connection.cursor()
    cur.execute("SELECT title, url from astarcompo_learningvideos WHERE id ='%s'" % (vid))
    video = cur.fetchone()
    return render(request, 'create_video.html', {'title': video[0], 'url': video[1], 'id': vid, 'cu': "/editVideo/", 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
    cur.close()
    
    
#Update video in database
def editVideo(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next': request.path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    errors = []
    if request.method == 'POST':
        superuser = request.session["superuser"];
        username = request.session["username"] 

        if not request.POST.get('title', ''):
           errors.append('Title is empty.')
        if not request.POST.get('url', ''):
           errors.append('URL is empty.')
           
        if not errors:
            url = request.POST.get('url', '')
            title = request.POST.get('title', '')
            vid = request.POST.get('id', '')
            cur = connection.cursor()
            cur.execute("SET autocommit=1"), 
            cur.execute("UPDATE astarcompo_learningvideos SET url='%s', title='%s' WHERE id='%s'" % (url, title, vid))
            cur.close()
            content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Video Updated! </strong></div>'
            return render(request, 'create_video.html', {'success': content, 'url': url, 'title': title, 'user': username, 'superuser': superuser}, context_instance=RequestContext(request))
        else:
            return render(request, 'create_video.html', {'errors': errors, 'url': url, 'title': title, 'user': username, 'superuser': superuser}, context_instance=RequestContext(request))
            
    return render(request, '404.html', {}, context_instance=RequestContext(request))
    
#Delete Video from database
def deleteVideo(request):
    superuser = request.session.get('superuser')
    if superuser:
        vid = request.GET.get('id', '')
        cur = connection.cursor()
        cur.execute("SET autocommit=1")
        cur.execute("DELETE FROM  astarcompo_learningvideos WHERE id='%s'"% (vid))
        cur.close()
        return HttpResponseRedirect('/videolist/')
    return render(request, '404.html', {'user': ''}, context_instance=RequestContext(request))

#View requsted video
def viewVideo(request):
    username = request.session["username"]  
    superuser = request.session.get('superuser')
       
    vid = request.GET.get('id', '')     
    cur = connection.cursor()
    cur.execute("SELECT title, url, noOfViews from astarcompo_learningvideos WHERE id ='%s'" % (vid))
    video = cur.fetchone()
    if not video:
         return render(request, '404.html', {}, context_instance=RequestContext(request))
    count = video[2] + 1
    cur.execute("SET autocommit=1"), 
    cur.execute("UPDATE astarcompo_learningvideos SET noOfViews = %s WHERE id=%s", (count, vid))
    cur.execute("SELECT id, title from astarcompo_learningvideos WHERE id <> %s" %(vid))
    videos = cur.fetchall()
    content = '<div class="well" >No. of views: %s <br/><h2>Other Videos</h2><ul class="list">' %(video[2])
    for v in videos:
        content = content + '<li><a href="/video/?id=%s">%s</a></li>'% (v[0], v[1])
    content = content + "</ul></div>"
    cur.close()
    return render(request, 'watch_video.html', {'title': video[0], 'url': video[1], 'content': content, 'user': username, 'superuser': superuser }, context_instance=RequestContext(request))

#Writing Support

#dictionary
def dictionary(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    
    word = request.GET.get('word', '')
    
    if word:
        apiUrl = 'http://api.wordnik.com/v4'
        apiKey = '451974a819100c50c10090123a70643c65b035d24b96b980c'
        client = swagger.ApiClient(apiKey, apiUrl)
        wordApi = WordApi.WordApi(client)
        definitions = wordApi.getDefinitions(word, sourceDictionaries='wiktionary')
        
        content = "<h4>%s</h4><h4><i>Definition(s): </i></h4><ul>" %(word)
        for definition in definitions:
             content = content + "<li>" + definition.text + "</li>"

        eg = wordApi.getExamples(word)
        content = content + "</ul><h4>Example(s): </h4><ul>"
        for e in eg.examples:
            content = content + "<li>" + e.text + "</li>"
        content = content + "</ul>"
        '''
        if len(wn.synsets(word))!=0:
            content = "<h2><i>Definition: </i></h2>"
            for word in wn.synsets(word):
                df = word.definition 
                content = content + df + "<br/>"
            
        else:
            content = 'Word Definition is not found. Find definition on google? click <a href="https://www.google.com.sg/#q=%s" target="_blank">here</a>!' % (word)
        '''
    else:
        content = "Word is not specify"
    return render(request, 'dictionary.html', {'content': content}, context_instance=RequestContext(request))
    

#Retrieves Vocabualry regard to theme
def vp(request): 
     if not request.user.is_authenticated():
         return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
     superuser = request.session["superuser"];
     username = request.session["username"]  
     cur = connection.cursor()
     cur.execute("SELECT phrase, category, theme from astarcompo_phrases")
    
     cur1 = connection.cursor()
     cur1.execute("SELECT vocabulary, category, theme from astarcompo_vocabularies")
   
     content = ""
     if cur.rowcount == 0 or cur1.rowcount ==0 :
         content = "<p>No Vocabulary or Phrase</p>"
         return render(request, 'vplist.html', {'content': content, 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
 
     else:
         vs = cur1.fetchall()
         ps = cur.fetchall()
         content = "<table id=\"vptable\" class=\"table table-striped table-hover\"><thead><tr><th>Vocabulary</th><th>Category</th><th>Theme</th></tr></thead><tbody>"
         for v in vs:
             word = '<a href="#myModal" data-toggle="modal" data-load-remote="/dictionary/?word=%s" data-remote-target="#myModal .modal-body">%s</a>' %(v[0], v[0])
             content = content + "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" %(word, v[1], v[2])
         for p in ps:
             phrase = '<a href="https://www.google.com.sg/#q=%s" target="_blank">' %(p[0]) + p[0] + "</a><br/>" 
             content = content + "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" %(phrase, p[1], p[2])
        
         content = content +   "</tbody></table>" 
        
         return render(request, 'vp.html', {'content': content, 'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
     cur.close()
     cur1.close()   

#Retrieve  guides
def guides(request):
    if not request.user.is_authenticated():
        return render(request, 'login.html', {'next':  request.get_full_path, 'user': "", 'superuser': ""}, context_instance=RequestContext(request))
    superuser = request.session["superuser"];
    username = request.session["username"]  
    return render(request, 'guides.html', {'user': username, 'superuser': superuser  }, context_instance=RequestContext(request))
    
#Insert Comment into database
def addComment(request):
    if request.method == 'POST':
        qid = request.POST.get('qid', '')
        aid = request.POST.get('aid', '')
        username = request.session["username"]
        comment = request.POST.get('comment', '')
    
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        cur = connection.cursor()
        cur.execute("SELECT id from auth_user where username = '%s'" %(username))
        userid = cur.fetchone()
        cur.execute("SET autocommit=1")
        cur.execute("INSERT INTO astarcompo_modelAnswerComments(ansid, comment, userid, timedate) VALUES(%s, %s, %s, %s)", (aid, comment, userid[0], now))
        cur.close()
        return HttpResponseRedirect('/browse/?id=%s' % (qid))

#Deete Comment from database
def deleteComment(request):
    superuser = request.session["superuser"]
    if superuser:
        cid = request.GET.get('id', '')  
        cur = connection.cursor()
        cur.execute("SELECT ansid from astarcompo_modelAnswerComments where id = '%s'" %(cid))
        aid =  cur.fetchone() 
        cur.execute("SELECT questionID from astarcompo_model_ans where ansid = '%s'" %(aid))
        qid =  cur.fetchone()
        cur = connection.cursor()
        cur.execute("SET autocommit=1")
        cur.execute("DELETE FROM astarcompo_modelAnswerComments where id = '%s'" %(cid))
        cur.close()
        return HttpResponseRedirect('/browse/?id=%s' % (qid[0]))
    return render(request, '404.html', {'user': ''}, context_instance=RequestContext(request))
          
#Retrieve Comments for model answer
def retrieveComments(request, aid):
    superuser = request.session["superuser"];
    username = request.session["username"]
    cur = connection.cursor()
    cur.execute("SELECT COUNT(*) from astarcompo_modelAnswerComments where ansid = '%s'" %(aid))
    numrows = cur.fetchone()
    
    cur.execute("SELECT questionID from astarcompo_model_ans where ansid = '%s'" %(aid))
    qid =  cur.fetchone()
    
    if numrows[0]== 0:
       commenttext = '''
       No Comments Available
       <form id="com" method="Post" action="/addComment/">

       <div class="form-group">
       <label class="control-label" for="comment">Comment</label>
       <textarea class="form-control" rows="3" id="comment" name="comment"></textarea>
       <input type="hidden" name="aid" value="%s"/>
       <input type="hidden" name="qid" value="%s"/>
       <input type="hidden" name="csrfmiddlewaretoken" value="%s"/>
       <br/>
       <button type="submit"  id="submit" disabled class="btn btn-primary">Post</button>
       </div>
       </form>
       ''' %(aid, qid[0], get_or_create_csrf_token(request))
    
       return commenttext
        
    cur.execute("SELECT id, comment, userid, timedate from astarcompo_modelAnswerComments where ansid = '%s'" %(aid))
    comments = cur.fetchall()
    commenttext = '<ul class="list-group" id="comments">'
    for comment in comments:
        cu = connection.cursor()
        cu.execute("SELECT username from auth_user where id = '%s'" %(comment[2]))
        username = cu.fetchone()
        name = username[0].split("@")
        
        t = comment[3].strftime('%Y-%m-%d %H:%M')
        if superuser:
            commenttext = commenttext + '<li class="list-group-item">' + comment[1].replace("\n", "<br/>") + '<br/><small>Posted by: %s @ %s' %(name[0], t) + '</small><span style="float:right"><a href="/deleteComment/?id=%s">Delete</a></span></li>' %(comment[0])
        else:
            commenttext = commenttext + '<li class="list-group-item">' + comment[1].replace("\n", "<br/>") + '<br/><small>Posted by: %s @ %s' %(name[0], t) + '</small></li>'
            
    commenttext =  commenttext + '''
    </ul>
    <center><div id="loadMore">Load more</div></center>
     <form id="com" method="Post" action="/addComment/">
    
    <div class="form-group">
    <label class="control-label" for="comment"><h3>Your Comment</h3></label>
    <textarea class="form-control" rows="3" id="comment" name="comment"></textarea>
    <input type="hidden" name="aid" value="%s"/>
    <input type="hidden" name="qid" value="%s"/>
    <input type="hidden" name="csrfmiddlewaretoken" value="%s"/>
    <br/>
    <button type="submit"  id="submit" disabled class="btn btn-primary">Post</button>
    </div>
    </form>
    ''' %(aid, qid[0], get_or_create_csrf_token(request))
    cur.close()
    return commenttext

#Request Home Page
def homepage(request):
    if request.user.is_authenticated():
        usr = request.session["username"]
        superuser = request.session["superuser"] 
        return render(request, 'index.html', {'user': usr, 'superuser': superuser }, context_instance=RequestContext(request))
    return render(request, 'index.html', {'user': "", 'superuser': ""}, context_instance=RequestContext(request))

#Request Error Page
def errorPage(request):
    if request.user.is_authenticated():
        usr = request.session["username"]
        superuser = request.session["superuser"] 
        return render(request, '404.html', {'user': usr, 'superuser': superuser }, context_instance=RequestContext(request))   
    
    return render(request, '404.html', {'user': "", 'superuser': ""}, context_instance=RequestContext(request))    

#For POST
from django.middleware import csrf
def get_or_create_csrf_token(request):
    token = request.META.get('CSRF_COOKIE', None)
    if token is None:
        token = csrf._get_new_csrf_key()
        request.META['CSRF_COOKIE'] = token
    request.META['CSRF_COOKIE_USED'] = True
    return token

'''
#Retrieve Themes for Question Page
def retrieveThemes(request):
    cur = connection.cursor()
    cur.execute("SELECT theme from astarcompo_themes")
    themes = cur.fetchall()
    cur.close()
    themeddl = '<select class="form-control" name="theme" id="theme">'
    for theme in themes:
        themeddl = themeddl + '<option value="%s">%s</option>' % (theme[0], theme[0])
    themeddl = themeddl + '</select>'  
    return themeddl  
'''  

#Save file on to disk
def save_file(file, newname, ext):
    fd = open('%s/%s' % (MEDIA_ROOT, str(newname + ext)), 'wb')
    for chunk in file.chunks():
        fd.write(chunk)
    fd.close()   
'''    
def extractPhrases(text):
    phrases = []
    sentences = re.split(r' *[\.\?!][\'"\)\]]* *', text)
    pattern = """
        NP: {<DT>? <JJ>* <NN>*} # NP
        PP: {<IN> <NP> <IN> <NP> <IN> <NP> | <IN> <NP|PP>}      # PP -> P NP
        VP: {<V.*> <NP|PP>*}  # VP -> V (NP|PP)*
    """
    for sentence in sentences:
      tokens = nltk.wordpunct_tokenize(sentence)
      postoks = nltk.pos_tag(tokens)
      chunker = nltk.RegexpParser(pattern)
      if postoks:
        result = chunker.parse(postoks)
        for n in result:
          if isinstance(n, nltk.tree.Tree):
            if (n.node == 'VP' or n.node == 'PP') and len(n) >1:
              phrase = ""
              for i in range(0, len(n.leaves())):
                phrase = phrase + " " + n.leaves()[i][0] 
              if len(phrase.split(" "))> 3:
                phrases.append(phrase.strip() + "</br>")
    return phrases
'''

#Match Vocabulary
def commonPhrasesVocabs(text):
    phrasesvocabs = []
    cur1 = connection.cursor()
    cur1.execute("SELECT phrase from astarcompo_phrases")
    phrases = cur1.fetchall()
    
    cur2 = connection.cursor()
    cur2.execute("SELECT vocabulary from astarcompo_vocabularies")
    vocabs = cur2.fetchall()
    
    '''
    text = text.replace("-", "_")
    text = re.sub(r'[^\w\s]','',text)
    tokens = text.lower().split()
    tokens = [t.replace('_', '-') for t in tokens]
    '''
    
    for vocab in vocabs: 
        #if vocab[0] in tokens:
        if len(re.findall('\\b%s\\b' %(vocab[0]), text))>0: 
            phrasesvocabs.append(vocab[0])        
        #if text.lower().find(vocab[0])!= -1:

                   
                     
    for phrase in phrases:
        if text.lower().find(phrase[0])> 0:
                phrasesvocabs.append(phrase[0])
    
    phrasesvocabs = sorted(set(phrasesvocabs))
    return phrasesvocabs
    
'''    
def downloadPackages(request):
    
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('maxent_treebank_pos_tagger')
            
    content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Packages downloaded successfully </strong></div>'
    return render(request, 'packages.html', {'content': content}, context_instance=RequestContext(request))
'''
'''
def rebuildTemplates(request):
  
    
    cur = connection.cursor()
    cur.execute("SET autocommit=1")
    cur.execute("TRUNCATE astarcompo_templates")
    cur.execute("SELECT a.ans, q.theme, q.questionType FROM astarcompo_questions q,  astarcompo_model_ans a WHERE a.questionID = q.questionID")
    questions = cur.fetchall()
    cur.close()
    for question in questions:
        if question[2]== 'Continuous':
            paragraphs = question[0].split("\n")
            counter = 0
            mb = ""
            for i in range(1, len(paragraphs) - 1):
                mb = mb + paragraphs[i].strip() + "\n"
                if counter == 0:
                    mb = mb.replace("\n", "")
                counter = counter + 1
                           
            cur1 = connection.cursor()
            cur1.execute("SET autocommit=1")
            cur1.execute("INSERT INTO astarcompo_templates(template, templateType, theme) VALUES(%s, %s, %s)", (paragraphs[0], 'Introduction', question[1]))
            cur1.execute("INSERT INTO astarcompo_templates(template, templateType, theme) VALUES(%s, %s, %s)", (mb, 'Main Body', question[1]))
            cur1.execute("INSERT INTO astarcompo_templates(template, templateType, theme) VALUES(%s, %s, %s)", (paragraphs[len(paragraphs)-1], 'Conclusion', question[1])) 
            cur1.close()
            
    
        
    content = '<div class="alert alert-dismissable alert-success"><button type="button" class="close" data-dismiss="alert">x</button><strong>Templates rebuild successfully </strong></div>'
    return render(request, 'rebuildTemplates.html', {'content': content}, context_instance=RequestContext(request))
'''  

'''
def output(request):   
    cur = connection.cursor()
    content = ""
    cur.execute("SELECT a.ans, q.question, q.questionID, q.theme, q.questionType, q.questionCategory from astarcompo_questions q, astarcompo_model_ans a where q.questionID = a.questionID ORDER BY q.questionType")   
    qas = cur.fetchall()
    count = 1

    for qa in qas:
        content = content + "<h4>Question %s </h4><h4>QuestionID: %s </h4><h4>Question Type: %s </h4><h4>Question Category: %s </h4><h4>Theme: %s </h4>" % (count, qa[2], qa[4], qa[5], qa[3])
        content = content + qa[1].replace('\n','<br/>')
        cur.execute("SELECT url from astarcompo_pictorial where questionID = '%s'" %(qa[2]))
        if not cur.rowcount == 0:
            pic = cur.fetchone()
            content = content + "<p><img src = %s/%s></p>" % ('/static/pictures', pic[0])
        content = content + "<h4>Sample Solution</h4>" + qa[0].replace('\n','<br/>') + '<br/><br/>'
        count = count + 1
    

    cur.close()
   
    return render(request, 'pdf.html', {'content': content }, context_instance=RequestContext(request))
'''

