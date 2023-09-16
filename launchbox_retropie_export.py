import glob
import io
import os
import configparser
from shutil import copy
import xml.etree.ElementTree as ET
from xml.dom import minidom

config = configparser.RawConfigParser()
config.read('config.cfg')
platforms_dict = dict(config.items('Platforms'))

# version 1.2.0
# The path to your Launchbox folder.
lb_dir = r"E:\LaunchBox"

# Where to put the exported roms, images and xmls
# Copy the gamelist, roms and images to /home/<user>/RetroPie/roms. Gamelists are now saved inside each platform dir.
output_dir = r"E:\LaunchBox\Rom Export"

# Restrict export to only Launchbox Favorites
favorites_only = False

# Retropie running on an old Pi needs small images. Images with a height or width above 500 pixels will be reduced with their aspect ratio preserved. If generating for Onion OS the images will be 250 px.
reduce_image_size = False

# Choose platforms (comment/uncomment as needed)
# The first string in each pair is the Launchbox platform filename, the second is the output platform folder name
platforms = dict()
# platforms["Atari 2600"] = "atari2600"
# platforms["Atari 7800"] = "atari7800"
# platforms["Atari Lynx"] = "atarilynx"
# platforms["Nintendo 64"] = "n64"
# platforms["Nintendo Famicom Disk System"] = "fds"
# platforms["Nintendo Game & Watch"] = "gw"
# platforms["Nintendo Game Boy"] = "gb"
# platforms["Nintendo Game Boy Color"] = "gbc"
# platforms["Nintendo Game Boy Advance"] = "gba"
# platforms["Nintendo NES"] = "nes"
# platforms["Super Nintendo Entertainment System"] = "snes"
# platforms["Nintendo GameCube"] = "gc"
# platforms["Nintendo Switch"] = "switch"
platforms["Nintendo Wii"] = "wii"
# platforms["Nintendo DS"] = "nds"
# platforms["Nintendo 3DS"] = "n3ds"
# platforms["Sega 32x"] = "sega32x"
# platforms["Sega Game Gear"] = "gamegear"
# platforms["Sega CD"] = "segacd"
# platforms["Sega Genesis"] = "genesis"
# platforms["Sega Mega Drive"] = "megadrive"
# platforms["Sega Master System"] = "mastersystem"
# platforms["Sega Saturn"] = "saturn"
# platforms["Sega Dreamcast"] = "dreamcast"
# platforms["Sega SG-1000"] = "sg-1000"
# platforms["SNK Neo Geo AES"] = "neogeo"
# platforms["SNK Neo Geo Pocket Color"] = "ngpc"
# platforms["Sony Playstation"] = "psx"
# platforms["Sony Playstation 2"] = "ps2"
# platforms["Sony Playstation 3"] = "ps3"
# platforms["Sony PSP"] = "psp"
# platforms["TurboGrafx-16"] = "pcengine"
# platforms["WonderSwan Color"] = "wonderswancolor"


### edits should not be required below here ###

processed_games = 0
processed_platforms = 0
media_copied = 0

