import requests, json, re, datetime, math
from Scratch import get_time

def time_rel(TZ):
  t = str(datetime.datetime.now() - datetime.datetime.strptime(TZ, "%Y-%m-%dT%H:%M:%S.%fZ"))
  if "day" in t:
    days = int(t.split(" ")[0])
    if days < 7:
      t = str(days) + " days"
    else:
      weeks = math.floor(days / 7)
      if weeks < 4:
        t = str(weeks) + " weeks"
      else:
        months = math.floor(weeks / 4)
        if months < 12:
          t = " months"
        else:
          years = math.floor(months / 12)
          t = str(years) + " ago"
  else:
    hours, minutes, _ = t.split(":")
    if hours == "0":
      if minutes == "00":
        t = "less than a minute"
      else:
        t = str(int(minutes)) + " minutes "
    else:
      t = hours + " hours"
  return t + " ago"

class _Session:
  def __init__(self, username, password):
    self.username = username
    request = requests.post("https://scratch.mit.edu/login/", data = json.dumps({"username": self.username, "password": password}), headers = {"x-csrftoken": "a","x-requested-with": "XMLHttpRequest","Cookie": "scratchcsrftoken=a;scratchlanguage=en;","referer": "https://scratch.mit.edu","user-agent": ""})
    try:
      self.session_id = re.search('"(.*)"', request.headers["Set-Cookie"]).group()
      self.token = request.json()[0]["token"]
    except AttributeError:
      return ""
    self.csrf_token = re.search("scratchcsrftoken=(.*?);", requests.get("https://scratch.mit.edu/csrf_token/", headers = {"x-requested-with": "XMLHttpRequest","Cookie": "scratchlanguage=en;permissions=%7B%7D;","referer": "https://scratch.mit.edu"}).headers["Set-Cookie"]).group(1)
    self.headers = {"x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": "https://scratch.mit.edu"}
  def messages(self, page = 0):
    return requests.get(f"https://api.scratch.mit.edu/users/{self.username}/messages?limit=40&offset={40 * int(page)}",headers = self.headers).json()
  def following_loved(self):
    projects = requests.get(f"https://api.scratch.mit.edu/users/{self.username}/following/users/loves", headers = self.headers.update({"referer": f"https://scratch.mit.edu/users/{self.username}"})).json()
    if "error" in projects:
      projects = []
    return projects
  def messages_clear(self):
    requests.post("https://scratch.mit.edu/site-api/messages/messages-clear/", headers = self.headers.update({"referer": f"https://scratch.mit.edu/users/{self.username}"}))
  def loved(self, id):
    return requests.get(f"https://api.scratch.mit.edu/projects/{id}/loves/user/{self.username}", headers = self.headers.update({"referer": f"https://scratch.mit.edu/users/{self.username}"})).json()
  def favorited(self, id):
    return requests.get(f"https://api.scratch.mit.edu/projects/{id}/favorites/user/{self.username}", headers = self.headers.update({"referer": f"https://scratch.mit.edu/users/{self.username}"})).json()
  def love(self, id):
    if self.loved(id):
      requests.delete(f"https://api.scratch.mit.edu/proxy/projects/{id}/loves/user/{self.username}", headers = self.headers.update({"referer": f"https://scratch.mit.edu/projects/{id}"}))
    else:
      requests.post(f"https://api.scratch.mit.edu/proxy/projects/{id}/loves/user/{self.username}", headers = self.headers.update({"referer": f"https://scratch.mit.edu/projects/{id}"}))
  def favorite(self, id):
    if self.favorited(id):
      requests.delete(f"https://api.scratch.mit.edu/proxy/projects/{id}/favorites/user/{self.username}", headers = self.headers.update({"referer": f"https://scratch.mit.edu/projects/{id}"}))
    else:
      requests.post(f"https://api.scratch.mit.edu/proxy/projects/{id}/favorites/user/{self.username}", headers = self.headers.update({"referer": f"https://scratch.mit.edu/projects/{id}"}))

