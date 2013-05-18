import re
import UK

TITLE = "Netflix UK"
ART = "nfx_wall.jpg"
ICON = "nfx_icon.png"
THUMB = "nfx_default.png"

HTTP.Headers["Accept-Encoding"] = "gzip,sdch"
###################################################################################################

def Start():

  ObjectContainer.art = R(ART)
  ObjectContainer.title1 = R(TITLE)

  DirectoryObject.thumb = R(THUMB)
  InputDirectoryObject.thumb = R("nfx_search.png")
  PrefsObject.thumb = R("nfx_preferences.png")

###################################################################################################

@handler("/video/netflixuk", TITLE, ICON, ART)
def Menu():

  # Verify that Silverlight is currently installed.
  if Platform.HasSilverlight == False:
    return ObjectContainer(header="Error", message="Silverlight is required for the Netflix plug-in. On your Plex Media Server please visit http://silverlight.net to install.")

  return Main().MainMenu()

###################################################################################################

def Main():
  return UK


# Neflix UK
# Based on the original Netflix plugin for Plex
# Uses icons from GemIcon http://gemicon.net/