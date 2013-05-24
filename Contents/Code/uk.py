import cgi, urllib
import webbrowser
from account import Account

SEARCH_URL      = "http://api.djinteractive.co.uk/netflix/search/%s"
MOVIE_URL       = "http://api.djinteractive.co.uk/netflix/movies/%s"
TV_URL          = "http://api.djinteractive.co.uk/netflix/tv/%s"
GENRE_URL       = "http://api.djinteractive.co.uk/netflix/genres/%s"
POSTER_URL      = "http://static.djinteractive.co.uk/img/posters/200/%s.200.jpg"

PLAYER_URL      = "http://www.netflix.com/WiPlayer?movieid=%s"

MOVIE_PATTERN   = Regex("^http://(.)+\.netflix.com/catalog/titles/movies/[0-9]+$")
TVSHOW_PATTERN  = Regex("^http://(.)+\.netflix.com/catalog/titles/series/[0-9]+$")
SEASON_PATTERN  = Regex("^http://(.)+\.netflix.com/catalog/titles/series/[0-9]+/seasons/[0-9]+$")
EPISODE_PATTERN = Regex("^http://(.)+\.netflix.com/catalog/titles/programs/[0-9]+/[0-9]+")

EPISODE_TITLE_PATTERN = Regex("^S(?P<season>[0-9]+):E(?P<episode>[0-9]+) - (?P<title>.+)$")

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
def MenuItem(url, title, page = 1, interval = 50, type = "Mixed", content = ContainerContent.Mixed, is_queue = False):
  oc = ObjectContainer(title2 = title, content = content)

  # Separate out the specified parameters from the original URL
  params = {}
  if url.find("?") > -1:
    original_params = String.ParseQueryString(url[url.find("?") + 1:])
    for key, value in original_params.items():
  	 params[key] = value[0]

  # Add the paging parameters
  params["page"] = int(page)
  params["interval"] = int(interval)

  # Load JSON from URL
  try:
    data = JSON.ObjectFromURL( url )
  except Ex.HTTPError, e:
    Log( "Error loading url : %s %s" % (e.code, url) )
    return ObjectContainer(header="No Results", message="No results were found")

  if type == "Episodes":
    if "episodes" in data and data["episodes"]:
      video_url = PlaybackURL( PLAYER_URL % data["id"], Prefs["playbackpreference"] )
      oc.add(EpisodeObject(
        key = Callback(Lookup, type = "Movie", id = data["id"]),
        items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, type = "Movie", url = video_url, id = data["id"]))], protocol = "webkit") ],
        rating_key = data["id"],
        title = "Resume",
        show = data["name"],
        thumb = POSTER_URL % data["imdb"],
        summary = data["overview"],
        duration = data["runtime"] * 60 * 1000,
        rating = float(data["rating"])/10,
        content_rating = data["classification"]))
      for item in data["episodes"]:
        video_url = PlaybackURL( PLAYER_URL % item["id"], Prefs["playbackpreference"] )
        episode_name = str(item["season"]) + "x" + str(item["episode"]).zfill(2) + " " + item["name"]
        oc.add(EpisodeObject(
          key = Callback(Lookup, type = "Movie", id = item["id"]),
          items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, type = "Episode", url = video_url, id = item["id"]))], protocol = "webkit") ],
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
    else: # Handle one off TV Programmes that have no individual episodes
      video_url = PlaybackURL( PLAYER_URL % data["id"], Prefs["playbackpreference"] )
      oc.add(EpisodeObject(
        key = Callback(Lookup, type = "Movie", id = data["id"]),
        items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, type = "Episode", url = video_url, id = data["id"]))], protocol = "webkit") ],
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
  else:
    for item in data["results"]:
      video_url = PlaybackURL( PLAYER_URL % item["id"], Prefs["playbackpreference"] )
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
        item_type = "Movie"
        oc.add(MovieObject(
          key = Callback(Lookup, type = item_type, id = item["id"], item = item),
          items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, type = "Movie", url = video_url, id = item["id"]))], protocol = "webkit") ],
          rating_key = item["id"],
          title = item["name"],
          thumb = POSTER_URL % item["imdb"],
          summary = item["overview"],
          year = item["year"],
          duration = item["runtime"] * 60 * 1000,
          studio = studios,
          rating = float(item["rating"])/10,
          content_rating = item["classification"]))


  # Pagination disabled for the time being, let's see how it goes.
  # If there are further results, add an item to allow them to be browsed.
  #total_results = int(data["total"])
  #if total_results > 0:
  #  if total_results > (page * interval):
  #    oc.add(DirectoryObject(
  #      key = Callback(MenuItem, url = url, title = title, page = page * interval, interval = interval, content = content),
  #      title = "Next..."))

  # Check to see if we have any results
  if len(oc) == 0:
    return ObjectContainer(header="No Results", message="No results were found")

  return oc

