from flask import Flask, render_template, request, make_response, redirect, Response
from Scratch import Session, get_time
import os, logging, re, json, functools, math, requests
logging.getLogger('werkzeug').disabled = True
from API import *

golinks = {
  "post" : "https://scratch.mit.edu/discuss/topic/550473/?page=1#post-5697737"
}

app = Flask("app")
os.system("clear")

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.url_map.strict_slashes = False
app.secret_key = os.environ["key"]

def login(next = "/"):
  def decorator(func):
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
      if request.method == "GET":
        if request.cookies.get("username"):
          return func(*args, **kwargs)
        else:
          return render_template("login.html", message="Login to your Scratch accout to get started!", next = next)
      elif request.method == "POST":
        s = Session()
        s.login(request.form["username"], request.form["password"])
        if next == "/":
          return func(s, *args, **kwargs)
        else:
          return func(*args, **kwargs)
    return decorated_function
  return decorator

def loading():
  return render_template("loading.html")

@app.route('/arc-sw.js')
def arc_sw():
  resp = open("arc-sw.txt", "r").read()

  return Response(resp, mimetype="text/javascript")

@app.route('/go/', defaults={"where":None})
@app.route('/go/<where>')
def goLink(where):

  if not where:
    where = request.args.get("where")
  if not where:
    return redirect('/')

  if golinks[where]:
    return redirect(golinks[where])
  else:
    return redirect('/')

@app.route("/login")
def login_page():
  return render_template("login.html")

@app.route("/loggedin", methods = ["POST"])
@login()
def loggedin(s):
  try:
    resp = redirect("/")
    resp.set_cookie("username", s.username)
    resp.set_cookie("csrf_token", s.csrf_token)
    resp.set_cookie("token", s.token)
    resp.set_cookie("session_id", s.session_id)
    return resp
  except:
    return render_template("login.html", message = "Incorrect username or password")

@app.route("/")
def main():
  s = Session()
  s.set(request.cookies)
  news = s.news()
  api = s.api(s.username)
  featured = s.featured()
  tfeatured = s.turbowarp_featured()
  wh = s.wh()
  loved = s.following_loved()
  resp = render_template("home.html", api = api, news = news, featured = featured, tfeatured = tfeatured, wh = wh, loved = loved)
  if request.cookies.get("settings") == None:
    resp = make_response(resp)
    resp.set_cookie("settings", "000000")
  return resp

@app.route("/messages", methods = ["GET", "POST"])
@login("/messages")
def messages():
  s = Session()
  s.set(request.cookies)
  new = s.new_messages()
  api = s.api(s.username)
  messages = s.messages(20, int(0) * 20)
  return render_template("messages.html", api = api, messages = messages, new = new, page = int(0), username = s.username)

@app.route("/unshared")
def stuff():
  s = Session()
  s.set(request.cookies)
  return s.unshared()

@app.route("/users/<username>")
def profile(username):
  user = User(username)
  user_api = user.api
  if not "username" in user_api:
    return render_template("404.html"), 404
  user_featured = user.featured()
  ocular = user.ocular()
  shared = user.projects()
  favs = user.favorites()
  curating = user.curating()
  followers = user.followers()
  following = user.following()
  comments = user.comments()
  return render_template("profile.html", user_api = user_api, user_featured = user_featured, ocular = ocular, shared = shared, favorites = favs, curating = curating, comments = comments, followers = followers, following = following)

@app.route("/users/forum", methods = ["POST"])
def forum_profile():
  user = request.form["q"]
  return redirect(f"/users/{user}/forum")

@app.route("/users/<user>/forum")
def user_forum(user):
  user = User(user)
  ocular = user.ocular()
  forum = user.forum()
  posts = user.posts()
  post_history = user.forum_post_history()
  sig_history = user.forum_signiture_history()
  return render_template("forum_profile.html", ocular = ocular, forum = forum, posts = posts, post_history = post_history, sig_history = sig_history)

@app.route("/users/<user>/api")
def user_api(user):
  data = User(user).api
  data.update({"messages": User(user).messages()})
  return data

