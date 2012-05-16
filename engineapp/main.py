import cgi
import datetime
import urllib
import webapp2

from google.appengine.ext import db
from google.appengine.api import users


class Greeting(db.Model):
  """Models an individual Guestbook entry with an channel, content, and date."""
  channel = db.UserProperty()
  channell = db.StringProperty()
  writer = db.StringProperty()
  content = db.StringProperty(multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)


def guestbook_key(guestbook_name=None):
  """Constructs a datastore key for a Guestbook entity with guestbook_name."""
  return db.Key.from_path('Guestbook', guestbook_name or 'default_guestbook')


def f2(seq): 
   # order preserving
   checked = []
   for e in seq:
       if e not in checked:
           checked.append(e)
   return checked


class MainPage(webapp2.RequestHandler):
  def get(self):
    self.response.out.write(""" 
	  
	  <html>
	  <head>
	  <title>Just Write In</title>
	  <meta name="description" content="You can write something here about any event, let us hear it :D" />
	  </head>
	  <body style="font-family:arial; font-size:13px"> 
			  
			  """)
    guestbook_name=self.request.get('guestbook_name')

    # Ancestor Queries, as shown here, are strongly consistent with the High
    # Replication datastore. Queries that span entity groups are eventually
    # consistent. If we omitted the ancestor from this query there would be a
    # slight chance that Greeting that had just been written would not show up
    # in a query.
    greetings = db.GqlQuery("SELECT * "
                            "FROM Greeting "
                            "WHERE ANCESTOR IS :1 "
                            "ORDER BY date DESC LIMIT 10",
                            guestbook_key(guestbook_name))


    currentchannel = cgi.escape(guestbook_name)

    if (guestbook_name==''):
      currentchannel = 'just write in'

    self.response.out.write("""
	  <div style="background-color:#F7D66A;">
	  <center> 
	  <p>this channel is <b>%s</b>
	  <form>other channel event: <input name="guestbook_name">
          <input type="submit" value="switch"></form>
	  <p><span style="color:#006356;">you can make your own channel by insert to the form above</span></p>
	  <p>most popular channel :

		    """ % currentchannel)

    channells = db.GqlQuery("SELECT * "
                            "FROM Greeting")
    seq = []

    for chanel in channells:
      if chanel.channell:
        seq.append(chanel.channell)
      else:
	seq.append('writesomething')
    
    sque = f2(seq)
    numberwriting = seq.count('writesomething')
    self.response.out.write(
			'#<a href="/"><b>just write in</b></a><span style="font-size:10px;"> ['+str(numberwriting)+']</span>, ' )
    for chanel in sque:
      if chanel:
	numberwriting = seq.count(chanel)
	if chanel != 'writesomething':
          self.response.out.write(
			'#<a href="/?guestbook_name='+cgi.escape(chanel)+'"><b>'+cgi.escape(chanel)+'</b></a><span style="font-size:10px;"> ['+str(numberwriting)+']</span>, ')
	  

    self.response.out.write("""
    			</center><hr>
    			</div>
			""")


    for greeting in greetings:
      if greeting.writer:
        self.response.out.write(
			'<b style="font-size:16px;">%s</b> <span style="font-size:11px; color:#575254;">wrote:</span>' % cgi.escape(greeting.writer))
      else:
	self.response.out.write('<b><span style="font-size:16px; color:red;">Hacker</span></b><span style="font-size:11px; color:#575254;"> wrote:</span>')

      self.response.out.write('<blockquote>%s</blockquote>' %
                              cgi.escape(greeting.content))

    self.response.out.write("""
          
	  <form action="/sign?%s" method="post">
            <div><textarea name="content" rows="3" cols="60"></textarea></div>
	    <div><br>your name : <input type="text" name="writer" value="%s" /></div>
            <div><br><input type="submit" value="Write Something"></div>
          </form>
          <hr>
	  <div style="height:40px; background-color:#F7D66A; padding-top:10px;">
	  <center>
          <span style="color:black; font-family:arial; font-style:italic">going to be opensource. fully written in Python, hosted on Google's App Engine</span>   
          </center>
	  </div>
       	  </body>
          </html>
      """ % (urllib.urlencode({'guestbook_name': guestbook_name}),
                        cgi.escape(self.request.get('writer'))))


class Guestbook(webapp2.RequestHandler):
  def post(self):
    # We set the same parent key on the 'Greeting' to ensure each greeting is in
    # the same entity group. Queries across the single entity group will be
    # consistent. However, the write rate to a single entity group should
    # be limited to ~1/second.
    guestbook_name = self.request.get('guestbook_name')
    greeting = Greeting(parent=guestbook_key(guestbook_name))

    if users.get_current_user():
      greeting.channel = guestbook_name
      greeting.channell = cgi.escape(guestbook_name)

    greeting.channell = cgi.escape(guestbook_name)
    greeting.content = self.request.get('content')
    greeting.writer = self.request.get('writer')
    greeting.put()
    self.redirect('/?' + urllib.urlencode({'guestbook_name': guestbook_name})+'&'+urllib.urlencode({'writer': greeting.writer}))


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/sign', Guestbook)],
                              debug=True)

