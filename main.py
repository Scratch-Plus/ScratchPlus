from flask import Flask, render_template, request, make_response, redirect
from Scratch import Session, get_time
import os, logging, re, json, functools
from replit import db
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask("app")
os.system("clear")

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

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
        session = Session()
        session.login(request.form["username"], request.form["password"])
        if next == "/":
          return func(session, *args, **kwargs)
        else:
          return func(*args, **kwargs)
    return decorated_function
  return decorator

def loading():
  return render_template("loading.html")

@app.route("/login", strict_slashes=False)
def login_page():
  return render_template("login.html")

@app.route("/loggedin", methods = ["POST"])
@login()
def loggedin(session):
  try:
    resp = redirect("/")
    resp.set_cookie("username", session.username, 60 * 60 * 24 * 30)
    resp.set_cookie("csrf_token", session.csrf_token, 60 * 60 * 24 * 30)
    resp.set_cookie("token", session.token, 60 * 60 * 24 * 30)
    resp.set_cookie("session_id", session.session_id, 60 * 60 * 24 * 30)
    return resp
  except:
    return render_template("login.html", message = "Incorrect username or password")

@app.route("/", strict_slashes=False)
def main():
  session = Session()
  session.set(request.cookies)
  news = session.news()
  api = session.api(session.username)
  featured = session.featured()
  tfeatured = session.turbowarp_featured()
  wh = session.wh()
  loved = session.following_loved()
  resp = render_template("home.html", api = api, news = news, featured = featured, tfeatured = tfeatured, wh = wh, loved = loved)
  if request.cookies.get("settings") == None:
    resp = make_response(resp)
    resp.set_cookie("settings", "00000")
  return resp

@app.route("/messages", methods = ["GET", "POST"], strict_slashes=False)
@login("/messages")
def messages():
  session = Session()
  session.set(request.cookies)
  new = session.new_messages()
  api = session.api(session.username)
  messages = session.messages(20, int(0) * 20)
  return render_template("messages.html", api = api, messages = messages, new = new, page = int(0), username = session.username)

@app.route("/unshared", strict_slashes=False)
def stuff():
  session = Session()
  session.set(request.cookies)
  return session.unshared()

@app.route("/session", strict_slashes=False)
def session():
  session = Session()
  session.set(request.cookies)
  return session.session()

@app.route("/users/<user>", strict_slashes=False)
def profile(user):
  session = Session()
  session.set(request.cookies)
  try:
    user_api = session.api(user)
  except:
    return render_template("404.html")
  api = session.api(session.username)
  user_featured = session.user_featured(user)
  ocular = session.ocular(user)
  shared = session.projects(user)
  favs = session.favorites(user)
  curating = session.curating(user)
  online = user_api["username"] in db["online"]
  return render_template("profile.html", api = api, user_api = user_api, user_featured = user_featured, ocular = ocular, shared = shared, favorites = favs, curating = curating, online = online)

@app.route("/users/forum", methods = ["POST"])
def forum_profile():
  user = request.form["q"]
  return redirect(f"/users/{user}/forum")

@app.route("/users/<user>/forum")
def user_forum(user):
  session = Session()
  session.set(request.cookies)
  api = session.api(session.username)
  ocular = session.ocular(user)
  forum = session.forum_user(user)
  posts = session.forum_user_posts(user)
  post_history = session.forum_post_history(user)
  return render_template("forum_profile.html", api = api, ocular = ocular, forum = forum, posts = posts, post_history = post_history)

@app.route("/reset")
def reset():
  referrer = request.referrer
  if "https://scratchplus.am4.uk/" in str(referrer) or "https://why-is-this-blocked.scratchplus.repl.co/" in str(referrer):
    user = request.cookies.get("username")
    if user in db["online"]:
      if db["online"][user] == 0:
        del db["online"][user]
      else:
        db["online"][user] = db["online"][user] - 1
    resp = redirect("/login")
    resp = make_response(resp)
    resp.set_cookie("username", expires=0)
    resp.set_cookie("csrf_token", expires=0)
    resp.set_cookie("token", expires=0)
    resp.set_cookie("session_id", expires=0)
    if request.cookies.get("settings")[2] == "1":
      resp.set_cookie("settings", expires=0)
    return resp
  else:
    return "To logout of your Scratch+ Account, please use the logout button on the website."

@app.route("/projects/<id>", strict_slashes=False)
def project(id):
  session = Session()
  session.set(request.cookies)
  try:
    project_api = session.project(id)
  except Exception:
    return render_template("404.html")
  api = session.api(session.username)
  loved = session.loved(id, session.username)
  faved = session.faved(id, session.username)
  remixes = session.project_remixes(id)
  studios = session.project_studios(id)
  comments = session.project_comments(id)
  settings = request.cookies.get("settings")
  return render_template("project.html", api = api, id = id, project_api = project_api, settings = settings, loved = loved, faved = faved, remixes = remixes, studios = studios, comments = comments)

@app.errorhandler(404)
def not_found(e):
  return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
  return render_template("500.html"), 500

@app.route("/search", methods=["POST", "GET"], strict_slashes=False)
def search():
  if request.method == "POST":
    q = request.form["q"]
    return redirect(f"/search?q={q}")
  else:
    q = request.args.get("q")
    session = Session()
    session.set(request.cookies)
    user, projects, studios, forum = session.search(q)
    api = session.api(session.username)
    return render_template("search.html", user = user, projects = projects, studios = studios, forum = forum, api = api)

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

