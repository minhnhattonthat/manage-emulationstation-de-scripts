import glob
import io
import os
import configparser
import re
import json
from shutil import copy
import xml.etree.ElementTree as ET
from xml.dom import minidom

config = configparser.RawConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
config.read("config.ini")

# version 1.2.0
# The path to your Launchbox folder.
lb_dir = config["Paths"]["LaunchboxDirectory"]

# Where to put the exported images and xmls
output_dir = config["Paths"]["OutputDirectory"]

# Where EmulationStation is installed
es_dir = config["Paths"]["EmulationStationDirectory"]
roms_dir = config["Paths"]["ROMsDirectory"]

# Restrict export to only Launchbox Favorites
favorites_only = config["Filters"].getboolean("FavoritesOnly")

platforms = config["Filters"].getlist("Platforms")

overwrite_image_types = config["MediaOptions"].getlist("OverwriteImageTypes")

overwrite_fields = config["GamelistOptions"].getlist("OverwriteFields")
should_merge_with_emulation_station = config["GamelistOptions"]["MergeWithEnulationStation"]

# The first string in each pair is the EmulationStation platform folder name,
# the second is the Launchbox platform folder name
PLATFORMS_MAP = {}
with open('platforms.json', encoding='utf-8') as f:
    PLATFORMS_MAP = json.load(f)
    f.close()

DISC_PLATFORM = ["dreamcast", "fds", "gc", "megacd", "neogeocd", "ps2", "ps3", "ps4", "psp", "psx", "saturn", "saturnjp", "segacd", "steam", "wii", "wiiu"]

### edits should not be required below here ###

processed_games = 0
processed_platforms = 0
media_copied = 0

