# Utilized resources
# https://github.com/YogurtTheHorse/ulauncher-translator
# https://github.com/mouuff/mtranslate
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
import textwrap
import sys
import re
from googletrans import Translator

import time # todo: remove

AGENT =  "Mozilla/5.0 (Android 9; Mobile; rv:67.0.3) Gecko/67.0.3 Firefox/67.0.3"


class TranslateExtension(Extension):
    translator: Translator

    def __init__(self):
        super(TranslateExtension, self).__init__()
        self.translator = Translator(user_agent=AGENT)
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener(self.translate))
    
    def translate(self, query, to_language="auto", from_language="auto"):
        result = self.translator.translate(query, src=from_language, dest=to_language)
        # res_text, orig, to = result.text, result.src, result.dest
        # return res_text, orig, to
        return result.text, result.src, result.dest, result.pronunciation


class KeywordQueryEventListener(EventListener):
    def __init__(self, tr_func):
        self.tr_func = tr_func

    def on_event(self, event, extension):
        query = event.get_argument() or str()
        
        if len(query.strip()) == 0:
            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                    name='No input',
                                    on_enter=HideWindowAction())
            ])
        
        if len(query)>3 and ":" in query[0]:
            from_language = "auto"
            to_language = query[1:3]
            query = query[3:].strip()
        elif len(query)>5 and ":" in query[2]:
            from_language = query[:2]
            to_language = query[3:5]
            query = query[5:].strip()
        else:
            from_language = extension.preferences["otherlang"]
            to_language = extension.preferences["mainlang"]
        
        if to_language == 'zh':
            to_language = 'zh-CN'

        result, orig, to, pronunc = self.tr_func(query, to_language, from_language)
        try:
            wrap_len = int(extension.preferences['wrap'])
        except ValueError:
            wrap_len = 80
        
        if pronunc and pronunc != result and len(pronunc) + len(result) + 4 <= wrap_len:
            res_text = f'{result}  "{pronunc}"'
        else:
            res_text = '\n'.join(textwrap.wrap(result, wrap_len))
        
        items = [
            ExtensionResultItem(icon='images/icon.png',
                                name=query.replace("\n","") + f'  [{orig} → {to}]',
                                description=res_text,
                                on_enter=CopyToClipboardAction(result))
        ]

        return RenderResultListAction(items)


if __name__ == '__main__':
    TranslateExtension().run()
