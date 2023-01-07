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
from googletrans import Translator, models

AGENT =  "Mozilla/5.0 (Android 9; Mobile; rv:67.0.3) Gecko/67.0.3 Firefox/67.0.3"
LANG_RE = '([a-zA-Z]{2})?:([a-zA-Z]{2})?' 

FLAGS = {'en': '🇺🇸', 'de': '🇩🇪', 'es': '🇪🇸', 'zh-cn': '🇨🇳', 'fr': '🇫🇷'}


class TranslateExtension(Extension):
    translator: Translator

    def __init__(self):
        super(TranslateExtension, self).__init__()
        self.translator = Translator(user_agent=AGENT)
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener(self.translate))
    
    def translate(self, query, to_list, from_language="auto"):
        if from_language in to_list and len(to_list) > 1:
            to_list.remove(from_language)

        results = [self.translator.translate(query, src=from_language, dest=to_language) for to_language in to_list]
        results = list(filter(lambda res: res.src != res.dest, results))

        yield from ((res.text, res.src, res.dest, res.pronunciation) for res in results)

        for res in results:
            try:
                all_tr = res.extra_data['possible-translations']
                for x, *_ in all_tr[0][2]:
                    if x != res.text:
                        yield x, res.src, res.dest, None
            except (TypeError, IndexError) as e:
                print(f"silencing error: {e}")
                pass
        # return text, result[0].src, result.dest, [res.pronunciation for res in results] + [None] * (len(text) - 1)

#     def translate(self, query, to_list, from_language="auto"):
#         if len(to_list) > 1:
#             to_list.remove(from_language)
#         results = [self.translator.translate(query, src=from_language, dest=to_language) for to_language in to_list]
#         text = [res.text for res in results]
#         for res in results:
#             try:
#                 all_tr = res.extra_data['possible-translations']
#                 for x, *_ in all_tr[0][2]:
#                     if x != text[0]:
#                         text.append(x)
#             except (TypeError, IndexError):
#                 pass
#         return text, result[0].src, result.dest, [res.pronunciation for res in results] + [None] * (len(text) - 1)


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
            to_langs= [m.group(2) or extension.preferences["mainlang"]]
            if m.start():
                query = query[:m.start()].strip()
            else:
                query = query[m.end():].strip()
        else:
            from_language = extension.preferences["otherlang"]
            to_langs = extension.preferences["mainlang"].split(',')

        if 'zh' in to_langs:
            to_langs[to_langs.index('zh')] = 'zh-cn'

        try:
            tr_list = list(self.tr_func(query, to_langs, from_language))
        except ValueError as e:
            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                    name=query,
                                    description=str(e),
                                    on_enter=HideWindowAction())
            ])

        try:
            wrap_len = int(extension.preferences['wrap'])
        except ValueError:
            wrap_len = 80
        
        items = []
        for result, orig, to, pronunc in tr_list:
            if isinstance(pronunc, str) and pronunc != result and pronunc != query and len(pronunc + result) + 4 <= wrap_len:
                res_text = f'{result}  "{pronunc}"'
            else:
                res_text = '\n'.join(textwrap.wrap(result, wrap_len))
            
            items.append(
                ExtensionResultItem(icon='images/icon.png',
                                    name=query.replace("\n","") + f'  [{orig + FLAGS.get(orig, "")} → {to + FLAGS.get(to, "")}]',
                                    description=res_text,
                                    on_enter=CopyToClipboardAction(result))
            )

        return RenderResultListAction(items)


if __name__ == '__main__':
    TranslateExtension().run()