for platform_rp in platforms:
    platform_lb = PLATFORMS_MAP[platform_rp]
    lb_platform_xml = fr"{lb_dir}\Data\Platforms\{platform_lb}.xml"
    lb_image_dir = fr"{lb_dir}\Images\{platform_lb}\Box - Front"
    lb_3dbox_dir = fr"{lb_dir}\Images\{platform_lb}\Box - 3D"
    lb_backcover_dir = fr"{lb_dir}\Images\{platform_lb}\Box - Back"
    lb_fanart_dir = fr"{lb_dir}\Images\{platform_lb}\Fanart - Background"
    lb_wheel_dir = fr"{lb_dir}\Images\{platform_lb}\Clear Logo"
    lb_physicalmedia_dir = fr"{lb_dir}\Images\{platform_lb}\Disc" if platform_rp in DISC_PLATFORM else fr"{lb_dir}\Images\{platform_lb}\Cart - Front"
    if platform_rp == "steam":
        lb_cover_dir = fr"{lb_dir}\Images\{platform_lb}\Steam Poster"
        lb_screenshot_dir = fr"{lb_dir}\Images\{platform_lb}\Steam Screenshot"
    else:
        lb_cover_dir = fr"{lb_dir}\Images\{platform_lb}\Box - Front"
        lb_screenshot_dir = fr"{lb_dir}\Images\{platform_lb}\Screenshot - Gameplay"
    lb_titlescreens_dir = fr"{lb_dir}\Images\{platform_lb}\Screenshot - Game Title"
    lb_video_dir = fr"{lb_dir}\Videos\{platform_lb}"
    output_media_platform = fr"{output_dir}\downloaded_media\{platform_rp}"
    output_gamelists_platform = fr"{output_dir}\gamelists\{platform_rp}"
    output_3dbox_dir = fr"{output_media_platform}\3dboxes"
    output_backcover_dir = fr"{output_media_platform}\backcovers"
    output_cover_dir = fr"{output_media_platform}\covers"
    output_fanart_dir = fr"{output_media_platform}\fanart"
    output_marquee_dir = fr"{output_media_platform}\marquees"
    output_screenshots_dir = fr"{output_media_platform}\screenshots"
    output_titlescreens_dir = fr"{output_media_platform}\titlescreens"
    output_video_dir = fr"{output_media_platform}\videos"

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    if not os.path.isdir(output_media_platform):
        os.makedirs(output_media_platform)

    if not os.path.isdir(output_gamelists_platform):
        os.makedirs(output_gamelists_platform)

    xmltree = ET.parse(lb_platform_xml)
    games_found = []
    images_3dbox = []
    images_backcover = []
    images_cover = []
    images_fanart = []
    images_marquee = []
    images_physicalmedia = []
    images_screenshots = []
    images_titlescreens = []
    videos = []
    images = []

    image_maps = [
        {
            "type": "3d box",
            "xmltag": None,
            "output_dir": "3dboxes",
            "lb_media_dir": lb_3dbox_dir,
            "lb_media_files": images_3dbox,
        },
        {
            "type": "backcover",
            "xmltag": None,
            "output_dir": "backcovers",
            "lb_media_dir": lb_backcover_dir,
            "lb_media_files": images_backcover,
        },
        {
            "type": "cover",
            "xmltag": None,
            "output_dir": "covers",
            "lb_media_dir": lb_cover_dir,
            "lb_media_files": images_cover,
        },
        {
            "type": "fanart",
            "xmltag": None,
            "output_dir": "fanart",
            "lb_media_dir": lb_fanart_dir,
            "lb_media_files": images_fanart,
        },
        {
            "type": "marquee",
            "xmltag": None,
            "output_dir": "marquees",
            "lb_media_dir": lb_wheel_dir,
            "lb_media_files": images_marquee,
        },
        {
            "type": "physicalmedia",
            "xmltag": None,
            "output_dir": "physicalmedia",
            "lb_media_dir": lb_physicalmedia_dir,
            "lb_media_files": images_physicalmedia,
        },
        {
            "type": "screenshot",
            "xmltag": None,
            "output_dir": "screenshots",
            "lb_media_dir": lb_screenshot_dir,
            "lb_media_files": images_screenshots,
        },
        {
            "type": "titlescreen",
            "xmltag": None,
            "output_dir": "titlescreens",
            "lb_media_dir": lb_titlescreens_dir,
            "lb_media_files": images_titlescreens,
        },
    ]

    for image_map in image_maps:
        for fname in glob.glob(fr"{image_map['lb_media_dir']}\**", recursive=True):
            img_path = os.path.join(image_map["lb_media_dir"], fname)
            if not os.path.isdir(img_path):
                image_map["lb_media_files"].append(img_path)

    def get_image(game_name, image_files):
        name = game_name.replace(":", "_").replace("'", "_").replace("/", "_").replace("*", "_")
        for image_path in image_files:
            image_name = os.path.basename(r"%s" % image_path)
            if (
                image_name.startswith(name + "-01.")
                or image_name.startswith(name + "-02.")
                or image_name.lower() == name.lower() + ".mp4"
            ):
                return [image_name, image_path]

    def is_image_existed(output_dir, rom_filename):
        name = glob.escape(rom_filename)
        output_path = os.path.join(output_dir, name)
        result = glob.glob(fr"{output_path}.*")
        # output_path = glob.escape(output_path)
        return result

    def save_image(original_path, output_dir, rom_filename):
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        extension = os.path.splitext(original_path)[1]
        if "fanart" in output_dir:
            extension = ".jpg"
        elif "video" not in output_dir:
            extension = ".png"
        filename = rom_filename + extension

        output_path = os.path.join(output_dir, filename)
        copy(r"%s" % original_path, r"%s" % output_path)
        return os.path.basename(output_path)

    for game in xmltree.getroot().iter("Game"):
        this_game = dict()
        try:
            game_name = game.find('Title').text
            print(f"{platform_lb}: {game_name}")
            if platform_rp == "steam":
                if game.find('Source').text != "Steam":
                    continue
                rom_filename = game_name.replace(":", "").replace("'", "").replace("/", "").replace("*", "")
                rom_path = fr'./{rom_filename}.url'
            else:
                rom_path = "./" + os.path.basename(game.find("ApplicationPath").text)
                rom_filename = os.path.splitext(os.path.basename(rom_path))[0]
            this_game["path"] = rom_path
            this_game["name"] = game_name
            if not game.find("Notes") is None:
                this_game["desc"] = game.find("Notes").text
            for image_map in image_maps:
                image_info = get_image(this_game["name"], image_map["lb_media_files"])

                if image_info is None:
                    print(f'\tNo {image_map["type"]} found for {this_game["name"]}')
                    if image_map["xmltag"] is not None:
                        this_game[image_map["xmltag"]] = ""
                    continue

                image_file = image_info[0]
                image_path = image_info[1]

                if image_map["output_dir"] not in overwrite_image_types and is_image_existed(
                    output_media_platform + os.sep + image_map["output_dir"],
                    rom_filename,
                ):
                    print(f'\t{image_map["type"]} already existed for {this_game["name"]}')
                    continue

                new_image_filename = save_image(
                    image_path,
                    output_media_platform + os.sep + image_map["output_dir"],
                    rom_filename,
                )
                if image_map["xmltag"] is not None:
                    this_game[image_map["xmltag"]] = (
                        "./" + image_map["output_dir"] + "/" + new_image_filename
                    )
                media_copied += 1
            if game.find("CommunityStarRating") is not None:
                this_game["rating"] = str(
                    (round(float(game.find("CommunityStarRating").text) * 2 / 10, 1))
                )
            if game.find("ReleaseDate") is not None:
                this_game["releasedate"] = (
                    game.find("ReleaseDate").text.replace("-", "").split("T")[0]
                    + "T000000"
                )
            if game.find("Developer") is not None:
                this_game["developer"] = game.find("Developer").text
            if game.find("Publisher") is not None:
                this_game["publisher"] = game.find("Publisher").text
            if game.find("Genre") is not None:
                this_game["genre"] = game.find("Genre").text
            if game.find("MaxPlayers") is not None:
                max_players = game.find("MaxPlayers").text
                if max_players == "1":
                    this_game["players"] = "1"
                elif max_players == "0":
                    this_game["players"] = "1+"
                else:
                    this_game["players"] = "1-" + max_players
            if game.find("SortTitle") is not None:
                this_game["sortname"] = game.find("SortTitle").text
            games_found.append(this_game)
            # copy(rom_path, output_roms_platform)
            # copy(os.path.join(lb_dir, rom_path), output_roms_platform)
            processed_games += 1
        except Exception as e:
            print(e)

    if should_merge_with_emulation_station is False:
        alternative_emulator_element = None
        games_output = games_found
    else:
        ##--Start merge gamelist--##
        source_root = ET.Element("gameList")
        alternative_emulator_element = None
        games_output = []
        try:
            with open(fr"{es_dir}\.emulationstation\gamelists\{platform_rp}\gamelist.xml", encoding="utf-8") as f:
                xml = f.read()
            doc = ET.fromstring(re.sub(r"(<\?xml[^>]+\?>)", r"\1<root>", xml) + "</root>")
            source_root = doc.find("gameList")
            alternative_emulator_element = doc.find("alternativeEmulator")
        except ET.ParseError as e:
            print(e)
            print("gamelist.xml not existed.")

        for game in source_root.iter("game"):
            game_dict = dict()
            for item in list(game):
                game_dict[item.tag] = item.text
            rom_path = repr(game_dict["path"])

            filename = os.path.splitext(os.path.basename(r"%s" % rom_path))[0]
            filename = glob.escape(filename)
            if not glob.glob(fr"{roms_dir}\{platform_rp}\{filename}.*"):
                print(f"No game found at {rom_path}")
                continue

            matched_game_dict = next((x for x in games_found if repr(x["path"]) == rom_path), None)

            if matched_game_dict is None:
                games_output.append(game_dict)
                continue

            def update_element(tag):
                overwrite = tag in overwrite_fields
                if matched_game_dict.get(tag) is None:
                    return
                value = matched_game_dict[tag]

                if overwrite is False and game_dict.get(tag) is not None:
                    return

                game_dict[tag] = value
                return

            update_element("rating")
            update_element("players")
            update_element("genre")
            update_element("releasedate")
            update_element("developer")
            update_element("publisher")
            update_element("desc")
            update_element("sortname")

            games_output.append(game_dict)

        for game_dict in games_found:
            rom_path = repr(game_dict["path"])

            matched_games = source_root.findall(f'./game/[path={rom_path}]')

            if len(matched_games) == 0:
                games_output.append(game_dict)
                continue
        ##--End merge gamelist--##

    games_output.sort(key=lambda i: i["path"])
    top = ET.Element("gameList")
    for game in games_output:
        child = ET.SubElement(top, "game")
        for key in game.keys():
            child_content = ET.SubElement(child, key)
            child_content.text = game[key]

    try:
        xmlstr = minidom.parseString(ET.tostring(top)).toprettyxml()
        if alternative_emulator_element is not None:
            add_element = ET.tostring(alternative_emulator_element).decode()
            add_element = r"\n" + add_element.removesuffix("\n")
            xmlstr = re.sub(r"(<\?xml[^>]+\?>)", fr"\1{add_element}", xmlstr)
        this_output_xml_filename = output_gamelists_platform + os.sep + "gamelist.xml"
        with io.open(this_output_xml_filename, "w", encoding="utf-8") as f:
            f.write(xmlstr)
        processed_platforms += 1
    except Exception as e:
        print(e)
        print(f"\tERROR writing gamelist XML for {platform_lb}")


print("----------------------------------------------------------------------")
print(
    f"Created {processed_platforms :,} gamelist XMLs and copied {media_copied :,} media files from {processed_games :,} games"
)
print("----------------------------------------------------------------------")
