# NetflixUK.bundle
A channel plugin for [Plex Media Server](http://www.plexapp.com).

## Install
Download and copy the bundle into your Plex Media Server plugin folder. That's it.
On the Mac it's located at
````
~/Library/Application Support/Plex Media Server/Plug-ins/
````

## API
I've built up a custom API specifically for the UK version of Netflix and it's available at [api.djinteractive.co.uk/netflix/](http://api.djinteractive.co.uk/netflix). The data is currently sourced from TheTVDB and TheMovieDB with Freebase providing the IMDB id's that are used as the primary link between the services. I'll add more documentation on the API soon.

## Notes
Whilst most of the show information is accurate there may a couple instances where this is not the case. I'm currrently working on a frontend to flag these issues and deal with any inconsistances.

## Thanks
[Plex Team](https://github.com/plexinc-plugins/Netflix.bundle) - Original Netflix plugin on which this is based