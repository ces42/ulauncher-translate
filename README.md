# Ulauncher - Translate  (Updated, Forked)

This is a fork of [manahter's translation plugin](https://github.com/manahter/ulauncher-translate) for Ulauncher, rewritten to use [`py-googletrans`](https://github.com/ssut/py-googletrans/) as backend (this should be slightly faster) and with some other modifications

## Preview

![Preview](prev.gif)

## Requirements

* [Ulauncher](https://github.com/Ulauncher/Ulauncher) 5.0+

## Install

Open ulauncher preferences window -> extensions -> add extension and paste the following url:

```
https://github.com/manahter/ulauncher-translate
```

## Usage

ç : Translate Keyword
* > ç  from_lang:to_lang  some_text
* > ç Hello
* > ç :tr Hello
* > ç en:ru Hello
```
```
## Prefrences

* **Ceviri** - Main extension keyword. You can change.
* **Text Wrapping** - Count of letters in line. ( for multi-line translations )
* **Native Language** - Your language.
* **Other Language** - Translation language. ( Auto is preferred )
![Preferences](prefs.gif)

## Links

* [Language Keywords List](https://cloud.google.com/translate/docs/languages)
* [Ulauncher Extensions](https://ext.ulauncher.io/)
* [Ulauncher 5.0 (Extension API v2.0.0) — Ulauncher 5.0.0 documentation](http://docs.ulauncher.io/en/latest/)
