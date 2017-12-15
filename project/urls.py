from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from views import homepage
from views import registerPage
from views import loginPage
from views import forgetPasswordPage
from views import errorPage
from views import browse_mini
from views import browse
from views import insertQuestion
from views import deleteQuestion
from views import register
from views import user_login
from views import user_logout
from views import getCatandType
from views import tryexcercise
from views import insertAnswer
from views import continuous
from views import situational
from views import questions
from views import updateQuestion
from views import editQuestion
from views import updateAnswer
from views import editAnswer
from views import verifyAccount
from views import passwordChange
from views import requestPasswordChange
from views import verifyPasswordChange
from views import resendverifyAccount
#from views import downloadPackages
from views import getThemes
from views import themePage
from views import templatePage
from views import createTheme
from views import createTemplate
from views import editTheme
from views import deleteTheme
from views import editTemplate
from views import deleteTemplate
#from views import rebuildTemplates
from views import confirmDelete
from views import dictionary
from views import introduction
from views import mb
from views import conclusion
from views import vp
from views import getVPlist
from views import VPpage
from views import createVP
from views import deleteVP
from views import editVP
from views import addComment
from views import deleteComment

from views import createVideoPage
from views import createVideo
from views import listVideos
from views import editVideoPage
from views import editVideo
from views import deleteVideo
from views import viewVideo

from views import guides

#from views import output

urlpatterns = [
    # Examples:
    # url(r'^$', 'project.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', homepage),
    url(r'^forgotpassword/$', forgetPasswordPage),
    url(r'^requestpassword/$', requestPasswordChange),
    url(r'^changepassword/$', passwordChange),
    url(r'^verifyPasswordChange/$', verifyPasswordChange),
    url(r'^verifyAccount/$', verifyAccount),
    url(r'^resendverifyAccount/$', resendverifyAccount),
    (r'^login_page/$', loginPage),
    (r'^404/$', errorPage),
    (r'^register_page/$', registerPage),
    (r'^register/$', register),
    (r'^login/$', user_login),
    (r'^logout/$', user_logout),
    (r'^browse/$', browse),
    (r'^browse_mini/$', browse_mini),
    (r'^try/$', tryexcercise),
    (r'^add_answer/$', insertAnswer),
    (r'^add_question/$', getCatandType),
    (r'^questions/$', questions),
    (r'^insert_question/$', insertQuestion),
    (r'^deleteQuestion/$', deleteQuestion),
    (r'^continuous/$', continuous),		
    (r'^situational/$', situational),
    (r'^update_question/$', updateQuestion),
    (r'^edit_question/$', editQuestion),
    (r'^update_answer/$', updateAnswer),
    (r'^edit_answer/$', editAnswer),	
    #(r'^downloadPackages/$', downloadPackages),	
    #(r'^rebuildTemplates/$', rebuildTemplates),	
    (r'^confirmDelete/$', confirmDelete),
    (r'^themes/$', getThemes),
    (r'^theme/$', themePage),
    (r'^createTheme/$', createTheme),	
    (r'^editTheme/$', editTheme),	
    (r'^deleteTheme/$', deleteTheme),		
    (r'^template/$', templatePage),
    (r'^createTemplate/$', createTemplate),
    (r'^editTemplate/$', editTemplate),	
    (r'^deleteTemplate/$', deleteTemplate),
    (r'^dictionary/$', dictionary),	
    (r'^introduction/$', introduction),	
    (r'^mb/$', mb),	
    (r'^conclusion/$', conclusion),	
    (r'^vp/$', vp),	
    (r'^vplist/$', getVPlist),		
    (r'^vpPage/$', VPpage),	
    (r'^createVP/$', createVP),	
    (r'^deleteVP/$', deleteVP),
    (r'^editVP/$', editVP),	
    (r'^addComment/$', addComment),		
    (r'^deleteComment/$', deleteComment),	
    (r'^createVideoPage/$', createVideoPage),
    (r'^createVideo/$', createVideo),
    (r'^videolist/$', listVideos),	
    (r'^editVideoPage/$', editVideoPage),	
    (r'^editVideo/$', editVideo),	
    (r'^deleteVideo/$', deleteVideo),		
    (r'^video/$', viewVideo),
    (r'^guides/$', guides),			
    #(r'^output/$', output),	
    (r'^search/', include('haystack.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
