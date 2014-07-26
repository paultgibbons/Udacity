#!/usr/bin/env python
import webapp2
import os       # needed for jinja

import re       # regular expressions
import jinja2   # templating library

from google.appengine.ext import db  # database

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BaseHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    
    def render(self, template, **kw):
        self.response.out.write(render_str(template, **kw))

class MainHandler(BaseHandler):
    def get(self):
        self.render('homepage.html')

class RotThirteenHandler(BaseHandler):

    def escape_html(self, s):
        return cgi.escape(s, quote = True)

    def rotate(self, input):
        output = ''
        for c in input:
            value = ord(c)
            if (value >= ord('a') and value < ord('n')) or (value >= ord('A') and value < ord('N')):
                output += chr(value + 13)
            elif (value >= ord('n') and value <= ord('z')) or (value >= ord('N') and value <= ord('Z')):
                output += chr(value-13)
            else:
                output += chr(value)

        return output

    def write_form(self, input=''):
        self.response.out.write(staticFiles/rot13.html %input)

    def get(self):
        self.render('rot13.html')

    def post(self):
        input = self.request.get('text')
        input = self.rotate(input)
        self.render('rot13.html', text = input)

class UserSignupHandler(BaseHandler):

    def check_username(self, s):
        USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
        return USER_RE.match(s)

    def check_password(self, s):
        PASS_RE = re.compile(r"^.{3,20}$")
        return PASS_RE.match(s)

    def check_verify(self, s, password, ):
        return s==password

    def check_email(self, s):
        EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
        return EMAIL_RE.match(s)

    def get(self):
        self.render("usersignup.html")

    def post(self):
        user_username = self.request.get("username")
        user_password = self.request.get("password")
        user_verify = self.request.get("verify")
        user_email = self.request.get("email")

        valid_username = self.check_username(user_username)
        valid_password = self.check_password(user_password)
        valid_verify = self.check_verify(user_verify, user_password)
        valid_email = self.check_email(user_email) or user_email==''

        if not (valid_username and valid_password and valid_verify and valid_email):
            usernameInput = user_username
            usernameError = ''
            if not valid_username:
                usernameError = "That's not a valid username."
            passwordError = ''
            if not valid_password:
                passwordError = "That wasn't a valid password."
            verifyError = ''
            if valid_password and not valid_verify:
                verifyError = "Your passwords didn't match."
            emailInput = user_email
            emailError = ''
            if not valid_email:
                emailError = "That's not a valid email."
            self.render('usersignup.html',
                            usernameInput = usernameInput,
                            emailInput = emailInput,
                            usernameError = usernameError,
                            passwordError = passwordError,
                            verifyError = verifyError,
                            emailError = emailError)
        else:
            self.redirect('/welcome?username=%s' %user_username)

class WelcomeHandler(BaseHandler):

    def get(self):
        username = self.request.get('username')
        self.render('userwelcome.html', username = username)

class BlogPost(db.Model):
    title = db.StringProperty(required = True)
    body = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

class BlogHandler(BaseHandler):
    def get(self):
        posts = db.GqlQuery('SELECT * FROM BlogPost ORDER BY created DESC')
        self.render("blog.html", posts=posts)

class BlogPermalinkHandler(BaseHandler):
    def get(self, permalinkId):
        post = BlogPost.get_by_id(int(permalinkId))
        if post:
            self.render('blogPermalink.html', post=post)


class BlogNewpostHandler(BaseHandler):
    def render_front(self, subject='', content='', error=''):
        self.render("blogNewpost.html", subject=subject, content=content, error=error)

    def get(self):
        self.render_front()
    def post(self):
        title = self.request.get("subject")
        body = self.request.get("content")

        if title and body:
            post = BlogPost(title = title, body = body)
            post.put()
            permalinkId = str(post.key().id())
            self.redirect('/blog/%s' % permalinkId)
        else:
            error = "both a title and body are required"
            self.render_front(error=error, subject=title, content=body)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/rot13/?', RotThirteenHandler),
    ('/usersignup/?', UserSignupHandler),
    ('/welcome/?', WelcomeHandler),
    ('/blog/?', BlogHandler),
    ('/blog/([0-9]+)/?', BlogPermalinkHandler),
    ('/blog/newpost/?', BlogNewpostHandler)
], debug=True)
