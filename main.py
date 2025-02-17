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
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
import textwrap
import sys
import re
from googletrans import Translator
from httpx import RemoteProtocolError
import asyncio
from functools import lru_cache
from time import sleep

AGENT =  "Mozilla/5.0 (Android 9; Mobile; rv:67.0.3) Gecko/67.0.3 Firefox/67.0.3"
LANG_RE = r'([a-zA-Z-]{2,})?:([a-zA-Z]{2})?' 

FLAGS = {'en': '🇺🇸', 'de': '🇩🇪', 'es': '🇪🇸', 'zh-CN': '🇨🇳', 'fr': '🇫🇷', 'it': '🇮🇹'}


class TranslateExtension(Extension):
    translator: Translator

    def __init__(self):
        super(TranslateExtension, self).__init__()
        self.translator = Translator(user_agent=AGENT)
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener(self.translate_multi))

    async def async_translate(self, query, to_langs, from_language="auto"):
        def tr_task(query, to, from_language):
            return lambda: self.translate(query, to, from_language)

        loop = asyncio.get_running_loop()
        tasks = []
        for to in to_langs:
            tasks.append(loop.run_in_executor(None, tr_task(query, to, from_language)))

        return await asyncio.gather(*tasks)

    @lru_cache(10_000)
    def translate(self, query, to_language, from_language="auto"): 
        try:
            res = self.translator.translate(query, src=from_language, dest=to_language)
        except ValueError as e:
            match str(e):
                case 'invalid destination language':
                    e.lang = to_language
                case 'invalid source language':
                    e.lang = from_language
            raise e

        if res.src == res.dest:
            return []
        ret = [(res.text, lang(res.src), lang(res.dest), res.pronunciation)]
        try:
            all_tr = res.extra_data['possible-translations']
            for x, *_ in all_tr[0][2]:
                if x != res.text:
                    ret.append((x, res.src, res.dest, None))
        except (TypeError, IndexError) as e:
            print(f"silencing error: {e}")
            pass
        return ret

    def translate_multi(self, query, to_langs, from_language="auto"):
        if from_language in to_langs and len(to_langs) > 1:
            to_langs.remove(from_language)

        results = asyncio.run(self.async_translate(query, to_langs, from_language))

        yield from (res[0] for res in results if res)
        for res in results:
            yield from res[1:]

def format_query(query, orig, to):
    return query.replace("\n","") + f'  [{orig + FLAGS.get(orig, "")} → {to + FLAGS.get(to, "")}]'


def lang(s):
    l = s.split('-')
    if len(l) != 2:
        if s == 'zh':
            return 'zh-CN'
        else:
            return s.lower()
    else:
        return f'{l[0].lower()}-{l[1].upper()}'

class KeywordQueryEventListener(EventListener):
    def __init__(self, tr_func):
        self.tr_func = tr_func

    def on_event(self, event, extension):
        tr_func = self.tr_func
        query = event.get_argument() or str()
        
        if len(query.strip()) == 0:
            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                    name='No input',
                                    on_enter=HideWindowAction())
            ])
        
        if m := re.search(LANG_RE + '$', query) or re.match(LANG_RE, query):
            from_language = m.group(1) or 'auto'
            to_langs= [m.group(2)] if m.group(2) else extension.preferences["mainlang"].split(',')
            if m.start():
                query = query[:m.start()].strip()
            else:
                query = query[m.end():].strip()
        else:
            from_language = extension.preferences["otherlang"]
            to_langs = extension.preferences["mainlang"].split(',')

        to_langs = [lang(l) for l in to_langs]
        from_language = lang(from_language)

        if len(to_langs) == 1:
            to_langs = to_langs[0]
            tr_func = extension.translate

        try:
            # tr_list = list(tr_func(query, to_langs, from_language))
            tr_list = []
            iterator = iter(tr_func(query, to_langs, from_language))
            for _ in range(100):
                try:
                    translation = next(iterator)
                except StopIteration:
                    break
                except RemoteProtocolError as e:
                    # return RenderResultListAction([
                    #     ExtensionResultItem(icon='images/icon.png',
                    #                         name=query,
                    #                         description=f"http error: {e}",
                    #                         on_enter=HideWindowAction())
                    # ])
                    print('encountered RemoteProtocolError, retrying in 10ms')
                    sleep(0.01)
                    iterator = iter(tr_func(query, to_langs, from_language))
                    continue
                tr_list.append(translation)

        except ValueError as e:
            if hasattr(e, 'lang'):
                return RenderResultListAction([
                    ExtensionResultItem(icon='images/icon.png',
                                        name=query,
                                        description=f"{e} '{e.lang}'",
                                        on_enter=HideWindowAction())
                ])
            else:
                raise e

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
                ExtensionResultItem(
                    icon='images/icon.png',
                    name=format_query(query, orig, to),
                    description=res_text,
                    on_enter=OpenUrlAction(f'https://translate.google.com/?sl={orig}&tl={to}&text={query}&op=translate'),
                    on_alt_enter=CopyToClipboardAction(result)
                )
            )

        return RenderResultListAction(items)


if __name__ == '__main__':
    TranslateExtension().run()
