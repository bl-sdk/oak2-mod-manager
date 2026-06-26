#!/usr/bin/env python3
# ruff: noqa: S311

import subprocess
from functools import cache
from pathlib import Path
from random import Random

# Process to generate this list, for when dlc adds new ones:
# 1. Go to Loot Lemon's item lists
# 2. Array.from(document.querySelectorAll("div.db_item > div:nth-child(3)")).map(x => `"${x.innerText}"`).join()  # noqa: E501
# 3. Add each page to the list, ruff format, sort lines
# 4. Look for duplicates and remove them - regex `(".*"),\n    \1`. Currently:
#    - Collector
#    - Trooper
#    - Principal
UNIQUE_ITEM_NAMES = [
    "ARC-TAN",
    "Abyss",
    "Accumulator",
    "Acey May",
    "Adrenaline Pump",
    "Aegon's Dream",
    "Anarchy",
    "Artificer",
    "Asher's Rise",
    "Assuit",
    "Atling Gun",
    "Augmenter AF1000",
    "Autocannibal",
    "Avatar",
    "Barb'ara",
    "Besieger",
    "Big Banger",
    "Binger",
    "Bio-Robot",
    "Birt's Bees",
    "Bismuth-Tipped Dagger",
    "Blacksmith",
    "Blind Box",
    "Blockbuster",
    "Blood Analyzer",
    "Blood Moon",
    "Bloody Lumberjack",
    "Bod",
    "Body Counter",
    "Bombastic",
    "Bonnie and Clyde",
    "Boomslang",
    "Borstel Ballista",
    "Bottled Lightning",
    "Broken Wings",
    "Bubbles",
    "Budget Deity",
    "Bugbear",
    "Bully",
    "Buoy",
    "Buster",
    "Buzz Axe",
    "Champion",
    "Chaumurky",
    "Chuck",
    "Cindershelly",
    "Cold Shoulder",
    "Collector",
    "Compleation",
    "Complex Root",
    "Configuration",
    "Conflux",
    "Constable",
    "Convergence",
    "Cooler",
    "Countermeasure",
    "Crazed Earl",
    "Crow-Sourced",
    "Dancer",
    "Darkbeast",
    "Defibrillator",
    "Destructo Disco",
    "Devourer",
    "Director",
    "Disc Jockey",
    "Disruptor",
    "Divided Focus",
    "Doeshot",
    "Dog Movement",
    "Driver",
    "Eigenburst",
    "Elementalist",
    "Elpis Star",
    "Entangler",
    "Entropic",
    "Esgrimidor",
    "Evolver",
    "Extension",
    "Extra Medium",
    "Falke",
    "Fashionista",
    "Faulty Detonator",
    "Fearstalker",
    "Filántropo",
    "Finnity XXX-L",
    "Firebreak",
    "Firepot",
    "Firewerks",
    "First Impression",
    "Fisheye",
    "Flak Cannon",
    "Flash Cyclone",
    "Flashpan",
    "Fleabag",
    "Forge Master",
    "Forsaken Chaos",
    "Furnace",
    "Fuse",
    "G.M.R.",
    "Gamer",
    "Gamma Void",
    "Gatherer",
    "Geiger-Roid",
    "Generator",
    "Glacier",
    "Goalkeeper",
    "Golden God",
    "Gomie",
    "Goremaster",
    "Grenazerker",
    "Grim Sister",
    "Guardian Angel",
    "Gummy",
    "Hair Trigger",
    "Handcannon",
    "Hardpoint",
    "Hat Trick",
    "Healthraiser",
    "Heavyweight",
    "Heimdahl",
    "Hellfire",
    "Hellwalker",
    "Hemorrhage",
    "Hephaestian",
    "Herald",
    "Hero of Bullet",
    "Hoarder",
    "Honey Badger",
    "Hooligan",
    "Hopscotch",
    "Hot Slugger",
    "Hotshot",
    "Husky Friend",
    "Hydrator",
    "Ichor",
    "Icon",
    "Illusionist",
    "Inkling",
    "Inscriber",
    "Instigator",
    "Jackhammer",
    "Jail-Broken Gatling",
    "Jelly",
    "Jetsetter",
    "Juliet's Sparkle",
    "Kaleidosplode",
    "Kaoson",
    "Katagawa's Revenge",
    "Kickballer",
    "Kill Spring",
    "Kindread Spirits",
    "King's Gambit",
    "Ladykiller",
    "Lamplighter",
    "Lamé",
    "Laser Disker",
    "Laser-Cutter",
    "Lead Balloon",
    "Linebacker",
    "Lockjaw",
    "Looper",
    "Lucian's Flank",
    "Lucky Clover",
    "Ludopath",
    "Luty Madlad",
    "Maestro",
    "Mantra",
    "Matador's Match",
    "Mercredi",
    "Mercurious",
    "Midnight Defiance",
    "Misericorde",
    "Missilaser",
    "Multistrike",
    "Murmur",
    "Noisy Cricket",
    "Oak-Aged Cask",
    "Ohm I got",
    "Onion",
    "Onslaught",
    "Oscar Mike",
    "Ouroboros",
    "Overdriver",
    "Pacemaker",
    "Pandoran Memento",
    "Parallaxis",
    "Parasite",
    "Phantom Flame",
    "Phlebotomist",
    "Plasma Coil",
    "Plasmaphile",
    "Potato Thrower IV",
    "Prestidigitator",
    "Primadiem",
    "Prince Harming",
    "Principal",
    "Protean Cell",
    "Prowler",
    "Pumper",
    "Queen's Rest",
    "Quencher",
    "Quicksilver",
    "Quintain",
    "Rainbow Vomit",
    "Rainmaker",
    "Rangefinder",
    "Ravenfire",
    "Reactor",
    "Reaparición",
    "Recursive",
    "Reminisce",
    "Roach",
    "Roil",
    "Rooker",
    "Roulette",
    "Rounder",
    "Rowan's Charge",
    "Rowdy Rider",
    "Ruby's Grasp",
    "San Saba Songbird",
    "Scattershot",
    "Scientist",
    "Scion",
    "Scoot'n'Shoot",
    "Screwstonian",
    "Seventh Sense",
    "Shalashaska",
    "Shammy Kablammy",
    "Shatterwight",
    "Shiny War Paint",
    "Sho Kunai",
    "Sideshow",
    "Sidewinder",
    "Skeptic",
    "Skully",
    "Slippy",
    "Slugger",
    "Solar Temper",
    "Soul Survivor",
    "Sparky Shield",
    "Spinning Blade",
    "Sprezzatura",
    "Stalwart",
    "Star Helix",
    "Steward",
    "Stop Gap",
    "Stray",
    "Streamer",
    "Studfinder",
    "Sunspot",
    "Super Soldier",
    "Swarm",
    "Sweet Embrace",
    "Symmetry",
    "T.K's Wave",
    "Tankbuster",
    "Technomancer",
    "Teen Witch",
    "Tempest",
    "Timekeeper's New Shield",
    "Toile",
    "Transmitter",
    "Triple Bypass",
    "Trooper",
    "Truck",
    "UAV",
    "Undead Eye",
    "Undershield",
    "Unstable Kor",
    "Urchin",
    "Value-Add",
    "Valuepalooza",
    "Vamoose",
    "Viking",
    "Waterfall",
    "Watts 4 Dinner",
    "Whale",
    "Whiskey Foxtrot",
    "Windrider",
    "Wombo Combo",
    "X-Initiator",
    "X-Y Combo",
    "Y-Initiator",
    "Y-Z Nexus",
    "Z-Initiator",
    "Z-X Junction",
    "Zipper",
]