@app.route("/users/<user>/live")
def live(user):
  return render_template("live.html", user = user)

@app.route("/users/<user>/count")
def user_count(user):
  o = 1000000
  i = 0
  r = []
  while True:
    last_o = o
    if r == []:
      if 10 ** (math.floor(math.log(o, 10)) - i) == o:
        o -= 10 ** (math.floor(math.log(o, 10)) - (i + 1))
      else:
        o -= 10 ** (math.floor(math.log(o, 10)) - i)
    else:
      o += 10 ** (math.floor(math.log(o, 10)) - i)
      i += 1
    o = round(o)
    r = requests.get(f"https://api.scratch.mit.edu/users/{user}/followers?limit=1&offset={o}").json()
    if o == last_o:
      break
  return str(o)

@app.route("/reset")
def reset():
  referrer = request.referrer
  if "https://scratchplus.am4.uk/" in str(referrer) or "https://scratchplus.scratchplus.repl.co/" in str(referrer):
    resp = redirect("/login")
    resp = make_response(resp)
    resp.set_cookie("username", "", 0)
    resp.set_cookie("csrf_token", "", 0)
    resp.set_cookie("token", "", 0)
    resp.set_cookie("session_id", "", 0)
    if request.cookies.get("settings") == "1":
      resp.set_cookie("settings", "", 0)
    return resp
  else:
    return "To logout of your Scratch+ Account, please use the logout button on the website."

@app.route("/projects/<id>")
def project(id):
  s = Session()
  s.set(request.cookies)
  project = Project(id)
  project_api = project.api
  loved = s.loved(id, s.username)
  faved = s.faved(id, s.username)
  remixes = project.remixes()
  studios = project.studios()
  comments = project.comments()
  db = project.db
  settings = request.cookies.get("settings")
  return render_template("project.html", id = id, project_api = project_api, settings = settings, loved = loved, faved = faved, remixes = remixes, studios = studios, comments = comments, db = db)

@app.errorhandler(404)
def not_found(e):
  return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
  return render_template("500.html"), 500

@app.route("/search", methods=["POST", "GET"])
def search():
  if request.method == "POST":
    q = request.form["q"]
    return redirect(f"/search?q={q}")
  else:
    q = request.args.get("q")
    user = User(q).api
    projects = Project().search(q)
    studios = Studio().search(q)
    forum = Forum().search(q)
    return render_template("search.html", user = user, projects = projects, studios = studios, posts = forum)

@app.template_filter("autolink")
def autolink(text):
  users = re.findall("@(.*?)(\s|$)", text)
  for user in users:
    user = user[0].strip("(),")
    try:
      Session().api(user)
      index = text.index("@" + user)
      text = text[:index] + f"<a href='/users/{user}' target='_blank'>{user}</a>" + text[index + len(user) + 1:]
    except:
      pass
  links = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
  for link in links:
    index = text.index(link)
    if link.startswith("https://scratch.mit.edu"):
      text = text[:index] + f"<a href='/{text[index + 24: index + len(link)]}' target='_blank'>{link}</a>" + text[index + len(link):]
    else:
      text = text[:index] + f"<a href='{link}' target='_blank'>{link}</a>" + text[index + len(link):]
    
  emojis = re.findall('(?<=<img src=\")/images/emoji/.*?(?=\" class=\"emoji\" alt=\".*\">)', text)
  for emoji in emojis:
    index = text.index(emoji)
    text = text[:index] + "/static/" + text[index + 1:]
  return text

@app.route("/secret")
@login("/secret")
def ssecret():
  return Session().ascii(request.cookies.get("username"))

@app.route("/secret/<user>")
def secret(user):
  return Session().ascii(user)

@app.route("/update_Bio", methods = ["POST"])
def update_Bio():
  s = Session()
  s.set(request.cookies)
  Bio = str(request.data.decode("utf-8", "replace")).strip()
  s.set_bio(Bio)
  return ""

@app.route("/update_Status", methods = ["POST"])
def update_Status():
  s = Session()
  s.set(request.cookies)
  Status = str(request.data.decode("utf-8", "replace")).strip()
  s.set_status(Status)
  return ""

