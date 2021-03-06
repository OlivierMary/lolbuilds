import requests
import json
import os
from bs4 import BeautifulSoup


def get_champions():
    body = requests.get("https://www.champion.gg/").text

    soup = BeautifulSoup(body, "html.parser")

    champions = []

    for champion_div in soup.find_all("div", {"class": "champ-height"}):
        champion = {
            "name": "",
            "id": "",
            "roles": []
        }

        champion["name"] = champion_div.find(
            "div", {"class": "champ-index-img"}).get("class")[1]

        champion["id"] = champion_div.find(
            "div", {"class": "tsm-tooltip"}).get("data-id")

        role_rank = 10
        for role in champion_div.find_all("a"):
            if role.get("style") == "display:block":
                champion["roles"].append((role.string.strip(), role_rank))
                role_rank -= 1

        champions.append(champion)

    return champions


def get_items_and_skill_order(champion):

    items = {}

    for role, role_rank in champion["roles"]:

        body = requests.get(
            "https://www.champion.gg/champion/" + champion["name"] + "/" + role).text
        soup = BeautifulSoup(body, "html.parser")

        role_items = {
            "rank": role_rank,
            "frequent": {
                "full": [],
                "starters": [],
                "skill_order": None
            },
            "highest": {
                "full": [],
                "starters": [],
                "skill_order": None
            }
        }

        skill_order = get_skill_order(soup)
        role_items["frequent"]["skill_order"] = skill_order["frequent"]
        role_items["highest"]["skill_order"] = skill_order["highest"]

        try:
            for a in soup.find("h2", string="Most Frequent Completed Build").find_next_sibling("div").find_all("a"):
                role_items["frequent"]["full"].append(
                    a.find("img").get("data-id"))

            for a in soup.find("h2", string="Highest Win % Starters").find_next_sibling("div").find_all("a"):
                role_items["highest"]["starters"].append(
                    a.find("img").get("data-id"))

            for a in soup.find("h2", string="Highest Win % Completed Build").find_next_sibling("div").find_all("a"):
                role_items["highest"]["full"].append(
                    a.find("img").get("data-id"))

            for a in soup.find("h2", string="Most Frequent Starters").find_next_sibling("div").find_all("a"):
                role_items["frequent"]["starters"].append(
                    a.find("img").get("data-id"))

        except:
            continue

        items[role] = role_items

    return items


def get_skill_order(soup):

    skill_order = {
        "frequent": [],
        "highest": []
    }

    for counter, skill_div in enumerate(soup.find_all("div", {"class": "skill-order"})):
        levels = skill_div.find("div", {"class": "skill"})
        q = levels.find_next_sibling("div", {"class": "skill"})
        w = q.find_next_sibling("div", {"class": "skill"})
        e = w.find_next_sibling("div", {"class": "skill"})
        r = e.find_next_sibling("div", {"class": "skill"})

        skills = {
            "q": q,
            "w": w,
            "e": e,
            "r": r
        }

        for skill, div in skills.items():
            skills[skill] = div.find(
                "div", {"class": "skill-selections"}).find("div")

        for level in range(18):
            for skill, div in skills.items():
                if div.get("class") == ["selected"]:
                    skill_order["frequent" if counter ==
                                0 else "highest"].append(skill)
                    for skill, div in skills.items():
                        skills[skill] = div.find_next_sibling("div")
                    break

    return skill_order


def format_skill_order(skill_order):
    skills = {
        "q": 0,
        "w": 0,
        "e": 0,
    }

    output = []

    for skill in skill_order:
        if skill in skills:
            skills[skill] += 1
        for skill, count in skills.items():
            if count == 5:
                output.append(skill.upper())
                skills[skill] = 0

    first_skills = ".".join(skill_order[:4]).upper()

    try:
        return (f"{first_skills}, {output[0]}>{output[1]}>{output[2]}")
    except:
        return "Not enough data for this skill order"

