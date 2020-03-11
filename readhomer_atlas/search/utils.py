from collections import defaultdict

import regex


w = r"\w[-\w]*"
p = r"\p{P}+"
ws = r"[\p{Z}\s]+"
token_re = regex.compile(fr"{w}|{p}|{ws}")
w_re = regex.compile(w)
p_re = regex.compile(p)
ws_re = regex.compile(ws)


def tokenize(content, words=True, punctuation=True, whitespace=True):
    tokens = []
    idx = defaultdict(int)
    offset = 0
    for w in token_re.findall(content):
        if w:
            wl = len(w)
            if w_re.match(w):
                offset += wl
                if not words:
                    continue
                t = "w"
            if p_re.match(w):
                offset += wl
                if not punctuation:
                    continue
                t = "p"
            if ws_re.match(w):
                if not whitespace:
                    continue
                t = "s"
            for wk in (w[i : j + 1] for i in range(wl) for j in range(i, wl)):
                idx[wk] += 1
            token = {"w": w, "i": idx[w], "t": t, "o": offset}
            tokens.append(token)
    return tokens


class Passage:
    def __init__(self, urn, content):
        self.urn = urn
        self.content = content

    def tokenize(self, **kwargs):
        return tokenize(self.content, **kwargs)


class Highlighter:
    w_re = regex.compile(fr"(?:<em>)?(?:\w[-\w]*|{chr(0xfffd)})(?:</em>)?")

    def __init__(self, passage, highlights):
        self.passage = passage
        self.highlights = highlights

    def tokens(self):
        if not hasattr(self, "_tokens"):
            acc = set()
            it = list(
                zip(
                    self.highlights.split(" "),
                    [(t["w"], t["i"]) for t in self.passage.tokenize(whitespace=False)],
                )
            )
            for hw, (sw, si) in it:
                if hw:
                    if self.w_re.match(hw):
                        if "<em>" in hw:
                            acc.add((sw, si))
            self._tokens = acc
        return self._tokens

    def content(self):
        if not hasattr(self, "_content"):
            acc = []
            highlighted_tokens = self.tokens()
            for token in self.passage.tokenize():
                if (token["w"], token["i"]) in highlighted_tokens:
                    acc.extend(["<em>", token["w"], "</em>"])
                else:
                    acc.append(token["w"])
            self._content = "".join(acc)
        return self._content

    def fragments(self, context=5):
        content = self.content()
        L = content.split(" ")
        acc = []
        for i, w in enumerate(L):
            fragment = []
            if regex.match(r"</?em>", w):
                fragment.extend(L[max(0, i - context) : i])
                fragment.append(w)
                fragment.extend(L[i + 1 : i + context + 1])
                acc.append(" ".join(fragment))
        return acc


def demo_highlighting():
    passage = Passage(
        urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1",
        content="μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος",
    )
    """
    ElasticSearch search query with FVH highlighter
    {
        "query" : {
            "match": { "content": "ἄειδε" }
        },
        "highlight" : {
            "type": "fvh",
            "number_of_fragments": 0,
            "fields" : {
                "content" : {}
            }
        }
    }
    """
    highlights = "μῆνιν <em>ἄειδε</em> θεὰ Πηληϊάδεω Ἀχιλῆος"

    highlighter = Highlighter(passage, highlights)

    print(f"Highlighted results from {passage.urn}: {highlighter.fragments()}")
    print(f"Highlighted tokens from {passage.urn}: {highlighter.tokens()}")
    print("(<token>, 0-indexed position)")
