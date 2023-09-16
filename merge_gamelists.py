import io
import xml.etree.ElementTree as ET
from xml.dom import minidom

platform = "wii"

source_xml = ET.parse(r"E:\EmulationStation-DE\.emulationstation\gamelists\%s\gamelist.xml" % platform)
destination_xml = ET.parse(r"E:\LaunchBox\Rom Export\roms\%s\gamelist.xml" % platform)
games_found = []
processed_games = 0

for game in source_xml.getroot().iter("game"):
    game_dict = dict()
    for item in list(game):
        game_dict[item.tag] = item.text
    rom_path = repr(game_dict["path"])
    matched_games = destination_xml.getroot().findall(f'./game/[path={rom_path}]')

    if len(matched_games) == 0:
        games_found.append(game_dict)
        processed_games += 1
        continue

    matched_game = matched_games[0]
    matched_game_dict = dict()
    for item in list(matched_game):
        matched_game_dict[item.tag] = item.text

    def replace_element(tag, force=True):
        if matched_game_dict.get(tag) is None:
            return
        value = matched_game_dict[tag]

        if game_dict.get(tag) is not None and force is False:
            return
        else:
            game_dict[tag] = value
            return

    replace_element("rating")
    replace_element("players")
    replace_element("genre")
    replace_element("releasedate")
    replace_element("developer")
    replace_element("publisher")
    replace_element("desc", False)

    games_found.append(game_dict)
    processed_games += 1

for game in destination_xml.getroot().iter("game"):
    game_dict = dict()
    for item in list(game):
        game_dict[item.tag] = item.text
    rom_path = repr(game_dict["path"])

    matched_games = source_xml.getroot().findall(f'./game/[path={rom_path}]')

    if len(matched_games) == 0:
        games_found.append(game_dict)
        processed_games += 1
        continue


top = ET.Element("gameList")
for game in games_found:
    child = ET.SubElement(top, "game")
    for key in game.keys():
        child_content = ET.SubElement(child, key)
        child_content.text = game[key]

try:
    xmlstr = minidom.parseString(ET.tostring(top)).toprettyxml()
    gamelist_xml = "gamelist.xml"
    this_output_xml_filename = r"E:\EmulationStation-DE\gamelist.xml"
    with io.open(this_output_xml_filename, "w", encoding="utf-8") as f:
        f.write(xmlstr)

except Exception as e:
    print(e)
    print(f"\tERROR writing gamelist XML")

print("----------------------------------------------------------------------")
print(
    f"Created gamelist XMLs with {processed_games :,} games"
)
print("----------------------------------------------------------------------")