@app.route("/clear", methods = ["POST"])
def clear():
  s = Session()
  s.set(request.cookies)
  s.clear()
  return ""

@app.route("/settings", methods = ["GET", "POST"])
def settings():
  return render_template("settings.html", data = request.cookies.get("settings"))

@app.route("/update_settings", methods = ["POST"])
def update_Settings():
  Settings = str(request.data.decode("utf-8", "replace")).strip()
  resp = make_response("")
  resp.set_cookie("settings", Settings)
  return resp

@app.route("/love", methods = ["POST"])
@login("/")
def love():
  s = Session()
  s.set(request.cookies)
  data = json.loads(str(request.data.decode("utf-8", "replace")).strip())
  s.love(**data)
  return ""

@app.route("/favorite", methods = ["POST"])
@login("/")
def favorite():
  s = Session()
  s.set(request.cookies)
  data = json.loads(str(request.data.decode("utf-8", "replace")).strip())
  s.favorite(**data)
  return ""

@app.template_filter("print")
def fprint(text):
  print(text)
  return text

@app.template_filter("type")
def ftype(text):
  return str(type(text))

@app.route("/studios/<id>")
def studio(id):
  studio = Studio(id)
  api = studio.api
  projects = studio.projects()
  comments = studio.comments()
  members = {"managers": studio.managers(), "curators": studio.curators()}
  activity = studio.activity()
  return render_template("studio.html", studio_api = api, studio_projects = projects, studio_comments = comments, members = members, activity = activity)

@app.template_filter("time")
def time(TZ):
  try:
    return get_time(TZ)
  except:
    return "-"

@app.route("/discuss")
def forum():
  leaderboard = Forum().leaderboard()
  return render_template("forum.html", leaderboard = leaderboard)

@app.route("/discuss/topic/<id>")
def forum_topic(id):
  if request.args.get("loaded") != "true":
    return loading()
  page = request.args.get("page")
  order = request.args.get("order")
  try:
    page = int(page)
  except:
    page = 0
  if not order == ["newest", "oldest"]:
    order = "oldest"
  reactions = request.cookies.get("settings")[5]
  posts = Forum().topic_posts(id, page, "oldest", reactions == "1")
  topic = Forum().topic(id)
  return render_template("forum_posts.html", posts = posts, page = page, topic = topic)

@app.route("/discuss/post/<id>")
def forum_post(id):
  if request.args.get("loaded") != "true":
    return loading()
  post_info = Forum().post(id)
  topic_id = post_info["topic"]["id"]
  topic = Forum().topic(topic_id)
  pages = math.ceil(topic["post_count"] / 50)
  for page in range(pages):
    posts = Forum().topic_posts(topic_id, page)
    for post in posts:
      if post["id"] == post_info["id"]:
        return redirect(f"/discuss/topic/{topic_id}?page={page}#{id}")
  return ""

@app.route("/discuss/<id>")
def forum_category(id):
  if request.args.get("loaded") != "true":
    return loading()
  category = Forum().categories[int(id)]
  topics = Forum().topics(id)
  leaderboard = Forum().leaderboard(id)
  return render_template("forum_category.html", category = category, topics = topics, leaderboard = leaderboard)

@app.template_filter("split")
def split(text, substring):
  return text.split(substring)

@app.route("/explore")
def explore():
  type = str(request.args.get("type")).lower()
  if not type in ["projects", "studios"]:
    type = "projects"
  page = request.args.get("page")
  if page == None:
    page = 0
  mode = str(request.args.get("mode")).lower()
  if mode not in ["trending", "popular", "recent"]:
    mode = "trending"
  data = Scratch().explore(type, page, mode)
  return render_template("explore.html", data = data)

@app.route("/open", methods = ["GET","POST"])

@app.template_filter("append")
def append(text, new):
  return text.append(new)

@app.route("/scratchblocks")
def scratchblocks():
  return render_template("scratchblocks.html")

@app.route("/hmm")
def api():
  return ""

app.run(host='0.0.0.0', port=8080)
