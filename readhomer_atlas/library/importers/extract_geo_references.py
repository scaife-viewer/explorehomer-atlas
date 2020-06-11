import csv
import json
import time

import logfmt
import requests

from readhomer_atlas.library.models import Node, Token


def main():
    # import requests
    # url = "https://rosetest.library.jhu.edu/rosademo/wa/homer/VA/VA035RN-0036/canvas/annotation/10"
    # r = requests.get(url)
    # data = r.json()

    lookup = {}
    # @@@
    data = json.load(open("/Users/jwegner/Downloads/egj0gj1mjo9oz1 (2).jsonld"))

    def append_token_to_lookup(lookup, entry, card, token):
        lookup.setdefault(entry["id"], []).append((card.urn, token.position))

    barber_cards = (
        Node.objects.filter(
            urn__startswith="urn:cts:greekLit:tlg0012.tlg001.perseus-eng4:", kind="card"
        )
        .filter(
            idx__gte=Node.objects.filter(
                urn="urn:cts:greekLit:tlg0012.tlg001.perseus-eng4:2.480"
            )
            .first()
            .idx
        )
        .filter(
            idx__lte=Node.objects.filter(
                urn__startswith="urn:cts:greekLit:tlg0012.tlg001.perseus-eng4:2.840"
            )
            .first()
            .idx
        )
    )

    errors = set()
    by_id = {}
    for entry in data:
        # entry["target"][0]["source"]["id"]
        # ia = ImageAnnotation.objects.get(canvas_identifier=entry["target"][0]["source"]["id"])
        # folio = ia.text_parts.first()
        # @@@ get_descendants is not happening yet
        # lines = Node.objects.filter(urn__startswith=folio.urn).filter(kind="line")
        # refs = [l.ref.split(".", maxsplit=1)[1] for l in lines]
        # @@@ JHU
        # needle = entry["target"][-1].rsplit("@", maxsplit=1)[1]
        # @@@ recogito
        by_id[entry["id"]] = entry
        needle = entry["target"]["selector"][-1]["exact"]
        matches = barber_cards.filter(text_content__contains=needle)

        for match in matches:
            pieces = needle.split()
            tokens = list(match.tokens.filter(word_value__in=pieces))
            for pos, token in enumerate(tokens):
                if token.word_value == pieces[0]:
                    if len(pieces) == 1:
                        append_token_to_lookup(lookup, entry, match, token)
                    elif len(pieces) == 2:
                        try:
                            matched_tokens = [token, tokens[pos + 1]]
                        except IndexError:
                            if entry["id"] in lookup:
                                pass
                            elif entry["id"] not in errors:
                                print(
                                    f'Cannot handle entry [id="{entry["id"]}", needle="{needle}"]'
                                )
                                errors.add(entry["id"])
                            break
                        if [mt.word_value for mt in matched_tokens] == pieces:
                            for matched_token in matched_tokens:
                                append_token_to_lookup(
                                    lookup, entry, match, matched_token
                                )
                    else:
                        if entry["id"] in lookup:
                            pass
                        elif entry["id"] not in errors:
                            print(
                                f'Cannot handle entry [id="{entry["id"]}", needle="{needle}"]'
                            )
                            errors.add(entry["id"])
                        break

    georefs = {}
    for entry_id, named_entity in lookup.items():
        entry = by_id[entry_id]
        for body in entry["body"]:
            if body.get("purpose") == "georeferencing":
                georefs[entry_id] = entry

    import pprint

    unique_georefs = []
    for entry_id, named_entity in lookup.items():
        if entry_id in georefs:
            entry = by_id[entry_id]
            found = False
            for body in entry["body"]:
                if body.get("value", "").startswith("http://pleiades.stoa.org"):
                    found = True
                    break
            if not found:
                print(entry_id)
                pprint.pprint(entry["body"])
                print("\n")
            else:
                unique_georefs.append((entry, named_entity))
    # hardcode the other pleiades uri
    # Token.objects.filter(text_part__urn="urn:cts:greekLit:tlg0012.tlg001.perseus-eng4:2.720").filter(position__gte=15).filter(position__lte=17)
    entry = by_id[
        "https://recogito.pelagios.org/annotation/532c231a-7360-4d7a-b205-d4fdf3a424a7"
    ]
    unique_georefs.append(
        (
            entry,
            [
                (token.text_part.urn, token.position)
                for token in Token.objects.filter(
                    text_part__urn="urn:cts:greekLit:tlg0012.tlg001.perseus-eng4:2.720"
                )
                .filter(position__gte=15)
                .filter(position__lte=17)
            ],
        )
    )

    cite_block = """urn#label#description#pleiades#status#redirect
urn:cite2:hmt:place.v1:place1#Athens#city in Attica#pleiades.stoa.org/places/579885#proposed#
urn:cite2:hmt:place.v1:place2#Thessaly#northern region of Greece (also called Aeolia)#pleiades.stoa.org/places/1332#proposed#
urn:cite2:hmt:place.v1:place3#Hellas#Greece#pleiades.stoa.org/places/1001896#proposed#
urn:cite2:hmt:place.v1:place4#Dodona#in Epirus#pleiades.stoa.org/places/530843#proposed#
urn:cite2:hmt:place.v1:place5#Mycenae#city in the Peloponnese#pleiades.stoa.org/places/570491#proposed#
urn:cite2:hmt:place.v1:place6#Ilium#ancient name for Troy#pleiades.stoa.org/places/550595#accepted#
urn:cite2:hmt:place.v1:place7#Asteria#DO NOT USE#pleiades.stoa.org/places/530816#rejected#urn:cite2:hmt:place.v1:place9
urn:cite2:hmt:place.v1:place8#Cyclades#island group in the Aegean#pleiades.stoa.org/places/560353#proposed#
urn:cite2:hmt:place.v1:place9#Delos#island in the Cyclades, also known as Asteria as the ancient name#pleiades.stoa.org/places/599587#proposed#
urn:cite2:hmt:place.v1:place10#Arcadia#province in the Peloponnese#pleiades.stoa.org/places/570102#proposed#
urn:cite2:hmt:place.v1:place11#Cilla#a town in the Troad#pleiades.stoa.org/places/554254#proposed#
urn:cite2:hmt:place.v1:place12#Pisa#in Greece#pleiades.stoa.org/places/403253#proposed#
urn:cite2:hmt:place.v1:place13#Lesbos#island of the coast of modern Turkey#pleiades.stoa.org/places/550696#proposed#
urn:cite2:hmt:place.v1:place14#Tenedos#island not far from Troy#pleiades.stoa.org/places/550912#proposed#
urn:cite2:hmt:place.v1:place15#Troy#REJECTED city in modern Turkey#pleiades.stoa.org/places/550595#rejected#urn:cite2:hmt:place.v1:place6
urn:cite2:hmt:place.v1:place16#Leucophrys#former name of Tenedos#pleiades.stoa.org/places/550911#proposed#
urn:cite2:hmt:place.v1:place17#Sminthos#town in the Troad##proposed#
urn:cite2:hmt:place.v1:place18#Troad#region in western Turkey#pleiades.stoa.org/places/550944#proposed#
urn:cite2:hmt:place.v1:place19#Chryse#town from which Agamemnon took Chryseis#pleiades.stoa.org/places/554214#proposed#
urn:cite2:hmt:place.v1:place20#Mysia#region in northern Turkey#pleiades.stoa.org/places/550759#proposed#
urn:cite2:hmt:place.v1:place21#Crete#island south of mainland Greece#pleiades.stoa.org/places/589748#proposed#
urn:cite2:hmt:place.v1:place22#Hellespont#the narrow crossing between Turkey and the rest of Europe#pleiades.stoa.org/places/501434#proposed#
urn:cite2:hmt:place.v1:place23#Libya#in Africa#pleiades.stoa.org/places/716588#proposed#
urn:cite2:hmt:place.v1:place24#Arabia#the Arabian peninsula#pleiades.stoa.org/places/29475#proposed#
urn:cite2:hmt:place.v1:place25#Egypt#in Africa#pleiades.stoa.org/places/766#proposed#
urn:cite2:hmt:place.v1:place26#Rhodes#island off the SW coast of Turkey#pleiades.stoa.org/places/590031#proposed#
urn:cite2:hmt:place.v1:place27#Lacedaemonia#also called Laconia, region around Sparta in the Peloponnese#pleiades.stoa.org/places/570406#proposed#
urn:cite2:hmt:place.v1:place28#Massalia#Greek colony in Gaul#pleiades.stoa.org/places/148127#proposed#
urn:cite2:hmt:place.v1:place29#Aulis#town in Boeotia#pleiades.stoa.org/places/579889#proposed#
urn:cite2:hmt:place.v1:place30#Boeotia#region containing the Greek Thebes#pleiades.stoa.org/places/540689#proposed#
urn:cite2:hmt:place.v1:place31#Tauris#aka Crimea#pleiades.stoa.org/places/197545#proposed#
urn:cite2:hmt:place.v1:place32#Scythia#region in central Asia#pleiades.stoa.org/places/991379#proposed#
urn:cite2:hmt:place.v1:place33#Macedon#Macedonia, ancient name is Emathia, region in Northern Greece#pleiades.stoa.org/places/991368#proposed#
urn:cite2:hmt:place.v1:place34#Phthia#southern Thessaly#pleiades.stoa.org/places/541052#proposed#
urn:cite2:hmt:place.v1:place35#Isthmus#of Corinth#pleiades.stoa.org/places/570317#proposed#
urn:cite2:hmt:place.v1:place36#Peloponnese#large peninsula of Greece#pleiades.stoa.org/places/570577#proposed#
urn:cite2:hmt:place.v1:place37#Mt. Parnassus#mountain in central Greece near Delphi#pleiades.stoa.org/places/541012#proposed#
urn:cite2:hmt:place.v1:place38#Amphipolis#city in Thrace#pleiades.stoa.org/places/501347#proposed#
urn:cite2:hmt:place.v1:place39#Cotiaeum#city in Western Turkey#pleiades.stoa.org/places/609444#proposed#
urn:cite2:hmt:place.v1:place40#Argolis#region in the Peloponnese#pleiades.stoa.org/places/570104#proposed#
urn:cite2:hmt:place.v1:place41#Pylos#island off the southwest corner of the Peloponnese#pleiades.stoa.org/places/570640#proposed#
urn:cite2:hmt:place.v1:place42#Messenia#region in the Peloponnese#pleiades.stoa.org/places/570480#proposed#
urn:cite2:hmt:place.v1:place43#Aegialeia#aka Aegialos, province Achaea#pleiades.stoa.org/places/570049#proposed#
urn:cite2:hmt:place.v1:place44#attos#port city in the Peloponnese#pleiades.stoa.org/places/570106#proposed#
urn:cite2:hmt:place.v1:place45#Olympus#realm of the Olympian gods#pleiades.stoa.org/places/491677#proposed#
urn:cite2:hmt:place.v1:place46#Ethiopia#in Africa#pleiades.stoa.org/places/39274#proposed#
urn:cite2:hmt:place.v1:place47#Tarsus#city in southern Turkey#pleiades.stoa.org/places/648789#proposed#
urn:cite2:hmt:place.v1:place48#Lindos#on Rhodes#pleiades.stoa.org/places/589913#proposed#
urn:cite2:hmt:place.v1:place49#Thebes#in Boetia#pleiades.stoa.org/places/541138#proposed#
urn:cite2:hmt:place.v1:place50#Phlius#city in the northwestern Argolid in the Peloponnese#pleiades.stoa.org/places/573109#proposed#
urn:cite2:hmt:place.v1:place51#Thebes#in the Troad, Cilician Thebes#pleiades.stoa.org/places/550920#proposed#
urn:cite2:hmt:place.v1:place53#Laconia#DO NOT USE#pleiades.stoa.org/places/570406#rejected#urn:cite2:hmt:place.v1:place27
urn:cite2:hmt:place.v1:place54#Colophon#city in Lydia#pleiades.stoa.org/places/599577#proposed#
urn:cite2:hmt:place.v1:place55#Cilicia#region in or near the Troad#pleiades.stoa.org/places/991403#proposed#
urn:cite2:hmt:place.v1:place56#Cape Maleas#peninsula in the Peloponnese#pleiades.stoa.org/places/570455#proposed#
urn:cite2:hmt:place.v1:place57#Pelion#mountain in Southeast Thessaly#pleiades.stoa.org/places/541021#proposed#
urn:cite2:hmt:place.v1:place58#Sinope#a town of Paphlagonia on the Black Sea#pleiades.stoa.org/places/857321#proposed#
urn:cite2:hmt:place.v1:place59#Lyrnessus#town associated with Cilician Thebes#pleiades.stoa.org/places/550703#proposed#
urn:cite2:hmt:place.v1:place60#Tartarus#deepest region of the Underworld##proposed#
urn:cite2:hmt:place.v1:place61#Scyros#island of the Sporades#pleiades.stoa.org/places/541093#proposed#
urn:cite2:hmt:place.v1:place62#Nile#River in Egypt#pleiades.stoa.org/places/727172#proposed#
urn:cite2:hmt:place.v1:place63#Ithaca#island in the Ionian Sea#pleiades.stoa.org/places/530906#proposed#
urn:cite2:hmt:place.v1:place64#Diospolis#Zeus City#pleiades.stoa.org/places/844907#proposed#
urn:cite2:hmt:place.v1:place65#Elis#region of the Peloponnese#pleiades.stoa.org/places/570220#proposed#
urn:cite2:hmt:place.v1:place66#Amnisos#port of Knossos#pleiades.stoa.org/places/589682#proposed#
urn:cite2:hmt:place.v1:place67#Hades#the Underworld##proposed#
urn:cite2:hmt:place.v1:place68#Cos#island in the Sporades#pleiades.stoa.org/places/599581#proposed#
urn:cite2:hmt:place.v1:place69#Lemnos#old name is Sinteis, island in the Northern Aegaen#pleiades.stoa.org/places/550693#proposed#
urn:cite2:hmt:place.v1:place70#Thrace#region NE of Greece near Turkey#pleiades.stoa.org/places/501638#proposed#
urn:cite2:hmt:place.v1:place71#Sidon#Phoenician city#pleiades.stoa.org/places/678393#proposed#
urn:cite2:hmt:place.v1:place72#Caucasus#mountains separating Turkey from central Europe#pleiades.stoa.org/places/863766#proposed#
urn:cite2:hmt:place.v1:place73#Thesprotia#shrine housed an oracle#pleiades.stoa.org/places/531117#proposed#
urn:cite2:hmt:place.v1:place74#Ashkelon#also spelled Ascalon, coastal city in modern Israel#pleiades.stoa.org/places/687839#proposed#
urn:cite2:hmt:place.v1:place75#Lycia#region in Anatolia#pleiades.stoa.org/places/638965#proposed#
urn:cite2:hmt:place.v1:place76#Attica#region containing Athens/a regional dialect#pleiades.stoa.org/places/579888#proposed#
urn:cite2:hmt:place.v1:place77#Aeolic#northern dialect#pleiades.stoa.org/places/1332#proposed#
urn:cite2:hmt:place.v1:place78#Doric/Dorian#dialect encompassing a large part of Greece including the Peloponeese#pleiades.stoa.org/places/540740#proposed#
urn:cite2:hmt:place.v1:place79#Ionia#region in Western Turkey#pleiades.stoa.org/places/550597#proposed#
urn:cite2:hmt:place.v1:place80#Ephesus#Greek city in Ionia#pleiades.stoa.org/places/599612#proposed#
urn:cite2:hmt:place.v1:place81#Arctic Circle#North pole##proposed#
urn:cite2:hmt:place.v1:place82#Antarctic Circle#South pole##proposed#
urn:cite2:hmt:place.v1:place83#Nablus#city in the Western Bank of modern day Israel (Neapolis)#pleiades.stoa.org/places/678301#proposed#
urn:cite2:hmt:place.v1:place84#Phaestus#city on Crete#pleiades.stoa.org/places/589987#proposed#
urn:cite2:hmt:place.v1:place85#Caria#region in Western Anatolia#pleiades.stoa.org/places/991381#proposed#
urn:cite2:hmt:place.v1:place86#Sardis#also called Tarne, capital of Lydia#pleiades.stoa.org/places/550867#proposed#
urn:cite2:hmt:place.v1:place87#Lydia#kingdom east of Ionia, also called Maeonia#pleiades.stoa.org/places/991385#proposed#
urn:cite2:hmt:place.v1:place88#Zeleia#town allied to Troy, at the foot of Mt. Ida#pleiades.stoa.org/places/511461#proposed#
urn:cite2:hmt:place.v1:place89#Mt. Ida#mountain in the Troad#pleiades.stoa.org/places/550402#proposed#
urn:cite2:hmt:place.v1:place90#Hyle#a town in Boeotia#pleiades.stoa.org/places/540825#proposed#
urn:cite2:hmt:place.v1:place91#Hyde#a town on Mt. Tmolus in Lydia (possibly the later Sardis)#pleiades.stoa.org/places/550867#proposed#
urn:cite2:hmt:place.v1:place92#Simois River#flows into the Scamander River#pleiades.stoa.org/places/550883#proposed#
urn:cite2:hmt:place.v1:place93#Scamander River#river rising from Mt. Ida,sometimes referred to as Xanthus#pleiades.stoa.org/places/550871#proposed#
urn:cite2:hmt:place.v1:place94#Acheron#river of the nether world##proposed#
urn:cite2:hmt:place.v1:place95#Locris#REJECTED, Opuntia, region in central Greece#pleiades.stoa.org/places/540918#rejected#urn:cite2:hmt:place.v1:place269 or urn:cite2:hmt:place.v1:place270
urn:cite2:hmt:place.v1:place96#Achaea#region of Greece in the NW part of the Peloponese#pleiades.stoa.org/places/570028#proposed#
urn:cite2:hmt:place.v1:place97#Emathoes#river near Pylos##proposed#
urn:cite2:hmt:place.v1:place98#Cyprus#Greek Island#pleiades.stoa.org/places/981516#proposed#
urn:cite2:hmt:place.v1:place99#Abydus#an ancient city of Mysia, in Asia Minor#pleiades.stoa.org/places/501325#proposed#
urn:cite2:hmt:place.v1:place100#Euboea#the island separated from Boeotia by the Euripus, named by Homer as the home of the Abantes#pleiades.stoa.org/places/540775#proposed#
urn:cite2:hmt:place.v1:place101#Aegina#Island off the western coast of Attica, formerly known as Oenone#pleiades.stoa.org/places/579844#proposed#
urn:cite2:hmt:place.v1:place102#Bosporus#Strait in Turkey#pleiades.stoa.org/places/520977#proposed#
urn:cite2:hmt:place.v1:place103#Aegean Sea#part of the Mediterranean Sea, near Greece#pleiades.stoa.org/places/560221#proposed#
urn:cite2:hmt:place.v1:place104#Myrtoan Sea#part of the Aegean, between the Cyclades and the Peloponnese#pleiades.stoa.org/places/570495#proposed#
urn:cite2:hmt:place.v1:place105#Istros#Greek city in modern day Romania on Black Sea#pleiades.stoa.org/places/446253#proposed#
urn:cite2:hmt:place.v1:place106#Alexandria#city in Egypt#pleiades.stoa.org/places/727070#proposed#
urn:cite2:hmt:place.v1:place107#Calydon#city in Aeolia#pleiades.stoa.org/places/540699#proposed#
urn:cite2:hmt:place.v1:place108#Icarian Sea#Sea between Cyclades and Asia Minor; named for son of Daedalus#pleiades.stoa.org/places/599668#proposed#
urn:cite2:hmt:place.v1:place109#Sicily#Largest island of Mediterranean; south of Italy#pleiades.stoa.org/places/462492#proposed#
urn:cite2:hmt:place.v1:place110#Camicus#city in Sicily#pleiades.stoa.org/places/465929#proposed#
urn:cite2:hmt:place.v1:place111#Persia#the great empire to the east, modern day Iran#pleiades.stoa.org/places/922698#proposed#
urn:cite2:hmt:place.v1:place112#Aegospotami#Small river issuing from the Hellespont#pleiades.stoa.org/places/501336#proposed#
urn:cite2:hmt:place.v1:place113#Cnidos#Greek settlement in modern day Turkey#pleiades.stoa.org/places/599575#proposed#
urn:cite2:hmt:place.v1:place114#Argos#Peloponnesian city; major Mycenaean site#pleiades.stoa.org/places/570106#proposed#
urn:cite2:hmt:place.v1:place115#Gerena#Nestor's city#pleiades.stoa.org/places/256181#proposed#
urn:cite2:hmt:place.v1:place116#Cayster River#Kaustros, small river in Turkey near Ephesus#pleiades.stoa.org/places/550492#proposed#
urn:cite2:hmt:place.v1:place117#Megara#city in Attica#pleiades.stoa.org/places/570468#proposed#
urn:cite2:hmt:place.v1:place118#Salamis#city in Cyprus#pleiades.stoa.org/places/580101#proposed#
urn:cite2:hmt:place.v1:place119#Mycale#a promontory in lydia Minor, opposite Samos#pleiades.stoa.org/places/599805#proposed#
urn:cite2:hmt:place.v1:place120#Miletus#city in the Anatolia province of modern-day Turkey#pleiades.stoa.org/places/599799#proposed#
urn:cite2:hmt:place.v1:place121#Meander#river of Caria#pleiades.stoa.org/places/599777#proposed#
urn:cite2:hmt:place.v1:place122#Phthiron#alternatively spelled Phtheiron, a mountain in Caria, near the city of Miletos##proposed#
urn:cite2:hmt:place.v1:place123#Priene#city in Ionia#pleiades.stoa.org/places/599905#proposed#
urn:cite2:hmt:place.v1:place124#Arisbe#town in the Troad#pleiades.stoa.org/places/501359#proposed#
urn:cite2:hmt:place.v1:place125#Sestus#Thracian city on the Hellespont, opposite Abydus#pleiades.stoa.org/places/501609#proposed#
urn:cite2:hmt:place.v1:place126#Aetolia#Region of Western Greece, north of the Gulf of Corinth#pleiades.stoa.org/places/540591#proposed#
urn:cite2:hmt:place.v1:place127#Phoenicia#a civilization on the Western Coast of the Fertile Crescent#pleiades.stoa.org/places/991410#proposed#
urn:cite2:hmt:place.v1:place128#Phocis#on the Corinthian gulf#pleiades.stoa.org/places/541048#proposed#
urn:cite2:hmt:place.v1:place129#Euripus#straight between Euboea and the mainland#http://pleiades.stoa.org/places/540783#proposed#
urn:cite2:hmt:place.v1:place130#Arne#town in Boeotia#pleiades.stoa.org/places/540663#proposed#
urn:cite2:hmt:place.v1:place131#Mycalessus#town in Boeotia##proposed#
urn:cite2:hmt:place.v1:place132#Samos#island in the eastern Aegean#pleiades.stoa.org/places/599925#proposed#
urn:cite2:hmt:place.v1:place133#Graia#town in Boeotia#pleiades.stoa.org/places/540796#proposed#
urn:cite2:hmt:place.v1:place134#Medeon#town in Boeotia#pleiades.stoa.org/places/540940#proposed#
urn:cite2:hmt:place.v1:place135#Tanagra#town in Boeotia#pleiades.stoa.org/places/580114#proposed#
urn:cite2:hmt:place.v1:place136#Cithaeron#mountain; in a scene in battle of Plataea#pleiades.stoa.org/places/540714#proposed#
urn:cite2:hmt:place.v1:place137#Eleon#town in Boeotia##proposed#
urn:cite2:hmt:place.v1:place138#Hyle#town in Lydia##proposed#
urn:cite2:hmt:place.v1:place139#Mt. Tmolus#mountain in Lydia#pleiades.stoa.org/places/550937#proposed#
urn:cite2:hmt:place.v1:place140#Haliartus#aka Aliartos, town in Boeotia#pleiades.stoa.org/places/540801#proposed#
urn:cite2:hmt:place.v1:place141#Plataea#town in Boeotia#pleiades.stoa.org/places/541063#proposed#
urn:cite2:hmt:place.v1:place142#Ogchestus#city in Boeotia##proposed#
urn:cite2:hmt:place.v1:place143#Chaeronea#town in Boeotia#pleiades.stoa.org/places/540701#proposed#
urn:cite2:hmt:place.v1:place144#Leontari#town in Boeotia##proposed#
urn:cite2:hmt:place.v1:place145#Helicon#mountain in Boeotia#pleiades.stoa.org/places/540808#proposed#
urn:cite2:hmt:place.v1:place146#Nisa#village on Mt. Helicon in Boeotia##proposed#
urn:cite2:hmt:place.v1:place147#Anthedon#town in Boeotia on the Euripus#pleiades.stoa.org/places/540639#proposed#
urn:cite2:hmt:place.v1:place148#Orchomenus#ancient city on Lake Copais in Boeotia, associated with the Minyans#pleiades.stoa.org/places/540987#proposed#
urn:cite2:hmt:place.v1:place149#Hyampolis#town in Phocis, on the Cephissus#pleiades.stoa.org/places/540820#proposed#
urn:cite2:hmt:place.v1:place150#Locris Ozolia#home of the Ozolae, tribe of Locrians#pleiades.stoa.org/places/540919#proposed#
urn:cite2:hmt:place.v1:place151#Lilaia#town in Phocis#pleiades.stoa.org/places/540915#proposed#
urn:cite2:hmt:place.v1:place152#Cephissus#river in Phocis#pleiades.stoa.org/places/540860#proposed#
urn:cite2:hmt:place.v1:place153#Syria#country#pleiades.stoa.org/places/1306#proposed#
urn:cite2:hmt:place.v1:place154#Abantes#USE EPONYMOUS ANCESTOR INSTEAD#pleiades.stoa.org/places/540583#rejected#urn:cite2:hmt:pers.pers776
urn:cite2:hmt:place.v1:place155#Eretria#city on western coast of Euboea#pleiades.stoa.org/places/579925#proposed#
urn:cite2:hmt:place.v1:place156#Oreus#town in northern Euboea#pleiades.stoa.org/places/540988#proposed#
urn:cite2:hmt:place.v1:place157#Curetes#oldest inhabitants of Pleuron in Aetolia#pleiades.stoa.org/places/543757#proposed#
urn:cite2:hmt:place.v1:place158#Chalcis#town in Aetolia#pleiades.stoa.org/places/540703#proposed#
urn:cite2:hmt:place.v1:place159#Arethousa#fount in Ithaca##proposed#
urn:cite2:hmt:place.v1:place160#Troezen#a town in Argolis, near the shore of the Saronic gulf#pleiades.stoa.org/places/570756#proposed#
urn:cite2:hmt:place.v1:place161#Calauria#an island close to the coast of Troezen in the Peloponnesus#pleiades.stoa.org/places/570325#proposed#
urn:cite2:hmt:place.v1:place162#Epidarus#sanctuary to Ascleipius in the Peloponnese#pleiades.stoa.org/places/570228#proposed#
urn:cite2:hmt:place.v1:place163#Mases#a town in Argolis, near Hermione#pleiades.stoa.org/places/570463#proposed#
urn:cite2:hmt:place.v1:place164#Scheria#island, inhabited by the Phaecians##proposed#
urn:cite2:hmt:place.v1:place165#Corinth#(old name is Ephyra), know as Argive Ephyre in Homer#pleiades.stoa.org/places/570182#proposed#
urn:cite2:hmt:place.v1:place166#Arene#town subject to Nestor##proposed#
urn:cite2:hmt:place.v1:place167#Amyclae#a city in Laconia, near the Eurotas, 20 stadia S.E. of Sparta, and the residence of Tyndareus#pleiades.stoa.org/places/438675#proposed#
urn:cite2:hmt:place.v1:place168#Mt. Taygetos#in Sparta#pleiades.stoa.org/places/570706#proposed#
urn:cite2:hmt:place.v1:place169#Parthenius#a river in Paphlagonia#pleiades.stoa.org/places/845036#proposed#
urn:cite2:hmt:place.v1:place170#Aonia#district in Boeotia##proposed#
urn:cite2:hmt:place.v1:place171#Iolcus#city in Thessaly#pleiades.stoa.org/places/540837#proposed#
urn:cite2:hmt:place.v1:place172#Pelasgians#USE EPONYMUS ANCESTOR INSTEAD##rejected#urn:cite2:hmt:pers.pers433
urn:cite2:hmt:place.v1:place173#Delphi#Home of Pythian oracle; sacred to Apollo#pleiades.stoa.org/places/540726#proposed#
urn:cite2:hmt:place.v1:place174#Pherae#a city in Thessaly#pleiades.stoa.org/places/541044#proposed#
urn:cite2:hmt:place.v1:place175#Triphylia#area in the Peloponnese, 'country of three tribes'#pleiades.stoa.org/places/570754#proposed#
urn:cite2:hmt:place.v1:place176#Alpheius#river in Arcadia and Elis#pleiades.stoa.org/places/570067#proposed#
urn:cite2:hmt:place.v1:place177#Aepu#town subject to Nestor##proposed#
urn:cite2:hmt:place.v1:place178#Hyria#in Boeotia#pleiades.stoa.org/places/540830#proposed#
urn:cite2:hmt:place.v1:place179#Schoenus#a town in Boeotia##proposed#
urn:cite2:hmt:place.v1:place180#Scolus#a town in Boeotia#pleiades.stoa.org/places/541106#proposed#
urn:cite2:hmt:place.v1:place181#Eteonus#a town in Boeotia#pleiades.stoa.org/places/543704#proposed#
urn:cite2:hmt:place.v1:place182#Thespia#a town in Boeotia#pleiades.stoa.org/places/541141#proposed#
urn:cite2:hmt:place.v1:place183#Copae#a town in Boeotia#pleiades.stoa.org/places/540878#proposed#
urn:cite2:hmt:place.v1:place184#Eutresis#a town in Boeotia#pleiades.stoa.org/places/540787#proposed#
urn:cite2:hmt:place.v1:place185#Messene#or Messe, city in the Peloponnese#pleiades.stoa.org/places/570479#proposed#
urn:cite2:hmt:place.v1:place186#Ascra#in Boeotia, hometown of Hesiod#pleiades.stoa.org/places/540670#proposed#
urn:cite2:hmt:place.v1:place187#Bouprosion#an ancient town of Elis##proposed#
urn:cite2:hmt:place.v1:place188#Bessa#or Besa, in Locris#pleiades.stoa.org/places/543653#proposed#
urn:cite2:hmt:place.v1:place189#Echinades#also called with Echinae, group of islands in the Ionian Sea#pleiades.stoa.org/places/530852#proposed#
urn:cite2:hmt:place.v1:place190#Doulichion#Dulichium, or Dolicha, or Doliche, island in the Echinades#pleiades.stoa.org/places/530845#proposed#
urn:cite2:hmt:place.v1:place191#Cephalonia#Cephellenia, largest Ionian island#pleiades.stoa.org/places/530826#proposed#
urn:cite2:hmt:place.v1:place192#Cyparissus#in Phocis##proposed#
urn:cite2:hmt:place.v1:place193#Pytho#more recent name for Crisa#pleiades.stoa.org/places/540726#proposed#
urn:cite2:hmt:place.v1:place194#Crisa#near the Delphic oracle#pleiades.stoa.org/places/540889#proposed#
urn:cite2:hmt:place.v1:place195#Daulis#city in Phocis#pleiades.stoa.org/places/540723#proposed#
urn:cite2:hmt:place.v1:place196#Lycastus#town in Southern Crete##proposed#
urn:cite2:hmt:place.v1:place197#Panopeus#city in Phocis#pleiades.stoa.org/places/541008#proposed#
urn:cite2:hmt:place.v1:place198#Anemoreia#town in Phocis#pleiades.stoa.org/places/543626#proposed#
urn:cite2:hmt:place.v1:place199#Cynus#town in Locris#pleiades.stoa.org/places/540896#proposed#
urn:cite2:hmt:place.v1:place200#Phylace#town in Thessaly#pleiades.stoa.org/places/541053#proposed#
urn:cite2:hmt:place.v1:place201#Imbros#island off the coast of Thrace#pleiades.stoa.org/places/501439#proposed#
urn:cite2:hmt:place.v1:place202#Ozonon river#in Aetolia##proposed#
urn:cite2:hmt:place.v1:place203#Euinus river#probably in Locris##proposed#
urn:cite2:hmt:place.v1:place204#Italy#Large peninsula in Western Mediterranean#pleiades.stoa.org/places/1052#proposed#
urn:cite2:hmt:place.v1:place205#Titanus#mountain/town in Thessaly#pleiades.stoa.org/places/541150#proposed#
urn:cite2:hmt:place.v1:place206#Orthe#town in Thessaly#pleiades.stoa.org/places/540992#proposed#
urn:cite2:hmt:place.v1:place207#Elone#town in Thessaly#pleiades.stoa.org/places/540760#proposed#
urn:cite2:hmt:place.v1:place208#Oloosson#town in Thessaly##proposed#
urn:cite2:hmt:place.v1:place209#Augeiae#lovely town in Laconia##proposed#
urn:cite2:hmt:place.v1:place210#Cyphus#town in Perrhaevia in Thessaly#pleiades.stoa.org/places/543761#proposed#
urn:cite2:hmt:place.v1:place211#Meliboea#town in Magnesia#pleiades.stoa.org/places/543784#proposed#
urn:cite2:hmt:place.v1:place212#Magnesia#region in North Eastern Greece#pleiades.stoa.org/places/540923#proposed#
urn:cite2:hmt:place.v1:place213#Orneae#Orneiae, town in Argolis#pleiades.stoa.org/places/570537#proposed#
urn:cite2:hmt:place.v1:place214#Araethyrea#in Corinth#pleiades.stoa.org/places/573109#proposed#
urn:cite2:hmt:place.v1:place215#Pellene#city in Thrace##proposed#
urn:cite2:hmt:place.v1:place216#Pallene#town in Attica#pleiades.stoa.org/places/580051#proposed#
urn:cite2:hmt:place.v1:place217#Batieia#height on the plain of Troy before the city##proposed#
urn:cite2:hmt:place.v1:place218#Sparta#Laconic city in the Peloponnese#pleiades.stoa.org/places/570685#proposed#
urn:cite2:hmt:place.v1:place219#Laas#or Las, in Laconia##proposed#
urn:cite2:hmt:place.v1:place220#Oetylus#in Laconia##proposed#
urn:cite2:hmt:place.v1:place221#Chersonese#peninsula of Thrace#pleiades.stoa.org/places/501352#proposed#
urn:cite2:hmt:place.v1:place222#Thryon#or Thryoessa, town in Elis##proposed#
urn:cite2:hmt:place.v1:place223#Maroneia#in Thrace##proposed#
urn:cite2:hmt:place.v1:place224#Europe#Continent west of and connected to Asia. Contains Greece##proposed#
urn:cite2:hmt:place.v1:place225#Helus#a costal city in Lacadaemon##proposed#
urn:cite2:hmt:place.v1:place226#Asia#Continent east of and connected to Europe. Contains Asia Minor and Persia##proposed#
urn:cite2:hmt:place.v1:place227#Veneto#region in Northern Italy inhabited by the Veneti (Latin Heneti, Greek Enetoi)##proposed#
urn:cite2:hmt:place.v1:place228#Eruthinoi#a place in Paphlagonia##proposed#
urn:cite2:hmt:place.v1:place229#Acragas#Agrigento, Sicily#pleiades.stoa.org/places/462086#proposed#
urn:cite2:hmt:place.v1:place230#Oechalia#in Thessaly##proposed#
urn:cite2:hmt:place.v1:place231#Phrygia#Region in Western Central Anatolia#pleiades.stoa.org/places/609502#proposed#
urn:cite2:hmt:place.v1:place232#Sangarius#a river flowing through Bithynia and Phrygia, and emptying into the Euxine#pleiades.stoa.org/places/511406#proposed#
urn:cite2:hmt:place.v1:place233#Phthiron#REJECTED Not Used##rejected#urn:cite2:hmt:place.v1:place122
urn:cite2:hmt:place.v1:place234#Cyllene#mountain in Arcadia##proposed#
urn:cite2:hmt:place.v1:place235#Pheneus#town in Arcadia#pleiades.stoa.org/places/570595#proposed#
urn:cite2:hmt:place.v1:place236#Myrsinos#A village near Elis#pleiades.stoa.org/places/57049#proposed#
urn:cite2:hmt:place.v1:place237#Hyrmine#A port in northern Elis#pleiades.stoa.org/places/570305#proposed#
urn:cite2:hmt:place.v1:place238#Olenia#REJECTED NOT A PLACE, DON'T USE##rejected#
urn:cite2:hmt:place.v1:place239#Aleision#or Alesion, town near Elis##proposed#
urn:cite2:hmt:place.v1:place240#Scandeia#name of a harbor in the island of Cythera#pleiades.stoa.org/places/570673#proposed#
urn:cite2:hmt:place.v1:place241#Cythera#island off the coast of the southeastern tip of the Peloponnese#pleiades.stoa.org/places/570186#proposed#
urn:cite2:hmt:place.v1:place242#Asopos River#river in Boeotia#pleiades.stoa.org/places/540672#proposed#
urn:cite2:hmt:place.v1:place243#Paeonia#region of Northern Greece that includes Thrace##proposed#
urn:cite2:hmt:place.v1:place244#Leleges#USE EPONYMOUS ANCESTOR INSTEAD##rejected#urn:cite2:hmt:pers.pers777
urn:cite2:hmt:place.v1:place245#Caucones#DO NOT USE, NO PLACE OR EPONYMOUS ANCESTOR##rejected#
urn:cite2:hmt:place.v1:place246#Thymbres#a tributary of the Sangarius in Phrygia##proposed#
urn:cite2:hmt:place.v1:place247#Adriatic Sea#body of water between the Italian and Balkan Peninsulae#pleiades.stoa.org/places/1004#proposed#
urn:cite2:hmt:place.v1:place248#Dacelea#also spelt Decelea, city in Attica, fortified by Spartans during Peloponnesian War##proposed#
urn:cite2:hmt:place.v1:place249#Percote#town northeast of Troy##proposed#
urn:cite2:hmt:place.v1:place250#Ister#Danube river; also colony at its mouth#pleiades.stoa.org/places/226577#proposed#
urn:cite2:hmt:place.v1:place251#Rhesus#a river that flows from Mt Ida near Troy#pleiades.stoa.org/places/511398#proposed#
urn:cite2:hmt:place.v1:place252#Aesepus#a river that flows from Mt Ida near Troy#pleiades.stoa.org/places/511141#proposed#
urn:cite2:hmt:place.v1:place253#Heptaporus#a river that flows from Mt Ida near Troy##proposed#
urn:cite2:hmt:place.v1:place254#Granicus#a river that flows from Mt Ida near Troy#pleiades.stoa.org/places/511260#proposed#
urn:cite2:hmt:place.v1:place255#Caresus#a river that flows from Mt Ida near Troy#pleiades.stoa.org/places/511287#proposed#
urn:cite2:hmt:place.v1:place256#Rhodius#a river that flows from Mt Ida near Troy#pleiades.stoa.org/places/501590#proposed#
urn:cite2:hmt:place.v1:place257#Selleeis#or Selleis,a river in the Troad near Arisbe#pleiades.stoa.org/places/501604#proposed#
urn:cite2:hmt:place.v1:place258#Pannonia#Province north of Illyricum; bounded by Danube#pleiades.stoa.org/places/992076#proposed#
urn:cite2:hmt:place.v1:place259#Cyzicus#Ancient town in Mysia#pleiades.stoa.org/places/511218#proposed#
urn:cite2:hmt:place.v1:place260#Opus#a city in Locris, the home of Menoetius, father of Patroclus##proposed#
urn:cite2:hmt:place.v1:place261#Spercheius#a river in Thessaly#pleiades.stoa.org/places/541112#proposed#
urn:cite2:hmt:place.v1:place262#Paphlagonia#Region on north coast of Anatolia#pleiades.stoa.org/places/845034#proposed#
urn:cite2:hmt:place.v1:place263#Caunus#City of Caria in Anatolia#pleiades.stoa.org/places/638796#proposed#
urn:cite2:hmt:place.v1:place264#Tralleis#or Tralles,City in southwestern Anatolia#pleiades.stoa.org/places/599987#proposed#
urn:cite2:hmt:place.v1:place265#Thymbra#Town near Troy; place of sanctuary to Apollo#pleiades.stoa.org/places/550927#proposed#
urn:cite2:hmt:place.v1:place266#Pidaios#town associated with the Leleges, alternatively spelled Pedasus##proposed#
urn:cite2:hmt:place.v1:place267#Teuchios#town in Euboea##proposed#
urn:cite2:hmt:place.v1:place268#Ios#island in the Cyclades#pleiades.stoa.org/places/599673#proposed#
urn:cite2:hmt:place.v1:place269#Locris#region of Greece north of Boeotia divided into three distinct regions##proposed#
urn:cite2:hmt:place.v1:place270#Opuntia#a region of Locris, home of the Epicnemidii Locri or the Locri Opuntii#pleiades.stoa.org/places/540918#proposed#
urn:cite2:hmt:place.v1:place271#Ikaros#modern Icaria,and island in the Aegean#pleiades.stoa.org/places/599667#proposed#
urn:cite2:hmt:place.v1:place272#Dardania#a city and a district of the Troad, in Asia Minor on the Hellespont##proposed#
urn:cite2:hmt:place.v1:place273#Xois#Ancient Egyptian City on Nile Delta, identified as the ancient Egyptian city of Khasut or Khaset or Sakha#pleiades.stoa.org/places/727256#proposed#
urn:cite2:hmt:place.v1:place274#Sais#or Sa el-Hagar, an  ancient Egyptian town in the Western Nile Delta on the Canopic branch of the Nile,Egyptian name was Zau#pleiades.stoa.org/places/727217#proposed#
urn:cite2:hmt:place.v1:place275#Triton#a river in Libya, joining the lake Tritonis with the sea##proposed#
urn:cite2:hmt:place.v1:place276#Gargaron#a village on Mt. Ida in the Troad##proposed#
urn:cite2:hmt:place.v1:place277#Helice#city located in Achaea, northern Peloponnesos, submerged in a tsunami in 373 BCE#pleiades.stoa.org/places/570281#proposed#
urn:cite2:hmt:place.v1:place278#Aegae#Aigai, an ancient town on the west coast of the island of Euboea#pleiades.stoa.org/places/540603#proposed#
urn:cite2:hmt:place.v1:place279#Cocytus#a river of the Underworld##proposed#
urn:cite2:hmt:place.v1:place280#Styx#a river of the Underworld##proposed#
urn:cite2:hmt:place.v1:place282#Pleuron#an ancient city in Aetolia#pleiades.stoa.org/places/540999#proposed#
urn:cite2:hmt:place.v1:place283#Eleusis#a district of Attica, site of the Eleusinian Mysteries#pleiades.stoa.org/places/579920#proposed#
urn:cite2:hmt:place.v1:place284#Lekton#the westernmost point of the Anatolian part of Turkey#pleiades.stoa.org/places/550691#proposed#
urn:cite2:hmt:place.v1:place285#Phalacra#a promontory of Mount Ida, in Mysia##proposed#
urn:cite2:hmt:place.v1:place286#Erebus#a region of the Greek underworld where the dead pass immediately after dying##proposed#
urn:cite2:hmt:place.v1:place287#Aesyme#Aisyme, a town near Troy, possibly the historic Oisyme##proposed#
urn:cite2:hmt:place.v1:place288#Minyeius#River in Elis near Arene##proposed#
urn:cite2:hmt:place.v1:place289#Canopus#a town in Egypt#pleiades.stoa.org/places/727097#proposed#
urn:cite2:hmt:place.v1:place290#Glisas#a town in Boeotia#pleiades.stoa.org/places/540791#proposed#
urn:cite2:hmt:place.v1:place291#Halicarnassus#ancient city in Asia Minor#pleiades.stoa.org/places/599636#proposed#
urn:cite2:hmt:place.v1:place292#Lycabessos#or Lycabettos, the highest point in Athens#pleiades.stoa.org/places/582871#proposed#
urn:cite2:hmt:place.v1:place293#Tartessos#Tarshish, a district of Spain#pleiades.stoa.org/places/256468#proposed#
urn:cite2:hmt:place.v1:place294#Olenian Rock#possibly modern Mt. Skollis, named in a scholion as Kolone#pleiades.stoa.org/places/570676#proposed#
urn:cite2:hmt:place.v1:place295#Eleutherae#city in northern Attica bordering Boeotia#pleiades.stoa.org/places/540756#proposed#
urn:cite2:hmt:place.v1:place296#Trauos#a river of unclear location, possibly Thrace##proposed#
urn:cite2:hmt:place.v1:place297#Pramne#a hill in the island of Icaria, famous for its wine##proposed#
urn:cite2:hmt:place.v1:place298#Melos#island in the Cyclades group in the Aegean#pleiades.stoa.org/places/536106#proposed#
urn:cite2:hmt:place.v1:place299#Tenaron#Also called Cape Tainaron or Matapan, in the Laconic Gulf, contains the mythical enterance to Hades#pleiades.stoa.org/places/570703#proposed#
urn:cite2:hmt:place.v1:place300#Cranae#island off of Gytheio, where Helen and Paris spent their first night after leaving Sparta#pleiades.stoa.org/places/570379#proposed#
urn:cite2:hmt:place.v1:place301#Satnioeis#a river in the Troad, runs through Pedasus#pleiades.stoa.org/places/550870#proposed#
urn:cite2:hmt:place.v1:place302#Nysa#mythical mountanious area where the Hyades raised Dionysus##proposed#
urn:cite2:hmt:place.v1:place303#Harma#a town in Boeotia#pleiades.stoa.org/places/579943#proposed#
urn:cite2:hmt:place.v1:place304#Eilesion#Eilesium, a town in Boeotia#pleiades.stoa.org/places/540750#proposed#
urn:cite2:hmt:place.v1:place305#Erythrai#Erythrae, a town in Boeotia#pleiades.stoa.org/places/550535#proposed#
urn:cite2:hmt:place.v1:place306#Peteon#a town in Boeotia#pleiades.stoa.org/places/541028#proposed#
urn:cite2:hmt:place.v1:place307#Okalea#Ocalea, a village in Boeotia near Haliartus##proposed#
urn:cite2:hmt:place.v1:place308#Thisbe#a town in Boeotia#pleiades.stoa.org/places/541146#proposed#
urn:cite2:hmt:place.v1:place309#Aleian Plain#cite of Bellerephon's wandering, also know as Cilicia Pedias#pleiades.stoa.org/places/648554#proposed#
urn:cite2:hmt:place.v1:place310#Coroneia#or Coronea, a city in Boeotia, south of lake Copais#pleiades.stoa.org/places/540717#proposed#
urn:cite2:hmt:place.v1:place311#Onchestus#a town in Boeotia, sacred to Poseidon#pleiades.stoa.org/places/540984#proposed#
urn:cite2:hmt:place.v1:place312#Medeia#a town in Boeotia on Lake Copais##proposed#
urn:cite2:hmt:place.v1:place313#Aspledon#a town in Boeotia, also called Eudeielos#pleiades.stoa.org/places/540673#proposed#
urn:cite2:hmt:place.v1:place314#Placus#mountain at whose foot lies Cilician Thebe#pleiades.stoa.org/places/550836#proposed#
urn:cite2:hmt:place.v1:place315#Messeis#a spring in Pelasgian Argos##proposed#
urn:cite2:hmt:place.v1:place316#Hypereia#a spring in Pelasgian Argos##proposed#
urn:cite2:hmt:place.v1:place317#Calliarus#town in Locris#pleiades.stoa.org/places/540847#proposed#
urn:cite2:hmt:place.v1:place318#Scarphe#a place in Locris, near Thermopylae#pleiades.stoa.org/places/541103#proposed#
urn:cite2:hmt:place.v1:place319#Tarphe#a town in Locris#pleiades.stoa.org/places/540958#proposed#
urn:cite2:hmt:place.v1:place320#Thronion#a town in Locris#pleiades.stoa.org/places/541147#proposed#
urn:cite2:hmt:place.v1:place321#Boagrius#river in Locris##proposed#
urn:cite2:hmt:place.v1:place322#Histiaia#or Hestiaia, a city in Euboea#pleiades.stoa.org/places/540817#proposed#
urn:cite2:hmt:place.v1:place323#Kerinthos#Cerinthus, a city in Euboea#pleiades.stoa.org/places/540861#proposed#
urn:cite2:hmt:place.v1:place324#Dion#town in Euboea##proposed#
urn:cite2:hmt:place.v1:place325#Carystus#or Karystos, a town at the southern extremity of Euboea#pleiades.stoa.org/places/570336#proposed#
urn:cite2:hmt:place.v1:place326#Styra#a town in Euboea#pleiades.stoa.org/places/541117#proposed#
urn:cite2:hmt:place.v1:place327#Salamis#an island near Athens, home of Telamonian Ajax#pleiades.stoa.org/places/580101#proposed#
urn:cite2:hmt:place.v1:place328#Tiryns#a Mycenaean city in Argolis#pleiades.stoa.org/places/570740#proposed#
urn:cite2:hmt:place.v1:place329#Hermione#a city in Argolis#pleiades.stoa.org/places/329217#proposed#
urn:cite2:hmt:place.v1:place330#Asine#a town in Argolis#pleiades.stoa.org/places/570124#proposed#
urn:cite2:hmt:place.v1:place331#Eionae#a town in Argolis##proposed#
urn:cite2:hmt:place.v1:place332#Cleonae#or Kleonai, a town in Argolis#pleiades.stoa.org/places/570361#proposed#
urn:cite2:hmt:place.v1:place333#Sicyon#a city on the south shore of the gulf of Corinth#pleiades.stoa.org/places/570668#proposed#
urn:cite2:hmt:place.v1:place334#Hyperesia#a town in Achaea##proposed#
urn:cite2:hmt:place.v1:place335#Gonoessa#town in Achaea, near Pellene##proposed#
urn:cite2:hmt:place.v1:place336#Pellene#a town in Achaea#pleiades.stoa.org/places/570576#proposed#
urn:cite2:hmt:place.v1:place337#Aigion#Aegium, town in Achaea, afterward the capital of the Achaean league#pleiades.stoa.org/places/570049#proposed#
urn:cite2:hmt:place.v1:place338#Pharis#town in Laconia, south of Amyclae#pleiades.stoa.org/places/570591#proposed#
urn:cite2:hmt:place.v1:place339#Bryseiae#town in Laconia##proposed#
urn:cite2:hmt:place.v1:place340#Cyparisseis#a town in Elis##proposed#
urn:cite2:hmt:place.v1:place341#Amphigeneia#a town subject to Nestor##proposed#
urn:cite2:hmt:place.v1:place342#Pteleos#or Pteleon, a town in Elis subject to Nestor, possibly a colony from Thessalian Petelon##proposed#
urn:cite2:hmt:place.v1:place343#Helus#a city in Elis, not the Laconian Helus##proposed#
urn:cite2:hmt:place.v1:place344#Dorion#or Dorio, a town in the Peloponnese where Thamyris contested with the Muses#pleiades.stoa.org/places/570202#proposed#
urn:cite2:hmt:place.v1:place345#Orchomenus#city in Arcadia#pleiades.stoa.org/places/570535#proposed#
urn:cite2:hmt:place.v1:place346#Rhipe#a town in Arcadia##proposed#
urn:cite2:hmt:place.v1:place347#Stratia#a town in Arcadia##proposed#
urn:cite2:hmt:place.v1:place348#Enispe#a town in Arcadia##proposed#
urn:cite2:hmt:place.v1:place349#Tegea#a town in Arcadia#pleiades.stoa.org/places/570707#proposed#
urn:cite2:hmt:place.v1:place350#Mantineia#a town in Arcadia#pleiades.stoa.org/places/570459#proposed#
urn:cite2:hmt:place.v1:place351#Stymphalus#a small city in Arcadia#pleiades.stoa.org/places/570696#proposed#
urn:cite2:hmt:place.v1:place352#Parrasia#or Parrhassia, a town in Arcadia#pleiades.stoa.org/places/570564#proposed#
urn:cite2:hmt:place.v1:place353#Neriton#or Neritum, an Ionian island##proposed#
urn:cite2:hmt:place.v1:place354#Crocyleia#island or a village belonging to Ithaca##proposed#
urn:cite2:hmt:place.v1:place355#Aegilips# district, or island, under the rule of Odysseus##proposed#
urn:cite2:hmt:place.v1:place356#Zacynthus#an island in the realm of Odysseus, south of Same#pleiades.stoa.org/places/531155#proposed#
urn:cite2:hmt:place.v1:place357#Same#an island near Ithaca, perhaps Cephallenia or a part of Cephallenia#pleiades.stoa.org/places/531093#proposed#
urn:cite2:hmt:place.v1:place358#Olenus#a town in Aetolia, on Mt. Aracynthus##proposed#
urn:cite2:hmt:place.v1:place359#Pylene#a town in Aetolia##proposed#
urn:cite2:hmt:place.v1:place360#Knossos#or Cnosos, majors city on Crete#pleiades.stoa.org/places/589872#proposed#
urn:cite2:hmt:place.v1:place361#Gortys#or Gortyna, a city of Crete#pleiades.stoa.org/places/589796#proposed#
urn:cite2:hmt:place.v1:place362#Lyctus#a city in Crete, east of Cnosus#pleiades.stoa.org/places/589918#proposed#
urn:cite2:hmt:place.v1:place363#Miletus#in Crete, mother-city of the foregoing##proposed#
urn:cite2:hmt:place.v1:place364#Rhytion#city on Crete#pleiades.stoa.org/places/590033#proposed#
urn:cite2:hmt:place.v1:place365#Ialysus#a town on Rhodes#pleiades.stoa.org/places/589815#proposed#
urn:cite2:hmt:place.v1:place366#Cameirus#a town on the west coast of Rhodes##proposed#
urn:cite2:hmt:place.v1:place367#Ephyra#Ephyre, later name of Cichyrus, in Thesprotia#pleiades.stoa.org/places/530870#proposed#
urn:cite2:hmt:place.v1:place368#Selleis#a river near Ephyra, either Thesprotian or somewhere in Elis##proposed#
urn:cite2:hmt:place.v1:place369#Syme#island between Rhodes and Cnidus in Caria#pleiades.stoa.org/places/599951#proposed#
urn:cite2:hmt:place.v1:place370#Nisyrus#small island, one of the Sporades#pleiades.stoa.org/places/599830#proposed#
urn:cite2:hmt:place.v1:place371#Carpathus#an island between Crete and Rhodes#pleiades.stoa.org/places/589841#proposed#
urn:cite2:hmt:place.v1:place372#Casus#or Kasos, an island near Cos#pleiades.stoa.org/places/589846#proposed#
urn:cite2:hmt:place.v1:place373#Calydnae#group of islands off the coast of Caria#pleiades.stoa.org/places/550611#proposed#
urn:cite2:hmt:place.v1:place374#Alos#a town in the domain of Achilles##proposed#
urn:cite2:hmt:place.v1:place375#Alope#a town in the domain of Achilles##proposed#
urn:cite2:hmt:place.v1:place376#Trachis#town in Thessaly#pleiades.stoa.org/places/541157#proposed#
urn:cite2:hmt:place.v1:place377#Pyrasus#a town in Thessaly#pleiades.stoa.org/places/541081#proposed#
urn:cite2:hmt:place.v1:place378#Iton#a town in Thessaly##proposed#
urn:cite2:hmt:place.v1:place379#Antron#a town in Thessaly#pleiades.stoa.org/places/540644#proposed#
urn:cite2:hmt:place.v1:place380#Pteleon#a town in Thessaly#pleiades.stoa.org/places/541077#proposed#
urn:cite2:hmt:place.v1:place381#Boebeïs#lake in Thessaly#pleiades.stoa.org/places/540690#proposed#
urn:cite2:hmt:place.v1:place382#Boebe#town in Thessaly##proposed#
urn:cite2:hmt:place.v1:place383#Glaphyrae#town in Thessaly#pleiades.stoa.org/places/540790#proposed#
urn:cite2:hmt:place.v1:place384#Methone#a city in Magnesia, the home of Philoctetes#pleiades.stoa.org/places/540946#proposed#
urn:cite2:hmt:place.v1:place385#Thaumacia#a town in Magnesia, under the rule of Philoctetes#pleiades.stoa.org/places/541135#proposed#
urn:cite2:hmt:place.v1:place386#Olizon#a town in Magnesia in Thessaly#pleiades.stoa.org/places/540979#proposed#
urn:cite2:hmt:place.v1:place387#Trikka#or Trikke, a city in Thessaly, birthplace of Asclepius#pleiades.stoa.org/places/541163#proposed#
urn:cite2:hmt:place.v1:place388#Ithome#a city in Thessaly#pleiades.stoa.org/places/540841#proposed#
urn:cite2:hmt:place.v1:place389#Ormenion#a town in Thessaly##proposed#
urn:cite2:hmt:place.v1:place390#Asterion#or Asterium, a location in Thessaly##proposed#
urn:cite2:hmt:place.v1:place391#Argissa#a town in Thessaly##proposed#
urn:cite2:hmt:place.v1:place392#Gyrtone#a town in Pelasgiotis, on the river Peneus##proposed#
urn:cite2:hmt:place.v1:place393#Titaressus#a river in Thessaly##proposed#
urn:cite2:hmt:place.v1:place394#Peneus#or Peneius, a river in Thessaly#pleiades.stoa.org/places/541022#proposed#
urn:cite2:hmt:place.v1:place395#Pereia#a region in Thessaly#pleiades.stoa.org/places/541025#proposed#
urn:cite2:hmt:place.v1:place396#Adrasteia#or Adrastea, a region of Mysia#pleiades.stoa.org/places/511138#proposed#
urn:cite2:hmt:place.v1:place397#Apaesus#a town  on the coast of Troas, at the entrance of the Propontis, also known as Paesus##proposed#
urn:cite2:hmt:place.v1:place398#Pityeia#a town of Mysia##proposed#
urn:cite2:hmt:place.v1:place399#Tereia#a mountain of Mysia##proposed#
urn:cite2:hmt:place.v1:place400#Practius#a river in the Troad, north of Abydus#pleiades.stoa.org/places/501577#proposed#
urn:cite2:hmt:place.v1:place401#Larisa#or Larissa, a town in Asia Minor, near Cyme##proposed#
urn:cite2:hmt:place.v1:place402#Amydon#a city of the Paeonians, on the river Axius, in Macedonia##proposed#
urn:cite2:hmt:place.v1:place403#Axius#river in Macedonia#pleiades.stoa.org/places/491534#proposed#
urn:cite2:hmt:place.v1:place404#Cytorus#a town in Paphlagonia##proposed#
urn:cite2:hmt:place.v1:place405#Sesamon#or Sesamus, a town in Paphlagonia##proposed#
urn:cite2:hmt:place.v1:place406#Cromna#or Kromna, a locality in Paphlagonia#pleiades.stoa.org/places/844994#proposed#
urn:cite2:hmt:place.v1:place407#Aegialus#a town in Paphlagonia##proposed#
urn:cite2:hmt:place.v1:place408#Erythini#or Erythinoi, a place in Paphlagonia##proposed#
urn:cite2:hmt:place.v1:place409#Alybe#a country near Troy, productive of silver, homeland of the Halizones##proposed#
urn:cite2:hmt:place.v1:place410#Ascania#a district of Phrygia#pleiades.stoa.org/places/511165#proposed#
urn:cite2:hmt:place.v1:place411#Chios#Greek island off the coast of Anatolia#pleiades.stoa.org/places/550497#proposed#
urn:cite2:hmt:place.v1:place412#Smyrna#city in Asia Minor#pleiades.stoa.org/places/550771#proposed#
urn:cite2:hmt:place.v1:place413#Cyme#a costal town on Euboea##proposed#
urn:cite2:hmt:place.v1:place414#Meles#a river near Smyrna#pleiades.stoa.org/places/845016#proposed#
urn:cite2:hmt:place.v1:place415#Leontinoi#a town in Sicily, also called Leontini#pleiades.stoa.org/places/462279#proposed#
urn:cite2:hmt:place.v1:place416#Kapherides#promontory on which the Locrian Ajax died##proposed#
urn:cite2:hmt:place.v1:place417#Cyrene#Greek colony in Lybia#pleiades.stoa.org/places/373778#proposed#
urn:cite2:hmt:place.v1:place418#Brygias#a city in the Balkans, also Brygium##proposed#
urn:cite2:hmt:place.v1:place419#Leuke#The white island where Thetis and the Muses transport Achilles' body#pleiades.stoa.org/places/50091#proposed#
urn:cite2:hmt:place.v1:place420#Mytilene#major port on Lesbos#pleiades.stoa.org/places/550763#proposed#
urn:cite2:hmt:place.v1:place421#Olympia#site in the Peloponnese where the Olympic games were held#pleiades.stoa.org/places/570531#proposed#
urn:cite2:hmt:place.v1:place422#Othrys#mountain in central Greece in the southern part of Magnesia, home base of the Titans#pleiades.stoa.org/places/540994#proposed#
urn:cite2:hmt:place.v1:place423#Copais#a lake in lake in the center of Boeotia, also known as the Cephisian lake#pleiades.stoa.org/places/540715#proposed#
urn:cite2:hmt:place.v1:place424#Sigeion#city in the north-west of the Troad region located at the mouth of the Scamander#pleiades.stoa.org/places/550877#proposed#
urn:cite2:hmt:place.v1:place425#Rhoiteion#a city in the northern Troad bounded by the Simoeis and Ophryneion rivers#pleiades.stoa.org/places/550856#proposed#
urn:cite2:hmt:place.v1:place426#Pieria#city founded by Pierus in the southern part of Macedonia##proposed#
urn:cite2:hmt:place.v1:place427#Mt. Athos#A mountain in Greece that is linked to the Gigantomachy#pleiades.stoa.org/places/501366#proposed#
urn:cite2:hmt:place.v1:place428#Amathia#city founded by Amathus in the region called Emathia##proposed#
urn:cite2:hmt:place.v1:place429#Paphos#a city on Cyprus#pleiades.stoa.org/places/707596#proposed#
urn:cite2:hmt:place.v1:place430#Kos#island of the group of the Dodecanese in Caria, also spelled Cos##proposed#
urn:cite2:hmt:place.v1:place431#Teuthrania#City in Mysia#pleiades.stoa.org/places/845079#proposed#
urn:cite2:hmt:place.v1:place432#Pyrrha#an ancient settlement whose location is completely unknown#pleiades.stoa.org/places/543856#proposed#
urn:cite2:hmt:place.v1:place433#Epirus#An ancient region that included northwest parts of modern Greece and the southern tip of modern Albania#http://pleiades.stoa.org/places/530871#proposed#
urn:cite2:hmt:place.v1:place434#Balkans#geographical region of Southeast Europe, vague home of the Bryges##proposed#
urn:cite2:hmt:place.v1:place435#Mt. Oeta#A mountain of southern Phthiotis and northern Phocis in Greece, the site of Herakles' death#pleiades.stoa.org/places/540968#proposed#
urn:cite2:hmt:place.v1:place436#Kythnos# island in the Western Cyclades between Kea and Serifos#pleiades.stoa.org/places/570403#proposed#
urn:cite2:hmt:place.v1:place437#Sardinia#large island of the coast of Italy in the Mediterranean#pleiades.stoa.org/places/991344#proposed#
urn:cite2:hmt:place.v1:place438#Mt. Aetna#volcano on Sicily#pleiades.stoa.org/places/462077#proposed#
urn:cite2:hmt:place.v1:place439#Mt. Cragus#Kragos, mountain in Lycia#pleiades.stoa.org/places/638942#proposed#
urn:cite2:hmt:place.v1:place440#Pyrithlegethon#one of the rivers of the underworld##proposed#
urn:cite2:hmt:place.v1:place441#Corcyra#second largest of the Ionian Islands, modern day Corfu#pleiades.stoa.org/places/530834#proposed#
urn:cite2:hmt:place.v1:place442#Aphidna#Afidnes,  one of the twelve ancient towns of Attica; the place where Theseus left Helen after he had abducted her; later becomes the deme Aphidnes#pleiades.stoa.org/places/579873#proposed#
urn:cite2:hmt:place.v1:place443#Ismaros#Land of the Cicones, also known as Ismara or Ismaron#pleiades.stoa.org/places/507409#proposed#
urn:cite2:hmt:place.v1:place444#Sipylos#a mountain formerly in the heartland of the Lydians, modern day Mt. Spil#pleiades.stoa.org/places/550884#proposed#
urn:cite2:hmt:place.v1:place445#Melas Kolpos#the Black Gulf, one of the three seas around the island of Tenedos#pleiades.stoa.org/places/501513#proposed#
urn:cite2:hmt:place.v1:place446#Samothrace#an island in the northern Aegean#pleiades.stoa.org/places/501597#proposed#
urn:cite2:hmt:place.v1:place447#Rhyndacus#A river in northwestern Anatolia now known as the Mustafakemalpaşa River#pleiades.stoa.org/places/511401#proposed#
urn:cite2:hmt:place.v1:place448#Lampsacus#A city in the northern Troad#pleiades.stoa.org/places/501570#proposed#
urn:cite2:hmt:place.v1:place449#Krannon#also called Ephyra, a village in Thessaly#pleiades.stoa.org/places/540886#proposed#
urn:cite2:hmt:place.v1:place450#Kallikolone#a hill near Troy, on the Simois river#pleiades.stoa.org/places/550609#proposed#
urn:cite2:hmt:place.v1:place451#Naxos#the largest of the Cycladic islands#pleiades.stoa.org/places/599822#proposed#
urn:cite2:hmt:place.v1:place452#Taphios#the kingdom which Mentes rules#pleiades.stoa.org/places/531114#proposed#
urn:cite2:hmt:place.v1:place453#Saoce#a mountain on Samothrace, modern day Mt. Saos#pleiades.stoa.org/places/501600#proposed#
urn:cite2:hmt:place.v1:place454#Scepsis#an ancient settlement in the Troad#pleiades.stoa.org/places/550890#proposed#
urn:cite2:hmt:place.v1:place455#Cabesus#the home land of Othryoneus##proposed#
urn:cite2:hmt:place.v1:place456#Ilieis#a small village in the vicinity of Troy##proposed#
urn:cite2:hmt:place.v1:place457#Achelous#A river in Aetolia#https://pleiades.stoa.org/places/530768#proposed#
urn:cite2:hmt:place.v1:place458#Acheloos#A river in Phrygia, alternatively spelled Acheles or Acheleios; NOT the one in Aetolia#https://pleiades.stoa.org/places/550400#proposed#"""

    explore_homer_place_identifier = "urn:cite2:exploreHomer:place.v1:place"
    place_id = 1

    reader = csv.DictReader(cite_block.splitlines(), delimiter="#")
    rows = [r for r in reader]

    named_entity_rows = []
    cite_urn_lookup = {}
    url_to_urn_lookup = {}
    for entry, cts_urns in unique_georefs:
        extra = {}
        pleiades_uri = None
        for body in entry["body"]:
            if body.get("value").startswith("http://pleiades"):
                pleiades_uri = body["value"].split("http://")[1]
                break

        for body in entry["body"]:
            if body.get("purpose") == "tagging":
                extra["tagging"] = body["value"]

        for body in entry["body"]:
            if body.get("purpose") == "commenting":
                if "commenting" not in extra:
                    extra["commenting"] = body["value"]

        for body in entry["body"]:
            if body.get("purpose") == "georeferencing":
                geometry = body.get("geometry")
                if geometry:
                    coords_str = ", ".join(str(c) for c in geometry["coordinates"])
                    extra["coordinates"] = coords_str

        if pleiades_uri:
            cite_obj = next(
                iter(filter(lambda x: x["pleiades"] == pleiades_uri, rows)), None
            )
            if not cite_obj:
                cite_obj = url_to_urn_lookup.setdefault(pleiades_uri, {})
                if not cite_obj:
                    # cache requests
                    data = requests.get(f"https://{pleiades_uri}/json").json()
                    cite_obj.update(
                        {
                            "urn": f"{explore_homer_place_identifier}{place_id}",
                            "data": data,
                            "label": data["title"],
                        }
                    )
                    place_id += 1
                    time.sleep(0.1)

            cite_urn = cite_obj["urn"]
            named_entity_rows.append(
                {
                    "urn": cite_urn,
                    "label": cite_obj.get(
                        "label", cite_obj.get("data", {}).get("title")
                    ),
                    "description": cite_obj.get(
                        "description", cite_obj.get("data", {}).get("description")
                    ),
                    "data": next(logfmt.format(extra), ""),
                    "link": f"https://{pleiades_uri}",
                }
            )
            cite_urn_lookup[cite_urn] = cts_urns

    json.dump(
        url_to_urn_lookup,
        open("data/annotations/named-entities/raw/new_places.json", "w"),
        ensure_ascii=False,
        indent=2,
    )

    out_file = "data/annotations/named-entities/raw/new_places.csv"
    with open(out_file, "w", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter="#")
        for key, obj in url_to_urn_lookup.items():
            writer.writerow(
                [
                    obj["urn"],
                    obj["data"]["title"],
                    obj["data"]["description"],
                    key,
                    "proposed",
                ]
            )

    out_file = "data/annotations/named-entities/processed/entities/chiara_subset.csv"
    with open(out_file, "w", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=named_entity_rows[0].keys())
        writer.writeheader()
        for row in named_entity_rows:
            writer.writerow(row)

    standoff_rows = []
    for cite_urn, cts_urns in cite_urn_lookup.items():
        for cts_urn in cts_urns:
            standoff_rows.append(
                {
                    "named_entity_urn": cite_urn,
                    "ref": cts_urn[0],
                    "token_position": cts_urn[1],
                }
            )

    out_file = "data/annotations/named-entities/processed/standoff/tlg0012.tlg001.perseus-eng4.csv"
    with open(out_file, "w", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=standoff_rows[0].keys())
        writer.writeheader()
        for row in standoff_rows:
            writer.writerow(row)


if __name__ == "__main__":
    main()
