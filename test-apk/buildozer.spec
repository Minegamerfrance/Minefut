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
exclude_patterns = __pycache__ , *.pyc , *.pyo , *.orig , *.bak , .git , .github , */.DS_Store , Thumbs.db

# Python-for-Android requirements
requirements = python3, pygame

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

[buildozer]
log_level = 2
android.accept_sdk_license = True
