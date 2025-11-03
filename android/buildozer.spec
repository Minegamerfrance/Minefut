[app]
# Basic app identifiers
title = Minefut
package.name = minefut
package.domain = org.minefut

# Project location and entrypoint
source.dir = ..
entrypoint = main.py

# File types to include
source.include_exts = py,pyi,png,jpg,jpeg,gif,webp,svg,mp3,wav,ogg,ttf,otf,json,csv,ini,txt,md
exclude_patterns = __pycache__ , *.pyc , *.pyo , *.orig , *.bak , .git , .github , */.DS_Store , Thumbs.db , tools/** , test apk/** , cards/** , Fond/**

# Python-for-Android requirements
# Include pygame and common SDL2 add-ons used by pygame builds
# Keep it minimal for stability: pin target Python and pygame
requirements = python3==3.10.12, setuptools, pygame==2.5.2

# App settings
orientation = landscape
fullscreen = 1
version = 0.1.0
numeric_version = 1

# Android target
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.accept_sdk_license = True
android.build_tools_version = 33.0.2

# Pin the NDK API level commonly used with r25b
android.ndk_api = 21

# Use a recent python-for-android branch with pygame fixes
p4a.branch = develop

# Optional: icons/presplash if you have assets (uncomment and set correct paths)
# icon.filename = %(source.dir)s/assets/Profil/icon.png
# presplash.filename = %(source.dir)s/assets/Profil/presplash.png

[buildozer]
log_level = 2
android.accept_sdk_license = True
