[app]
title = FolyanApp
package.name = folyanapp
package.domain = org.folyan

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf,json,txt,glsl,md,po,pot
source.exclude_dirs = .git, .github, bin, venv, __pycache__
version = 0.6.1

requirements = python3,kivy,materialyoucolor==3.0.3,pillow,exceptiongroup,asyncgui,asynckivy,filetype,materialshapes,pycairo,pyjnius,yt-dlp,certifi,websockets
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE
android.add_libs_arm64_v8a = libs/arm64-v8a/*.so

orientation = portrait
fullscreen = 0
android.api = 34
android.minapi = 24
android.ndk = 28c
icon.filename = %(source.dir)s/icon.png
p4a.branch = v2026.05.09
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0