PREVIOUS_RELEASE_NAMES = [
    "Sprezzatura",
    "Valuepalooza",
]


@cache
def get_git_commit_hash(identifier: str | None = None) -> str:
    """
    Gets the full commit hash of the current git repo.

    Args:
        identifier: The identifier of the commit to get, or None to get the latest.
    Returns:
        The commit hash.
    """
    args = ["git", "show", "-s", "--format=%H"]
    if identifier is not None:
        args.append(identifier)

    return subprocess.run(
        args,
        cwd=Path(__file__).parent,
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf8",
    ).stdout.strip()


def pick_release_name(commit_hash: str, excludes: list[str] = PREVIOUS_RELEASE_NAMES) -> str:
    """
    Picks the name to use for a release.

    Args:
        commit_hash: The commit hash to pick the name of.
        excludes: The list of names to exclude.
    Returns:
        The release name.
    """
    # Think it's better to rely on an int than the string's hash method
    rng = Random(int(commit_hash, 16))
    while (name := rng.choice(UNIQUE_ITEM_NAMES)) in excludes:
        pass
    return name


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Picks the friendly name to use for the current release.",
    )
    parser.add_argument(
        "hash",
        nargs="?",
        default=None,
        help="The commit hash to base the name off of. If not given, retrieves from git.",
    )
    parser.add_argument(
        "--exclude",
        metavar="NAME",
        action="append",
        default=[],
        help="Excludes a name as if it were used in a previous release.",
    )
    parser.add_argument(
        "--ignore-previous-releases",
        action="store_true",
        help="Ignores all names which have been used in previous releases.",
    )
    args = parser.parse_args()

    commit_hash = get_git_commit_hash(args.hash)

    excludes = [] if args.ignore_previous_releases else PREVIOUS_RELEASE_NAMES
    excludes += args.exclude

    print(pick_release_name(commit_hash, excludes))  # noqa: T201