###################################################################################################

def PlaybackURL(url, preference):
  if preference == "Resume":
    return url + "&resume=true"

  return url


###################################################################################################

def parseItemDetails(item):
  id = item["id"] or ""
  video_url = PLAYER_URL % id
  season_url = None
  episode_url = None
  title = item["name"] or ""
  show = None
  season_index = None
  episode_index = None
  episode_count = None
  summary = item["overview"] or ""
  duration = item["runtime"] * 60 * 1000 or None
  rating = float(item["rating"])/10 or None
  content_rating = item["classification"] or None
  directors = None
  genres = None
  artwork = POSTER_URL % item["imdb"]

  return {
    'id': id,
    'url': video_url,
    'season_url': season_url,
    'episode_url': episode_url,
    'title': title,
    'show': show,
    'season_index': season_index,
    'episode_index': episode_index,
    'episode_count': episode_count,
    'summary': summary,
    'duration': duration,
    'rating': rating,
    'content_rating': content_rating,
    'directors': directors,
    'genres': genres,
    'thumb': artwork}

###################################################################################################

@route("/video/netflixuk/uk/lookup")
def Lookup(type, id, item = None):
  oc = ObjectContainer()

  Log("Lookup " + type + ", "+ id)
  return ObjectContainer(header="Lookup Unavailable", message="This class has been depreciated")
  # Separate out the specified parameters from the original URL
  params = {}

  item_details = parseItemDetails(item)

  video_url = PlaybackURL(item_details["url"], Prefs["playbackpreference"])

  if type == "Movie":
    oc.add(MovieObject(
      key = Callback(Lookup, type = type, id = id),
      rating_key = id,
      items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, type = type, url = video_url, id = id))], protocol = "webkit") ],
      title = item_details["title"],
      thumb = item_details["thumb"][0],
      summary = item_details["summary"],
      genres = item_details["genres"],
      directors = item_details["directors"],
      duration = item_details["duration"],
      rating = item_details["rating"],
      content_rating = item_details["content_rating"]))
  else:
    oc.add(EpisodeObject(
      key = Callback(Lookup, type = type, id = id),
      rating_key = id,
      items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, type = type, url = video_url, id = id))], protocol = "webkit") ],
      title = item_details["title"],
      show = item_details["show"],
      season = item_details["season_index"],
      index = item_details["episode_index"],
      thumb = item_details["thumb"][0],
      summary = item_details["summary"],
      directors = item_details["directors"],
      duration = item_details["duration"],
      rating = item_details["rating"],
      content_rating = item_details["content_rating"]))

  return oc

###################################################################################################

@route("/video/netflixuk/uk/playvideo")
@indirect
def PlayVideo(type, url, id, indirect = None):
  oc = ObjectContainer()

  user_url = "http://api-public.netflix.com/users/%s" % Account.GetUserId()

  params = {"movieid": id, "user": user_url}
  video_url = Account.GetAPIURL(PLAYER_URL % id, params = params)

  # If the &resume=true parameter was specified, ensure that it"s copied to the final webkit URL
  if url.endswith("&resume=true"):
    video_url = video_url + "&resume=true"
  Log("Final WebKit URL: " + video_url)

  oc.add(VideoClipObject(
    key = Callback(Lookup, type = type, id = id),
    rating_key = id,
    items = [
      MediaObject(
        parts = [PartObject(key = WebVideoURL(video_url))],
        protocol = "webkit")
    ]
  ))

  return oc