class User:
  def __init__(self, username):
    self.username = username
    self.api = requests.get(f"https://api.scratch.mit.edu/users/{username}").json()
    self.db = requests.get(f"https://scratchdb.lefty.one/v3/user/info/{username}").json()
  def history(self):
    return requests.get(f"https://scratchdb.lefty.one/v3/user/graph/{self.username}/followers?segment=1&range=10000").json()
  def followers(self, page = 0):
    return requests.get(f"https://api.scratch.mit.edu/users/{self.username}/followers?limit=40&offset={40 * int(page)}").json()
  def following(self, page = 0):
    return requests.get(f"https://api.scratch.mit.edu/users/{self.username}/following?limit=40&offset={40 * int(page)}").json()
  def posts(self, page = 0, order = "newest", reactions = False):
    data = requests.get(f"https://scratchdb.lefty.one/v3/forum/user/posts/{self.username}/{page}?order={order}").json()
    new = []
    for post in data:
      post.update({"ocular": requests.get(f"https://my-ocular.jeffalo.net/api/user/{post['username']}").json()})
      if reactions:
        post.update({"reactions": requests.get(f"https://my-ocular.jeffalo.net/api/reactions/{post['id']}").json()})
      new.append(post)
    return new
  def projects(self, page = 0):
    return requests.get(f"https://api.scratch.mit.edu/users/{self.username}/projects?limit=20&offset={20 * page}").json()
  def favorites(self, page = 0):
    return requests.get(f"https://api.scratch.mit.edu/users/{self.username}/favorites?limit=20&offset={20 * page}").json()
  def curating(self, page = 0):
    return requests.get(f"https://api.scratch.mit.edu/users/{self.username}/studios/curate?limit=20&offset={20 * page}").json()
  def forum(self):
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/user/info/{self.username}").json()
  def forum_signiture_history(self):
    data = requests.get(f"https://scratchdb.lefty.one/v3/forum/user/history/{self.username}").json()
    new = []
    for item in data:
      item["time_found"] = get_time(item["time_found"])
      new.append(item)
    new.insert(0, {'change': 'signature', 'previous_value': self.forum()['signature'], 'time_found': "Now"})
    if new[0]["previous_value"] == None:
      new[0]["previous_value"] = "None"
    return new
  def forum_post_history(self):
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/user/graph/{self.username}/total?segment=1&range=100000").json()
  def featured(self):
    return requests.get(f"https://scratch.mit.edu/site-api/users/all/{self.username}/").json()
  def ocular(self):
    return requests.get(f"https://my-ocular.jeffalo.net/api/user/{self.username}").json()
  def comments(self):
    return []
  def messages(self):
    headers = {"User-Agent": "Chrome"}
    return requests.get(f"https://api.scratch.mit.edu/users/{self.username}/messages/count", headers = headers).json()["count"]

class Project:
  def __init__(self, id = None, a = True):
    if id != None:
      self.id = id
      self.api = requests.get(f"https://api.scratch.mit.edu/projects/{id}").json()
      if a:
        if self.api["remix"]["root"] != None:
          self.api["remix"]["root"] = Project(self.api["remix"]["root"], False).api
          if self.api["remix"]["root"] != self.api["remix"]["parent"]:
            self.api["remix"]["parent"] = Project(self.api["remix"]["parent"], False).api
      self.db = requests.get(f"https://scratchdb.lefty.one/v3/project/info/{id}").json()
      if self.db == {"error":"post not found"}:
        self.db = {"statistics":{"ranks":{},"views":"Not found","loves":"Not found","favorites":"Not found","comments":"Not found"},"metadata":{"version":"Not found","costumes":"Not found","blocks":"Not found","variables":"Not found","assets":"Not found"}, "times": {"created": "Not found", "modified": "Not found", "shared": "Not found"}}
  def remixes(self, page = 0):
    data = requests.get(f"https://api.scratch.mit.edu/projects/{self.id}/remixes?limit=20&offset={20 * page}").json()
    if type(data) == dict:
      data = [data]
    return data
  def comments(self, page = 0, reactions = False):
    data = requests.get(f"https://api.scratch.mit.edu/users/{self.api['author']['username']}/projects/{self.id}/comments").json()
    new = []
    for comment in data:
      comment.update({"reactions": []})
      new.append(comment)
    return new
  def studios(self, page = 0):
    return []
  def search(self, query, mode = "trending"):
    return requests.get(f"https://api.scratch.mit.edu/search/projects/?mode={mode}&q={query}").json()

