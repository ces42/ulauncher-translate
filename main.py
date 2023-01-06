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

AGENT =  "Mozilla/5.0 (Android 9; Mobile; rv:67.0.3) Gecko/67.0.3 Firefox/67.0.3"
LANG_RE = '([a-zA-Z]{2})?:([a-zA-Z]{2})?' 


class TranslateExtension(Extension):
    translator: Translator

    def __init__(self):
        super(TranslateExtension, self).__init__()
        self.translator = Translator(user_agent=AGENT)
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener(self.translate))
    
    def translate(self, query, to_language="auto", from_language="auto"):
        result = self.translator.translate(query, src=from_language, dest=to_language)
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
        
        if m := re.search(LANG_RE + '$', query) or re.match(LANG_RE, query):
            from_language = m.group(1) or 'auto'
            to_language = m.group(2) or 'auto'
            if m.start():
                query = query[:m.start()].strip()
            else:
                query = query[m.end():].strip()
        else:
            from_language = extension.preferences["otherlang"]
            to_language = extension.preferences["mainlang"]

        if to_language == 'zh':
            to_language = 'zh-cn'

        result, orig, to, pronunc = self.tr_func(query, to_language, from_language)
        try:
            wrap_len = int(extension.preferences['wrap'])
        except ValueError:
            wrap_len = 80
        
        if pronunc not in {None, result, query} and len(pronunc + result) + 4 <= wrap_len:
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
