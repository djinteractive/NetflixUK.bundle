import cgi, urllib
import webbrowser
from account import Account

SEARCH_URL      = "http://api.djinteractive.co.uk/netflix/search/%s"
MOVIE_URL       = "http://api.djinteractive.co.uk/netflix/movies/%s"
TV_URL          = "http://api.djinteractive.co.uk/netflix/tv/%s"
GENRE_URL       = "http://api.djinteractive.co.uk/netflix/genres/%s"
POSTER_URL      = "http://static.djinteractive.co.uk/img/posters/200/%s.200.jpg"

PLAYER_URL      = "http://www.netflix.com/WiPlayer?movieid=%s"

###################################################################################################

def MainMenu():
  # Attempt to log in
  logged_in = Account.LoggedIn()
  if not logged_in:
    logged_in = Account.TryLogIn()

  oc = ObjectContainer(no_cache = True, title1 = "Netflix UK")

  if logged_in:

    # Search
    oc.add(InputDirectoryObject(key = Callback(Search), title = "Search", prompt = "Search for a Movie or TV Show..."))

    # Recently Added Movies
    oc.add(DirectoryObject(key = Callback(MenuItem, url = MOVIE_URL % "recent", title = "Recently Added Movies", content = ContainerContent.Movies), title = "Recently Added Movies", thumb = R("nfx_new.png")))

    # Recently Added TV
    oc.add(DirectoryObject(key = Callback(MenuItem, url = TV_URL % "recent", title = "Recent Added TV Programmes", content = ContainerContent.Shows), title = "Recent Added TV Programmes", thumb = R("nfx_new.png")))

    # List Genres
    data = JSON.ObjectFromURL( GENRE_URL % "" )
    if data["status"]["code"] == 200:
      for item in data["results"]:
        url = GENRE_URL % item["id"]
        title = item["genre"]
        thumb = "nfx_genre_%s.png" % item["id"]
        oc.add(DirectoryObject(key = Callback(MenuItem, url = url, title = title, content = ContainerContent.Mixed), title = title, thumb = R(thumb)))

  else:

    # The user has not yet provided valid credentials. Therefore, we should allow them to be redirected
    # to sign up for a free trial.
    if Client.Platform in ("MacOSX", "Windows"):
      oc.add(DirectoryObject(key = Callback(FreeTrial), title = "Sign up for free trial"))

  oc.add(PrefsObject(title = "Preferences", thumb = R("nfx_preferences.png")))

  return oc

###################################################################################################

@route("/video/netflixuk/uk/search")
def Search(query):
  return MenuItem(url = SEARCH_URL % urllib.quote_plus(query), title = query, content = ContainerContent.Mixed)

###################################################################################################

@route("/video/netflixuk/uk/freetrial")
def FreeTrial():
  url = "http://www.netflix.com/"
  webbrowser.open(url, new=1, autoraise=True)
  return ObjectContainer(header="Free Trial Signup", message="A browser has been opened so that you may sign up for a free trial. If you do not have a mouse and keyboard handy, visit http://www.netflix.com and sign up for free today!")

###################################################################################################

@route("/video/netflixuk/uk/menuitem")
def MenuItem(url, title, type = "Mixed", content = ContainerContent.Mixed):
  oc = ObjectContainer(title2 = title, content = content)

  # Load JSON from URL
  try:
    data = JSON.ObjectFromURL( url )
  except Ex.HTTPError, e:
    Log( "Error loading url : %s %s" % (e.code, url) )
    return ObjectContainer(header="No Results", message="No results were found")

  # Display movie listings
  if type == "Episodes":
    if "episodes" in data and data["episodes"]:
      oc.add(EpisodeObject(
        key = Callback(Lookup, id = data["id"]),
        items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, id = data["id"]))], protocol = "webkit") ],
        rating_key = data["id"],
        title = "Resume",
        show = data["name"],
        thumb = POSTER_URL % data["imdb"],
        summary = data["overview"],
        duration = data["runtime"] * 60 * 1000,
        rating = float(data["rating"])/10,
        content_rating = data["classification"]))
      for item in data["episodes"]:
        episode_name = str(item["season"]) + "x" + str(item["episode"]).zfill(2) + " " + item["name"]
        oc.add(EpisodeObject(
          key = Callback(Lookup, id = item["id"]),
          items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, id = item["id"]))], protocol = "webkit") ],
          rating_key = item["id"],
          title = episode_name,
          show = data["name"],
          season = item["season"],
          index = item["episode"],
          thumb = item["image"],
          summary = item["overview"],
          duration = item["runtime"] * 60 * 1000,
          rating = float(data["rating"])/10,
          content_rating = data["classification"]))
    else:
      # Handle one off TV Programmes that have no individual episodes
      oc.add(EpisodeObject(
        key = Callback(Lookup, id = data["id"]),
        items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, id = data["id"]))], protocol = "webkit") ],
        rating_key = data["id"],
        title = data["name"],
        show = data["name"],
        season = 0,
        index = 0,
        thumb = POSTER_URL % data["imdb"],
        summary = data["overview"],
        duration = data["runtime"] * 60 * 1000,
        rating = float(data["rating"])/10,
        content_rating = data["classification"]))
  elif "results" in data and data["results"]:
    for item in data["results"]:
      studios = ""
      if item["studios"]:
        i = 0
        for studio in JSON.ObjectFromString(item["studios"]):
          if i>0:
            studio += ", "
          studios += studio
          i += 1
      if item["tv"]:
        oc.add(TVShowObject(
          key = Callback(MenuItem, url = TV_URL % item["id"], title = item["name"], type = "Episodes", content = ContainerContent.Episodes),
          rating_key = item["id"],
          title = item["name"],
          thumb = POSTER_URL % item["imdb"],
          summary = item["overview"],
          duration = item["runtime"] * 60 * 1000,
          studio = studios,
          rating = float(item["rating"])/10,
          content_rating = item["classification"]))
      else:
        oc.add(MovieObject(
          key = Callback(Lookup, id = item["id"]),
          items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, id = item["id"]))], protocol = "webkit") ],
          rating_key = item["id"],
          title = item["name"],
          thumb = POSTER_URL % item["imdb"],
          summary = item["overview"],
          year = item["year"],
          duration = item["runtime"] * 60 * 1000,
          studio = studios,
          rating = float(item["rating"])/10,
          content_rating = item["classification"]))

  # Check to see if we have any results
  if len(oc) == 0:
    return ObjectContainer(header="No Results", message="No results were found")

  return oc

###################################################################################################

@route("/video/netflixuk/uk/lookup")
def Lookup(id):
  Log("Lookup " + id)
  return ObjectContainer(header="Lookup Unavailable", message="This class has been depreciated")

###################################################################################################

@route("/video/netflixuk/uk/playvideo")
@indirect
def PlayVideo(id):
  oc = ObjectContainer()

  user_url = "http://api-public.netflix.com/users/%s" % Account.GetUserId()
  params = {"movieid": id, "user": user_url}
  video_url = Account.GetAPIURL(PLAYER_URL % id, params = params)

  # If the &resume=true parameter was specified, ensure that it"s copied to the final webkit URL
  if Prefs["playbackpreference"] == "Resume":
    video_url = video_url + "&resume=true"
  Log("Final WebKit URL: " + video_url)

  oc.add(VideoClipObject(
    key = Callback(Lookup, id = id),
    rating_key = id,
    items = [
      MediaObject(
        parts = [PartObject(key = WebVideoURL(video_url))],
        protocol = "webkit")
    ]
  ))

  return oc