class Studio:
  def __init__(self, id = None):
    if id != None:
      self.id = id
      self.api = requests.get(f"https://api.scratch.mit.edu/studios/{id}").json()
      self.api.update({"host": self.managers()[0]})
  def projects(self, page = 0):
    return requests.get(f"https://api.scratch.mit.edu/studios/{self.id}/projects").json()
  def comments(self, page = 0, reactions = False):
    data = requests.get(f"https://api.scratch.mit.edu/studios/{self.id}/comments").json()
    new = []
    for comment in data:
      comment.update({"reactions": []})
      new.append(comment)
    return new
  def managers(self, page = 0):
    return requests.get(f"https://api.scratch.mit.edu/studios/{self.id}/managers").json()
  def curators(self, page = 0):
    return requests.get(f"https://api.scratch.mit.edu/studios/{self.id}/curators").json()
  def activity(self, page = 0):
    return requests.get(f"https://api.scratch.mit.edu/studios/{self.id}/activity").json()
  def search(self, query, mode = "trending"):
    return requests.get(f"https://api.scratch.mit.edu/search/studios/?mode={mode}&q={query}").json()

class Forum:
  def __init__(self):
    self.categories = {5: "Announcements", 6: "New Scratchers", 7: "Help With Scripts", 8: "Show and Tell", 9: "Project Ideas", 10: "Collaboration", 11: "Requests", 4: "Questions about Scratch", 1: "Suggestions", 3: "Bugs and Glitches", 31: "Advanced Topics", 32: "Connecting to the Physical World", 48: "Developing Scratch Extensions", 49: "Open Source Projects", 29: "Things I'm Making and Creating", 30: "Things I'm Reading and Playing"}
  def leaderboard(self, category = "total", page = 0):
    if category != "total":
      category = self.categories[int(category)]
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/category/rank/{category}/{page}").json()
  def topics(self, category, page = 0, detail = 2):
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/category/topics/{self.categories[int(category)]}/{page}?detail={detail}").json()
  def topic(self, id):
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/topic/info/{id}").json()
  def topic_posts(self, id, page = 0, order = "oldest", reactions = False):
    data = requests.get(f"https://scratchdb.lefty.one/v3/forum/topic/posts/{id}/{page}?o={order}").json()
    new = []
    for post in data:
      post.update({"ocular": requests.get(f"https://my-ocular.jeffalo.net/api/user/{post['username']}").json()})
      if reactions:
        post.update({"reactions": requests.get(f"https://my-ocular.jeffalo.net/api/reactions/{post['id']}").json()})
      new.append(post)
    return new
  def post(self, id):
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/post/info/{id}").json()
  def search(self, query, order = "relavent", page = 0):
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/search?q={query}&o={order}&page={page}").json()["posts"]

class Scratch:
  def featured():
    data = requests.get("https://api.scratch.mit.edu/proxy/featured").json()
    data.update({"turbowarp": Studio(27205657).projects()})
    return data
  def explore(self, type = "projects", page = 0, mode = "trending"):
    return requests.get(f"https://api.scratch.mit.edu/explore/{type}?limit=20&offset={page * 20}&language=en&mode={mode}").json()
  def news(page = 0):
    return requests.get(f"https://api.scratch.mit.edu/news?offset={page * 20}").json()
