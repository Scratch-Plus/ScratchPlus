import requests, json, re, datetime, os
from PIL import Image

def get_time(TZ):
  now = datetime.datetime.now()
  TZ = TZ.split("T")
  TZ[0] = TZ[0].split("-")
  TZ[1] = TZ[1].split(":")[:-1]
  TZ = [[int(s) for s in sl] for sl in TZ]
  TZ = datetime.datetime(*TZ[0], *TZ[1])
  dif = str(now - TZ)
  if "day" in dif:
    dif = float(dif[:dif.index("day")])
    if dif >= 30.437:
      dif /= 30.437
      if dif >= 12:
        dif /= 12
        dif = int(dif)
        if dif == 1:
          dif = "1 year ago"
        else:
          dif = str(dif) + " years ago"
      else:
        dif = int(dif)
        if dif == 1:
          dif = "1 month ago"
        else:
          dif = str(dif) + " months ago"
    else:
      if dif == 1:
        dif = "1 day ago"
      else:
        dif = str(int(dif)) + " days ago"
  else:
    dif = dif.split(":")
    if dif[0] == "0":
      if dif[1] == "00":
        dif = str(int(float(dif[2]))) + " seconds ago"
      else:
        if dif[1] == "01":
          dif = "1 minute ago"
        dif = str(dif[1]) + " minutes ago"
    else:
      if dif[0] == "1":
        dif = "1 hour ago"
      else:
        dif = str(dif[0]) + " hours ago"
  return dif

def notification(json):
  types = {"comment": ["project", "profile", "studio"], "activity": ["loveproject", "favoriteproject", "followuser", "becomecurator"], "other": ["studioactivity", "remixproject", "curatorinvite", "userjoin", "becomeownerstudio", "forumpost", "followstudio", "shareproject"]}
  data = {"created": get_time(json["datetime_created"]), "type": json["type"], "actor": json["actor_username"], "actor_id": json["actor_id"]}
  if json["type"] == "addcomment":
    data.update({"comment_type": types["comment"][json["comment_type"]], "comment": json["comment_fragment"], "title": json["comment_obj_title"], "id": json["comment_obj_id"],"reply": json["commentee_username"]})
  elif json["type"] in types["activity"]:
    data.update({"actor": json["actor_username"]})
    if json["type"] == "followuser":
      data.update({"followed": json["followed_username"]})
    elif json["type"] == "becomecurator":
      data.update({"title": json["title"], "id": json["gallery_id"]})
    else:
      data.update({"id": json["project_id"]})
      if json["type"] == "loveproject":
        data.update({"title": json["title"]})
      else:
        data.update({"title": json["project_title"]})
  elif json["type"] in types["other"]:
    if json["type"] == "studioactivity":
      data.update({"title": json["title"], "id": json["gallery_id"]})
    elif json["type"] == "remixproject":
      data.update({"title": json["title"], "id": json["project_id"], "parent_title": json["parent_title"], "parent_id": json["parent_id"]})
    elif json["type"] == "curatorinvite":
      data.update({"title": json["title"], "id": json["gallery_id"]})
    elif json["type"] == "forumpost":
      data.update({"title": json["topic_title"], "id": json["topic_id"]})
    elif json["type"] == "becomeownerstudio":
      data.update({"title": json["gallery_title"], "id": json["gallery_id"]})
  else:
    print("Unknown message", json)
  return data
  
