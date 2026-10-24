[app]
title = FolyanApp
package.name = folyanapp
package.domain = org.folyan

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf,json,txt

version = 0.3.1

requirements = python3,kivy,materialyoucolor,pillow,exceptiongroup,asyncgui,asynckivy,filetype,materialshapes

orientation = portrait
fullscreen = 0
android.api = 34
android.minapi = 24
android.ndk = 28c
icon.filename = %(source.dir)s/icon.png
p4a.branch = v2026.05.09
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 0
warn_on_root = 0