for platform in platforms.keys():
    platform_lb = platform
    platform_rp = platforms[platform]
    lb_platform_xml = r"%s\Data\Platforms\%s.xml" % (lb_dir, platform_lb)
    lb_image_dir = r"%s\images\%s\Box - Front" % (lb_dir, platform_lb)
    lb_3dbox_dir = r"%s\images\%s\Box - 3D" % (lb_dir, platform_lb)
    lb_backcover_dir = r"%s\images\%s\Box - Back" % (lb_dir, platform_lb)
    lb_cover_dir = r"%s\images\%s\Box - Front" % (lb_dir, platform_lb)
    lb_fanart_dir = r"%s\images\%s\Fanart - Background" % (lb_dir, platform_lb)
    lb_wheel_dir = r"%s\images\%s\Clear Logo" % (lb_dir, platform_lb)
    # lb_physicalmedia_dir = r"%s\images\%s\Cart - Front" % (lb_dir, platform_lb)
    lb_physicalmedia_dir = r"%s\images\%s\Disc" % (lb_dir, platform_lb)
    lb_screenshot_dir = r"%s\images\%s\Screenshot - Gameplay" % (lb_dir, platform_lb)
    lb_video_dir = r"%s\videos\%s" % (lb_dir, platform_lb)
    output_roms = r"%s\roms" % output_dir
    output_roms_platform = r"%s\%s" % (output_roms, platform_rp)
    output_gamelists = r"%s\gamelists" % output_dir
    output_gamelists_platform = r"%s\%s" % (output_gamelists, platform_rp)
    output_image_dir = r"%s\images" % output_roms_platform
    output_3dbox_dir = r"%s\3dboxes" % output_roms_platform
    output_backcover_dir = r"%s\backcovers" % output_roms_platform
    output_cover_dir = r"%s\covers" % output_roms_platform
    output_fanart_dir = r"%s\fanart" % output_roms_platform
    output_marquee_dir = r"%s\marquees" % output_roms_platform
    output_screenshots_dir = r"%s\screenshots" % output_roms_platform
    output_video_dir = r"%s\videos" % output_roms_platform

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    if not os.path.isdir(output_roms):
        os.makedirs(output_roms)

    if not os.path.isdir(output_roms_platform):
        os.makedirs(output_roms_platform)

    xmltree = ET.parse(lb_platform_xml)
    games_found = []
    images_3dbox = []
    images_backcover = []
    images_cover = []
    images_fanart = []
    images_marquee = []
    images_physicalmedia = []
    images_screenshots = []
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
    ]

    for image_map in image_maps:
        for fname in glob.glob(r"%s\**" % image_map["lb_media_dir"], recursive=True):
            img_path = os.path.join(image_map["lb_media_dir"], fname)
            if not os.path.isdir(img_path):
                image_map["lb_media_files"].append(img_path)

    def get_image(game_name, image_files):
        game_name = game_name.replace(":", "_")
        game_name = game_name.replace("'", "_")
        game_name = game_name.replace("/", "_")
        game_name = game_name.replace("*", "_")
        for image_path in image_files:
            image_name = os.path.basename(r"%s" % image_path)
            if (
                image_name.startswith(game_name + "-01.")
                or image_name.lower() == game_name.lower() + ".mp4"
            ):
                return [image_name, image_path]

    def save_image(original_path, output_dir, rom_path):
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        filename = os.path.basename(r"%s" % rom_path)
        extension = os.path.splitext(original_path)[1]
        if extension == ".jpg" and "fanart" not in output_dir:
            extension = ".png"
        filename = os.path.splitext(filename)[0] + extension

        output_path = os.path.join(output_dir, filename)
        copy(r"%s" % original_path, r"%s" % output_path)
        return os.path.basename(output_path)

    for game in xmltree.getroot().iter("Game"):
        this_game = dict()
        try:
            favorite_element = game.find("Favorite")
            if (favorites_only is False) or (
                favorites_only is True
                and favorite_element is not None
                and favorite_element.text == "true"
            ):
                print("%s: %s" % (platform_lb, game.find("Title").text))
                rom_path = game.find("ApplicationPath").text
                this_game["path"] = "./" + os.path.basename(
                    r"%s" % game.find("ApplicationPath").text
                )
                this_game["name"] = game.find("Title").text
                if not game.find("Notes") is None:
                    this_game["desc"] = game.find("Notes").text
                for image_map in image_maps:
                    image_info = get_image(
                        this_game["name"], image_map["lb_media_files"]
                    )

                    if image_info is None:
                        print(f'\tNo {image_map["type"]} found for {this_game["name"]}')
                        if (image_map["xmltag"] is not None):
                            this_game[image_map["xmltag"]] = ""
                        continue

                    image_file = image_info[0]
                    image_path = image_info[1]
                    new_image_filename = save_image(
                        image_path,
                        output_roms_platform + os.sep + image_map["output_dir"],
                        rom_path,
                    )
                    if (image_map["xmltag"] is not None):
                        this_game[image_map["xmltag"]] = (
                            "./" + image_map["output_dir"] + "/" + new_image_filename
                        )
                    media_copied += 1
                if not game.find("CommunityStarRating") is None:
                    this_game["rating"] = str(
                        (round(float(game.find("CommunityStarRating").text) * 2 / 10, 1))
                    )
                if not game.find("ReleaseDate") is None:
                    this_game["releasedate"] = (
                        game.find("ReleaseDate").text.replace("-", "").split("T")[0]
                        + "T000000"
                    )
                if not game.find("Developer") is None:
                    this_game["developer"] = game.find("Developer").text
                if not game.find("Publisher") is None:
                    this_game["publisher"] = game.find("Publisher").text
                if not game.find("Genre") is None:
                    this_game["genre"] = game.find("Genre").text
                if not game.find("MaxPlayers") is None:
                    max_players = game.find("MaxPlayers").text
                    if max_players == "1":
                        this_game["players"] = "1"
                    elif max_players == "0":
                        this_game["players"] = "1+"
                    else:
                        this_game["players"] = "1-" + max_players
                games_found.append(this_game)
                # copy(rom_path, output_roms_platform)
                # copy(os.path.join(lb_dir, rom_path), output_roms_platform)
                processed_games += 1
        except Exception as e:
            print(e)

    top = ET.Element("gameList")
    for game in games_found:
        child = ET.SubElement(top, "game")
        for key in game.keys():
            child_content = ET.SubElement(child, key)
            child_content.text = game[key]

    try:
        xmlstr = minidom.parseString(ET.tostring(top)).toprettyxml()
        gamelist_xml = "gamelist.xml"
        this_output_xml_filename = output_roms_platform + os.sep + gamelist_xml
        with io.open(this_output_xml_filename, "w", encoding="utf-8") as f:
            f.write(xmlstr)
        processed_platforms += 1
    except Exception as e:
        print(e)
        print(f"\tERROR writing gamelist XML for {platform}")


print("----------------------------------------------------------------------")
print(
    f"Created {processed_platforms :,} gamelist XMLs and copied {media_copied :,} media files from {processed_games :,} games"
)
print("----------------------------------------------------------------------")