class Session:
  def __init__(self):
    self = self
  def login(self, username, password):
    self.username = username
    headers = {"x-csrftoken": "a","x-requested-with": "XMLHttpRequest","Cookie": "scratchcsrftoken=a;scratchlanguage=en;","referer": "https://scratch.mit.edu","user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"}
    data = json.dumps({"username": self.username, "password": password})
    request = requests.post("https://scratch.mit.edu/login/", data=data, headers=headers)
    try:
      self.session_id = re.search('"(.*)"', request.headers["Set-Cookie"]).group()
      self.token = request.json()[0]["token"]
    except AttributeError:
      return ""
    headers = {"x-requested-with": "XMLHttpRequest","Cookie": "scratchlanguage=en;permissions=%7B%7D;","referer": "https://scratch.mit.edu"}
    request = requests.get("https://scratch.mit.edu/csrf_token/", headers=headers)
    self.csrf_token = re.search("scratchcsrftoken=(.*?);", request.headers["Set-Cookie"]).group(1)
    self.data = {"username": self.username, "session_id": self.session_id, "token": self.token, "csrf_token": self.csrf_token}
    self.id = requests.get(f"https://api.scratch.mit.edu/users/{self.username}").json()["id"]
  def set(self, cookies):
    self.username = cookies.get("username")
    self.session_id = cookies.get("session_id")
    self.token = cookies.get("token")
    self.csrf_token = cookies.get("csrf_token")
    self.id = requests.get(f"https://api.scratch.mit.edu/users/{self.username}").json()["id"]
    if self.username != None:
      self.username = self.api(self.username)["username"]
  def new_messages(self, user = None):
    if user == None:
      user = self.username
    headers = {"User-Agent": "Chrome"}
    return requests.get(f"https://api.scratch.mit.edu/users/{user}/messages/count", headers = headers).json()["count"]
  def messages(self, limit = 40, offset = 0):
    headers = {"x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": "https://scratch.mit.edu"}
    messages = []
    o = 0
    while True:
      res = requests.get(f"https://api.scratch.mit.edu/users/{self.username}/messages?limit=40&offset={offset + o}",headers = headers).json()
      if type(res) == dict:
        return ([], [])
      messages += res
      if len(messages) >= limit or res == []:
        break
      o += 40
    messages = messages[:limit]
    return list(map(notification, messages))
  def link_name(self, name, comment = None):
    if comment == None:
      link =  f"https://scratch.mit.edu/users/{name}"
    else:
      link =  f"https://scratch.mit.edu/users/{name}/#comments-{comment}"
    return f"<a href='{link}'>{name}</a>"
  def link_project(self, project, name, comment = None):
    if comment == None:
      link = f"projects/{project}"
    else:
      link = f"/projects/{project}/#comments-{comment}"
    return f"<a href='{link}'>{name}</a>"
  def link_studio(self, studio, name):
    link = f"https://scratch.mit.edu/studios/{studio}"
    return f"<a href='{link}'>{name}</a>"
  def about(self):
    try:
      data = requests.get(f"https://scratchdb.lefty.one/v3/user/info/{self.username}").json()
      if data["country"] == "United States":
        data["country"] = "US"
      return data
    except:
      return ""
  def top(self, category, country):
    data = requests.get(f"https://scratchdb.lefty.one/v3/user/rank/{country}/{category}/0").json()
    users = []
    for user in data:
      name = user["username"]
      amount = user["statistics"][category]
      users.append({"username": self.link_name(name), "amount": amount})
    return users
  def posts(self, page = 0):
    try:
      data = requests.get(f"https://scratchdb.lefty.one/v3/forum/user/posts/{self.username}/{page}?o=newest").json()
      if data == {"error": "NoMorePostsError"}:
        return []
      else:
        posts = []
        for post in data:
          posts.append({"id": post["id"], "category": post["topic"]["category"], "title": post["topic"]["title"], "time": get_time(post["time"]["posted"]), "content": post["content"]["bb"]})
        return posts
    except:
      return []
  def unshared(self):
    headers = {"x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": "https://scratch.mit.edu"}
    text = requests.get("https://scratch.mit.edu/site-api/projects/notshared", headers=headers).text
    return text
  def set_country(self, country):
    headers = {"x-csrftoken": self.csrf_token, "x-requested-with": "XMLHttpRequest", "Cookie": f'scratchcsrftoken=a;scratchlanguage=en;scratchsessionsid={self.session_id};',"referer": f"https://scratch.mit.edu/;"}
    data = {"country": country, "csrfmiddlewaretoken": "a"}
    requests.post("https://scratch.mit.edu/accounts/settings/", headers = headers, data = data)
  def session(self):
    headers = {"x-csrftoken": self.csrf_token, "x-requested-with": "XMLHttpRequest", "Cookie": f'scratchcsrftoken=a;scratchlanguage=en;scratchsessionsid={self.session_id};',"referer": f"https://scratch.mit.edu/;"}
    return requests.get(f"https://scratch.mit.edu/session", headers = headers).text
  def api(self, user):
    data = requests.get(f"https://api.scratch.mit.edu/users/{user}").json()
    data["history"]["joined"] = get_time(data["history"]["joined"])
    data.update({"messages": self.new_messages(user)})
    return data
  def news(self):
    data = requests.get("https://api.scratch.mit.edu/news").json()
    return data
  def featured(self):
    return requests.get("https://api.scratch.mit.edu/proxy/featured").json()
  def project(self, id):
    api = requests.get(f"https://api.scratch.mit.edu/projects/{id}").json()
    if api["remix"]["root"] != None:
      api['remix']["root"] = self.project(api['remix']["root"])
      if api["remix"]["root"] != api["remix"]["parent"]:
        api['remix']["parent"] = self.project(api['remix']["parent"])
    return api
  def turbowarp_featured(self):
    return requests.get("https://api.scratch.mit.edu/studios/27205657/projects").json()
  def search(self, q):
    user = requests.get(f"https://api.scratch.mit.edu/users/{q}").json()
    projects = requests.get(f"https://api.scratch.mit.edu/search/projects/?mode=trending&q={q}").json()
    studios = requests.get(f"https://api.scratch.mit.edu/search/studios/?mode=trending&q={q}").json()
    forum = requests.get(f"https://scratchdb.lefty.one/v3/forum/search?q={q}&o=relevant&page=0").json()["posts"]
    return user, projects, studios, forum
  def project_comment(self, id, message):
    headers = {"x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": f"https://scratch.mit.edu/projects/{id}/","accept": "application/json","-Type": "application/json"}
    data = {"commentee_id": self.api()["id"],"content": message,"parent_id": 0}
    return requests.post(f"https://api.scratch.mit.edu/proxy/comments/project/{id}/",headers=headers,data=data)
  def statistics(self):
    return requests.get("https://scratch.mit.edu/statistics/data/daily").json()
  def wh(self):
    headers = {"x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": "https://scratch.mit.edu"}
    data = requests.get(f"https://api.scratch.mit.edu/users/{self.username}/following/users/activity", headers = headers).json()
    try:
      for event in range(len(data)):
        data[event]["datetime_created"] = get_time(data[event]["datetime_created"]) 
    except:
      pass
    return data
  def ascii(self, username):
    id = requests.get(f"https://api.scratch.mit.edu/users/{username}").json()["id"]
    img = requests.get(f"https://cdn2.scratch.mit.edu/get_image/user/{id}_90x90.png", stream = True).content
    open("user.png", "wb").write(img)
    img = Image.open("user.png")
    os.remove("user.png")
    width, height = img.size
    aspect_ratio = height/width
    new_width = 150
    new_height = aspect_ratio * new_width
    img = img.resize((new_width, int(new_height)))

    rgb = img.convert("RGB")

    imgl = img.convert('L')
    pixels = imgl.getdata()
    chars = ["B","S","#","&","@","$","%"]
    new_pixels = [chars[pixel//41] for pixel in pixels]
    new_pixels = ''.join(new_pixels)

    ascii_image = "<div style='letter-spacing:0; line-height:2px; white-space:pre; font-family: monospace; font-size:6px;'>"
    for index in range(0, len(new_pixels), new_width):
      row = new_pixels[index:index + new_width]
      for pixel in range(len(row)):
        ascii_image += f"<span style='color: rgb{rgb.getpixel((pixel, index / new_width))}'>{row[pixel]}</span>"
      ascii_image += "<br>\n"
    ascii_image += "</div>"
    return ascii_image
  def set_bio(self, content):
    headers = {"x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": f"https://scratch.mit.edu/users/{self.username}"}
    data = {"userId": self.id, "id": self.username, "username": self.username, "bio": content}
    requests.put(f"https://scratch.mit.edu/site-api/users/all/{self.username}/", headers = headers, data = data)
  def set_status(self, content):
    headers = {"x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": f"https://scratch.mit.edu/users/{self.username}"}
    data = {"userId": self.id, "id": self.username, "username": self.username, "status": content}
    requests.put(f"https://scratch.mit.edu/site-api/users/all/{self.username}/", headers = headers, data = data)
  '''These exist for some people...
  def following_projects(self):
    headers = {"x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": f"https://scratch.mit.edu/users/{self.username}"}
    projects = requests.get(f"https://api.scratch.mit.edu/users/{self.username}/following/users/projects", headers = headers).json()
    return projects
  def studio_following_projects(self):
    headers = {"x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": f"https://scratch.mit.edu/users/{self.username}"}
    projects = requests.get(f"https://api.scratch.mit.edu/users/{self.username}/following/studios/projects", headers = headers).json()
    return projects'''
  def following_loved(self):
    headers = {"x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": f"https://scratch.mit.edu/users/{self.username}"}
    projects = requests.get(f"https://api.scratch.mit.edu/users/{self.username}/following/users/loves", headers = headers).json()
    if type(projects) == dict:
      projects = []
    return projects
  def clear(self):
    headers = {"x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": f"https://scratch.mit.edu/users/{self.username}"}
    requests.post("https://scratch.mit.edu/site-api/messages/messages-clear/", headers = headers)
  def user_featured(self, user):
    data = requests.get(f"https://scratch.mit.edu/site-api/users/all/{user}/").json()
    return data
  def ocular(self, user):
    return requests.get(f"https://my-ocular.jeffalo.net/api/user/{user}").json()
  def love(self, value, id):
    headers = {"User-Agent": "Chrome", "x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": f"https://scratch.mit.edu/projects/{id}/"}
    if value:
      requests.post(f"https://api.scratch.mit.edu/proxy/projects/{id}/loves/user/{self.username}", headers = headers)
    else:
      requests.delete(f"https://api.scratch.mit.edu/proxy/projects/{id}/loves/user/{self.username}", headers = headers)
  def favorite(self, value, id):
    headers = {"User-Agent": "Chrome", "x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": f"https://scratch.mit.edu/projects/{id}/"}
    if value:
      requests.post(f"https://api.scratch.mit.edu/proxy/projects/{id}/favorites/user/{self.username}", headers = headers)
    else:
      requests.delete(f"https://api.scratch.mit.edu/proxy/projects/{id}/favorites/user/{self.username}", headers = headers)
  def loved(self, id, user):
    headers = {"x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": f"https://scratch.mit.edu/users/{self.username}"}
    return requests.get(f"https://api.scratch.mit.edu/projects/{id}/loves/user/{user}", headers = headers).json()
  def faved(self, id, user):
    headers = {"x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": f"https://scratch.mit.edu/users/{self.username}"}
    return requests.get(f"https://api.scratch.mit.edu/projects/{id}/favorites/user/{user}", headers = headers).json()
  def projects(self, user):
    return requests.get(f"https://api.scratch.mit.edu/users/{user}/projects").json()
  def favorites(self, user):
    data = requests.get(f"https://api.scratch.mit.edu/users/{user}/favorites").json()
    new = []
    for project in data:
      try:
        author = requests.get(f"https://api.scratch.mit.edu/projects/{project['id']}").json()["author"]["username"]
        project["author"].update({"username": author})
        new.append(project)
      except:
        pass
    return new
  def curating(self, user):
    return requests.get(f"https://api.scratch.mit.edu/users/{user}/studios/curate").json()
  def project_comments(self, id):
    owner = requests.get(f"https://api.scratch.mit.edu/projects/{id}").json()["author"]["username"]
    comments = requests.get(f"https://api.scratch.mit.edu/users/{owner}/projects/{id}/comments").json()
    new = []
    for comment in comments:
      comment.update({"replies": requests.get(f"https://api.scratch.mit.edu/users/{owner}/projects/{id}/comments/{comment['id']}/replies").json()})
      comment["datetime_created"] = get_time(comment["datetime_modified"])
      new.append(comment)
    return new
  def project_remixes(self, id):
    return requests.get(f"https://api.scratch.mit.edu/projects/{id}/remixes").json()
  def project_studios(self, id):
    return requests.get(f"https://api.scratch.mit.edu/projects/{id}/studios/?limit=40&offset=0").json()
  def studio_api(self, id):
    return requests.get(f"https://api.scratch.mit.edu/studios/{id}").json()
  def studio_projects(self, id):
    return requests.get(f"https://api.scratch.mit.edu/studios/{id}/projects").json()
  def studio_comments(self, id):
    data = requests.get(f"https://api.scratch.mit.edu/studios/{id}/comments").json()
    new = []
    for comment in data:
      comment.update({"replies": requests.get(f"https://api.scratch.mit.edu/studios/{id}/comments//{comment['id']}/replies").json()})
      comment["datetime_created"] = get_time(comment["datetime_modified"])
      new.append(comment)
    return new
  def studio_members(self, id):
    managers = requests.get(f"https://api.scratch.mit.edu/studios/{id}/managers").json()
    curators = requests.get(f"https://api.scratch.mit.edu/studios/{id}/curators").json()
    return {"curators": curators, "managers": managers}
  def studio_activity(self, id):
    data =  requests.get(f"https://api.scratch.mit.edu/studios/{id}/activity").json()
    new = []
    for event in data:
      event["datetime_created"] = get_time(event["datetime_created"])
      new.append(event)
    return new
  def category_topics(self, category):
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/category/topics/{category}/0?detail=2").json()
  def topic_leaderboard(self, category):
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/category/rank/{category}/0").json()
  def topic_posts(self, topic_id, page = 0, order = "newest", reactions = True):
    data = requests.get(f"https://scratchdb.lefty.one/v3/forum/topic/posts/{topic_id}/{page}?o={order}").json()
    if not "error" in data:
      if reactions:
        for post in range(len(data)):
          data[post].update({"ocular": self.ocular(data[post]["username"]), "reactions": self.post_reactions(data[post]["id"])})
      return data
    else:
      return []
  def topic_info(self, id):
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/topic/info/{id}").json()
  def post_reactions(self, post_id):
    return requests.get(f"https://my-ocular.jeffalo.net/api/reactions/{post_id}").json()
  def forum_leaderboard(self):
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/category/rank/total/0").json()
  def forum_user(self, username):
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/user/info/{username}").json()
  def forum_post_history(self, username):
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/user/graph/{username}/total?segment=1&range=100000").json()
  def forum_user_posts(self, username):
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/user/posts/{username}").json()
  def explore(self, type, page, mode):
    return requests.get(f"https://api.scratch.mit.edu/explore/{type}?limit=20&offset={int(page) * 20}&language=en&mode={mode}").json()
  def post_info(self, id):
    return requests.get(f"https://scratchdb.lefty.one/v3/forum/post/info/{id}").json()
  def studio_comment_reactions(self, id, page):
    data = requests.get(f"https://magnifier-api.potatophant.net/api/comments/studios/{id}/{page + 1}").json()
    reactions = []
    for comment in data:
      reactions.append(comment["reactions"])
    return reactions
  def project_comment_reactions(self, id, page):
    data = requests.get(f"https://magnifier-api.potatophant.net/api/comments/projects/{id}/{page + 1}").json()
    reactions = []
    for comment in data:
      reactions.append(comment["reactions"])
    return reactions
  def profile_comment_reactions(self, user, page):
    data = requests.get(f"https://magnifier-api.potatophant.net/api/comments/users/{user}/{page + 1}").json()
    reactions = []
    for comment in data:
      reactions.append(comment["reactions"])
    return reactions
  def forum_post(self, id, content):
    headers = {"content-type": "multipart/form-data", "authority": "scratch.mit.edu", "user-agent": "a", "x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": f"https://scratch.mit.edu/discuss/topic/{id}"}
    data = {
      "csrfmiddlewaretoken": self.csrf_token,
      "body": content
    }
    r = requests.post(f"https://scratch.mit.edu/discuss/topic/{id}/", data = data, headers = headers)
    print("\n\n\n")
    if "location" in r.headers:
      print(r.headers["location"])
    else:
      for header in r.headers:
        print(header, r.headers[header])
  def profile_comments(self, user):
    html = requests.get(f"https://scratch.mit.edu/site-api/comments/user/{user}").text
    #data = json.dumps(xmltojson.parse(html))
    return re.findall('<li class=\"top-level-reply\">.*?</li>', html)
  def user_followers(self, user):
    i = 0
    r = []
    users = []
    while len(r) > 0 or i == 0:
      r = requests.get(f"https://api.scratch.mit.edu/users/{user}/followers?offset={20 * i}").json()
      users += r
      i += 1
    return users
  def follow_topic(self, id):
    headers = {"x-csrftoken": self.csrf_token,"X-Token": self.token,"x-requested-with": "XMLHttpRequest","Cookie": f"scratchcsrftoken={self.csrf_token};scratchlanguage=en;scratchsessionsid={self.session_id};","referer": f"https://scratch.mit.edu/discuss/topic/{id}",}
    print(requests.post(f"http://scratch.mit.edu/discuss/subscription/topic/{id}/add", headers = headers).text)
