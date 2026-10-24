[app]
title = FolyanApp
package.name = folyanapp
package.domain = org.folyan

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 0.1

requirements = python3,kivy,kivymd==2.0.0,pillow,materialyoucolor>=3.0.3,asynckivy

orientation = portrait
fullscreen = 0
android.api = 34
android.minapi = 24
android.ndk = 25b

android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 0
warn_on_root = 0