@app.route("/secret", strict_slashes=False)
@login("/secret")
def ssecret():
  session = Session()
  session.set(request.cookies)
  return session.ascii(session.username)

@app.route("/secret/<user>", strict_slashes=False)
def secret(user):
  session = Session()
  return session.ascii(user)

@app.route("/update_Bio", methods = ["POST"])
def update_Bio():
  session = Session()
  session.set(request.cookies)
  Bio = str(request.data.decode("utf-8", "replace")).strip()
  session.set_bio(Bio)
  return ""

@app.route("/update_Status", methods = ["POST"])
def update_Status():
  session = Session()
  session.set(request.cookies)
  Status = str(request.data.decode("utf-8", "replace")).strip()
  session.set_status(Status)
  return ""

@app.route("/clear", methods = ["POST"])
def clear():
  session = Session()
  session.set(request.cookies)
  session.clear()
  return ""

@app.route("/settings", methods = ["GET", "POST"], strict_slashes=False)
def settings():
  session = Session()
  session.set(request.cookies)
  api = session.api(session.username)
  return render_template("settings.html", data = request.cookies.get("settings"), api = api)

@app.route("/update_settings", methods = ["POST"])
def update_Settings():
  session = Session()
  session.set(request.cookies)
  Settings = str(request.data.decode("utf-8", "replace")).strip()
  resp = make_response("")
  resp.set_cookie("settings", Settings)
  return resp

@app.route("/love", methods = ["POST"])
@login("/")
def love():
  session = Session()
  session.set(request.cookies)
  data = json.loads(str(request.data.decode("utf-8", "replace")).strip())
  session.love(**data)
  return ""

@app.route("/favorite", methods = ["POST"])
@login("/")
def favorite():
  session = Session()
  session.set(request.cookies)
  data = json.loads(str(request.data.decode("utf-8", "replace")).strip())
  session.favorite(**data)
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
  session = Session()
  session.set(request.cookies)
  api = session.api(session.username)
  studio_api = session.studio_api(id)
  studio_projects = session.studio_projects(id)
  studio_comments = session.studio_comments(id)
  studio_members = session.studio_members(id)
  studio_activity = session.studio_activity(id)
  return render_template("studio.html", api = api, studio_api = studio_api, studio_projects = studio_projects, studio_comments = studio_comments, members = studio_members, activity = studio_activity)

@app.template_filter("time")
def time(TZ):
  try:
    return get_time(TZ)
  except:
    return "-"

@app.route("/discuss")
def forum():
  session = Session()
  session.set(request.cookies)
  api = session.api(session.username)
  leaderboard = session.forum_leaderboard()
  return render_template("forum.html", api = api, leaderboard = leaderboard)

@app.route("/discuss/topic/<topic_id>")
def forum_topic(topic_id):
  if request.args.get("loaded") != "true":
    return loading()
  session = Session()
  session.set(request.cookies)
  page = request.args.get("page")
  order = request.args.get("order")
  try:
    page = int(page)
  except:
    page = 0
  if not order == ["newest", "oldest"]:
    order = "oldest"
  api = session.api(session.username)
  posts = session.topic_posts(topic_id, page, order)
  topic = session.topic_info(topic_id)
  return render_template("forum_posts.html", api = api, posts = posts, page = page, topic = topic)

@app.route("/discuss/<id>")
def forum_category(id):
  session = Session()
  session.set(request.cookies)
  api = session.api(session.username)
  categories = {5: "Announcements", 6: "New Scratchers", 7: "?Help With Scripts", 8: "Show and Tell", 9: "Project Ideas", 10: "Collaboration", 11: "Requests", 4: "?Questions about Scratch", 1: "Suggestions", 3: "Bugs and Glitches", 31: "Advanced Topics", 32: "Connecting to the Physical World", 48: "Developing Scratch Extensions", 49: "Open Source Projects", 29: "Things I'm Making and Creating", 30: "Things I'm Reading and Playing"}
  category = categories[int(id)], id
  topics = session.category_topics(category[0])
  leaderboard = session.topic_leaderboard(category[0])
  return render_template("forum_category.html", api = api, category = category, topics = topics, leaderboard = leaderboard)

@app.template_filter("split")
def split(text, substring):
  return text.split(substring)

@app.route("/explore")
def explore():
  session = Session()
  session.set(request.cookies)
  type = str(request.args.get("type")).lower()
  if not type in ["projects", "studios"]:
    type = "projects"
  page = request.args.get("page")
  if page == None:
    page = 0
  mode = str(request.args.get("mode")).lower()
  if mode not in ["trending", "popular", "recent"]:
    mode = "trending"
  api = session.api(session.username)
  data = session.explore(type, page, mode)
  return render_template("explore.html", api = api, data = data)

@app.route("/open", methods = ["GET","POST"])
def open():
  if request.method == "POST":
    user = request.cookies.get("username")
    if user in db["online"]:
      db["online"][user] = db["online"][user] + 1
    else:
      db["online"].update({user: 1})
    return ""
  else:
    return str(dict(db["online"]))

@app.route("/close", methods = ["POST"])
def close():
  user = request.cookies.get("username")
  if user in db["online"]:
    if db["online"][user] == 0:
      del db["online"][user]
    else:
      db["online"][user] = db["online"][user] - 1
  return ""

@app.route("/clrdb")
def clrdb():
  db["online"] = {}

@app.template_filter("append")
def append(text, new):
  return text.append(new)

app.run(host='0.0.0.0', port=8080)