def save_item_set(role, champion, items):

    item_set = {
        "title": champion + " " + role,
        "type": "custom",
        "map": "any",
        "mode": "any",
        "priority": False,
        "sortrank": items["rank"],
        "champion": champion,
        "blocks": []
    }

    # frequent starters
    frequent_starters_dict = {}
    for item_id in items["frequent"]["starters"]:
        if not item_id in frequent_starters_dict:
            frequent_starters_dict[item_id] = 1
        else:
            frequent_starters_dict[item_id] += 1

    frequent_starters = []
    for item_id, count in frequent_starters_dict.items():
        frequent_starters.append(
            {
                "count": count,
                "id": item_id
            }
        )

    item_set["blocks"].append(
        {
            "items": frequent_starters,
            "type": "Most Frequent Starters"
        }
    )

    # highest win % starters
    highest_starters_dict = {}
    for item_id in items["highest"]["starters"]:
        if not item_id in highest_starters_dict:
            highest_starters_dict[item_id] = 1
        else:
            highest_starters_dict[item_id] += 1

    highest_starters = []
    for item_id, count in highest_starters_dict.items():
        highest_starters.append(
            {
                "count": count,
                "id": item_id
            }
        )

    item_set["blocks"].append(
        {
            "items": highest_starters,
            "type": "Highest Win % Starters"
        }
    )

    # frequent full build
    frequent_full_dict = {}
    for item_id in items["frequent"]["full"]:
        if not item_id in frequent_full_dict:
            frequent_full_dict[item_id] = 1
        else:
            frequent_full_dict[item_id] += 1

    frequent_full = []
    for item_id, count in frequent_full_dict.items():
        frequent_full.append(
            {
                "count": count,
                "id": item_id
            }
        )

    item_set["blocks"].append(
        {
            "items": frequent_full,
            "type": "Most Frequent Build"
        }
    )

    # highest win % full build
    highest_full_dict = {}
    for item_id in items["highest"]["full"]:
        if not item_id in highest_full_dict:
            highest_full_dict[item_id] = 1
        else:
            highest_full_dict[item_id] += 1

    highest_full = []
    for item_id, count in highest_full_dict.items():
        highest_full.append(
            {
                "count": count,
                "id": item_id
            }
        )

    item_set["blocks"].append(
        {
            "items": highest_full,
            "type": "Highest Win % Build"
        }
    )

    item_set["blocks"].append(
        {
            "items": [
                {
                    "count": 1,
                    "id": "2003"
                },
                {
                    "count": 1,
                    "id": "2031"
                },
                {
                    "count": 1,
                    "id": "2055"
                },
                {
                    "count": 1,
                    "id": "2138"
                },
                {
                    "count": 1,
                    "id": "2139"
                },
                {
                    "count": 1,
                    "id": "2140"
                }
            ],
            "type": "Consumables | Frequent: " + format_skill_order(items["frequent"]["skill_order"])
        }
    )

    item_set["blocks"].append(
        {
            "items": [
                {
                    "count": 1,
                    "id": "3340"
                },
                {
                    "count": 1,
                    "id": "3363"
                },
                {
                    "count": 1,
                    "id": "3364"
                }
            ],
            "type": "Trinkets | Wins: " + format_skill_order(items["highest"]["skill_order"])
        }
    )

    riot_champ_path = f"C:/Riot Games/League of Legends/Config/Champions/{champion}"
    riot_path = f"C:/Riot Games/League of Legends/Config/Champions/{champion}/Recommended"
    try:
        os.mkdir(riot_champ_path)
    except FileExistsError:
        pass

    try:
        os.mkdir(riot_path)
    except FileExistsError:
        pass

    champ_path = os.path.join(riot_path, f"ChampionGG_{role}.json")
    
    f = open(champ_path, "w")
    f.write(json.dumps(item_set))
    f.close()


def main():
    champions = get_champions()
    for champ in champions:
        print("Processing " + champ["name"])
        all_items = get_items_and_skill_order(champ)
        for role, items in all_items.items():
            save_item_set(role, champ["name"],  items)


if __name__ == "__main__":
    main()
