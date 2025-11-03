[app]
# (str) Title of your application
title = Minefut

# (str) Package name
package.name = minefut

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,jpeg,gif,svg,json,txt,md,ttf,wav,ogg,mp3

# (str) Application versioning
version = 0.1

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,pygame

# (str) Custom orientation
# Supported values are: landscape, portrait, all
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (int) The Android API level to use
android.api = 31

# (str) The Android NDK version to use
android.ndk = 25b

[buildozer]

# (int) Log level (0 = error, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) The Android command-line tools version to use
android.cmdline_tools_version = 8512546
