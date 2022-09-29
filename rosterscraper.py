import PySimpleGUI as sg
from pathlib import Path
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import validators

# This hashmap matches the netloc (example.com) of a WMT website team url to two tuples:
# the first represents the BeautifulSoup find parameter for its athlete roster
# and the second represents the the BeautifulSoup find_all parameter for every athlete within the roster
team_hashmap = {
    "arkansasrazorbacks.com": [("table"), ("tr")],
    "vucommodores.com": [("table"), ("tr")],
    "clemsontigers.com": [("ul", {"id": "person__table"}), ("li", {"class": "person__item"})],
    "und.com": [("div", {"class": "featured__list"}), ("div", {"class": "player col-lg-3 col-sm-6 col-xs-12"})],
    "ohiostatebuckeyes.com": [("div", {"class": "roster-photo"}), ("div", {"class": "ohio-square-blocks__item col-lg-3 col-md-3 col-sm-4 col-xs-12"})],
    "ramblinwreck.com": [("section", {"class": "roster__list"}), ("div", {"class": "roster__list_item"})],
    "seminoles.com": [("div", {"id": "roster"}), ("div", {"class": "thumbnail"})],
    "hawkeyesports.com": [("div", {"id": "players"}), ("div", {"itemprop": "athlete"})],
    "kuathletics.com": [("div", {"id": "players"}), ("div", {"itemprop": "athlete"})],
    "virginiasports.com": [("div", {"id": "players"}), ("div", {"itemprop": "athlete"})],
    "miamihurricanes.com": [("div", {"id": "players"}), ("div", {"itemprop": "athlete"})],
    "golobos.com": [("div", {"id": "players"}), ("div", {"itemprop": "athlete"})],
    "lsusports.net": [("div", {"id": "players"}), ("div", {"itemprop": "athlete"})],
    "ukathletics.com": [("div", {"class": "roster__flex-wrapper"}), ("div", {"itemprop": "athlete"})],
    "gamecocksonline.com": [("div", {"class": "container roster__wrapper"}), ("li", {"itemprop": "athlete"})]

}


# Returns true if the url is absolute (begins with example.com) or not, used for joining netlocs with images that do not have absolute urls
def is_absolute(team_url):
    return bool(urlparse(team_url).netloc)


# Converts html element to stripped text
def html_to_text(elem):
    if elem:
        elem = elem.text.strip()
        return ' '.join(elem.split())
    else:
        return ''

# Converts team roster data for non-dynamically generated Sidearm and WMT websites into a Pandas DataFrame


def convert_url_to_df(url):
    #Initialize empty data object
    data = {'First Name': [],
            'Last Name': [],
            'Dummy Email': [],
            'Image URL': [],
            'Hometown': [],
            'Class': [],
            'High School': [],
            'Previous School': [],
            'Position': [],
            'Jersey Number': [],
            'Height': [],
            'Weight': []
            }

    #Checks HTTP status code of user inputted URL, exits program if status code is not successful (200-299)
    r = requests.get(url, headers={
                     "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"})
    if (r.status_code // 100 != 2):
        sg.popup_error(str(r.status_code) + " HTTP error: Please try a different URL", title="")
        return 
    #Parses url text into soup
    soup = BeautifulSoup(r.text, "html.parser")

    #For these two WMT websites, we have to find the image separately on each athlete's bio since images do not appear on the main roster
    if (urlparse(url).netloc == "arkansasrazorbacks.com") or (urlparse(url).netloc == "vucommodores.com"):

        roster = soup.find(team_hashmap[urlparse(url).netloc][0])
        athletes = roster.find_all(team_hashmap[urlparse(url).netloc][1])

        if not athletes:
            sg.popup_error("Please double check your URL", title="")
            return
            
        for athlete in athletes:
            info = athlete.find("a", href=True)
            if info is not None:
                name = html_to_text(info)

                first_name = name.split(" ", 1)[0]
                data["First Name"].append(first_name)

                last_name = name.split(" ", 1)[1]
                data["Last Name"].append(last_name)

                dummy_email = str(first_name.replace(" ", "") + "+" +
                                  last_name.replace(" ", "") + "@example.com")
                data['Dummy Email'].append(dummy_email)

                athlete_url = info['href']
                if not is_absolute(athlete_url):
                    athlete_url = "https://" + \
                        urlparse(url).netloc + athlete_url

                r = requests.get(athlete_url, headers={
                                 "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"})

                soup = BeautifulSoup(r.text, "html.parser")
                person = soup.find('section', {'class': re.compile(r'bio')})
                image_url = person.find('img')['src']

                #Removes dimmension parameters from image url
                image_url = re.sub('-\d+[Xx]\d+', '', image_url)

                if not is_absolute(image_url):
                    image_url = "https://www." + \
                        urlparse(url).netloc + image_url

                data['Image URL'].append(image_url)

            else:
                data["First Name"].append("")
                data["Last Name"].append("")
                data["Dummy Email"].append("")
                data["Image URL"].append("")

            data['Hometown'].append("")
            data['Class'].append("")
            data['High School'].append("")
            data['Previous School'].append("")
            data['Position'].append("")
            data['Jersey Number'].append("")
            data['Height'].append("")
            data['Weight'].append("")
            

    # All of other WMT websites in the hashmap, which do have the athlete images on the main roster
    elif (urlparse(url).netloc in team_hashmap):

        roster = soup.find(*team_hashmap[urlparse(url).netloc][0])
        athletes = roster.find_all(*team_hashmap[urlparse(url).netloc][1])

        if not athletes:
            sg.popup_error("Please double check your URL", title="")
            return

        for athlete in athletes:
            if (urlparse(url).netloc == "lsusports.net") or (urlparse(url).netloc == "ukathletics.com") or (urlparse(url).netloc == "gamecocksonline.com"):
                name = athlete.find("span", {"itemprop": "name"})["content"]
                image_url = athlete.find(
                    "span", {"itemprop": "image"})["content"]
                # These two websites have the images loaded in a strange format with two https:// links
                # applying urlparse(image_url).path[1:] fixes it
                if (urlparse(url).netloc == "ukathletics.com") or (urlparse(url).netloc == "gamecocksonline.com"):
                    image_url = urlparse(image_url).path[1:]

            else:
                name = athlete.find("img")['alt']
                name = " ".join(name.split())
                image_url = athlete.find("img")['src']
                if not is_absolute(image_url):
                    image_url = urlparse(url).netloc + image_url
                
            first_name = name.split(" ", 1)[0]
            data["First Name"].append(first_name)

            last_name = name.split(" ", 1)[1]
            data["Last Name"].append(last_name)

            dummy_email = str(first_name.replace(" ", "") + "+" +
                              last_name.replace(" ", "") + "@example.com")
            data['Dummy Email'].append(dummy_email)

            image_url = re.sub('-\d+[Xx]\d+', '', image_url)
            data['Image URL'].append(image_url)

            data['Hometown'].append("")
            data['Class'].append("")
            data['High School'].append("")
            data['Previous School'].append("")
            data['Position'].append("")
            data['Jersey Number'].append("")
            data['Height'].append("")
            data['Weight'].append("")


    elif re.search("sidearm", r.text):
        teams = soup.find_all("ul", {"class": "sidearm-roster-players"})
        roster = []
        if teams:
            for team in teams:
                athletes = team.find_all(
                    "li", {"class": "sidearm-roster-player"})
                roster.extend(athletes)

            if not athletes:
                sg.popup_error("Please double check your URL", title="")
                return

            for athlete in roster:
                first_name = html_to_text(athlete.find("div", {"class", "sidearm-roster-player-first-name"}))
                last_name = html_to_text(athlete.find("div", {"class", "sidearm-roster-player-last-name"}))
                if not first_name or not last_name:
                    name = athlete.find("div", {"class", "sidearm-roster-player-name"})
                    name = html_to_text(name)
                    #Remove jersey numbers from name section
                    name = ''.join([char for char in name if not char.isdigit()]).strip()
                    first_name = name.split(" ")[0]
                    last_name = " ".join(name.split(" ")[1:])

                data["First Name"].append(first_name)
                data["Last Name"].append(last_name)

                dummy_email = str(first_name.replace(" ", "") + "+" +
                                  last_name.replace(" ", "") + "@example.com")
                data['Dummy Email'].append(dummy_email)

                image_src = athlete.find("img")
                if image_src:
                    try:
                        image_url = image_src['data-src']
                        image_url = image_url.split("?")[0]
                        if not is_absolute(image_url):
                            image_url = urlparse(url).netloc + image_url
                    except:
                        image_url = None
                else:
                    image_url = None
                data['Image URL'].append(image_url)

                hometown = athlete.find(
                    "span", {"class": "sidearm-roster-player-hometown"})
                hometown = html_to_text(hometown)
                data['Hometown'].append(hometown)

                year = athlete.find(
                    "span", {"class": "sidearm-roster-player-academic-year"})
                year = html_to_text(year)
                data['Class'].append(year)

                high_school = athlete.find(
                    "span", {"class": "sidearm-roster-player-highschool"})
                high_school = html_to_text(high_school)
                data['High School'].append(high_school)

                previous_school = athlete.find(
                    "span", {"class": "sidearm-roster-player-previous-school"})
                previous_school = html_to_text(previous_school)
                data['Previous School'].append(previous_school)

                position = athlete.find("div", {
                                        "class": "sidearm-roster-player-position"}).find("span", {"class": "text-bold"})
                position = html_to_text(position)
                data['Position'].append(position)

                jersey_number = athlete.find(
                    "span", {"class": "sidearm-roster-player-jersey-number"})
                jersey_number = html_to_text(jersey_number)
                data['Jersey Number'].append(jersey_number)

                height = athlete.find(
                    "span", {"class": "sidearm-roster-player-height"})
                height = html_to_text(height)
                data['Height'].append(height)

                weight = athlete.find(
                    "span", {"class": "sidearm-roster-player-weight"})
                weight = html_to_text(weight)
                data['Weight'].append(weight)
                
        else:
            sg.popup_error("Unable to process data from dynamically generated Sidearm URL", title="")
            return
    
    else:
       sg.popup_error("Unable to process data from this roster URL", title="")
       return

    df = pd.DataFrame(data)
    return df

def generate_file_name(url):
    if url:
        team_website_netloc = urlparse(url).netloc
        split = url.split("/")
        if any(char.isdigit() for char in split[-1]):
            if "season" == split[-2]:
                return team_website_netloc[:-4] + "-" + split[-4] + "-" + split[-3] + "-" + split[-1]
            else:
                return team_website_netloc[:-4] + "-" + split[-3] + "-" + split[-2] + "-" + split[-1]
        else:
            return team_website_netloc[:-4] + "-" + split[-2] + "-" + split[-1]

def save_file(team_url, os_path, csv_file_name):
    team_url = team_url
    df = convert_url_to_df(team_url)
    if df is not None:
        if len(df.index) > 0:
            filename = csv_file_name
            if not filename:
                filename = generate_file_name(team_url)
            outputfile = Path(os_path) / f"{filename}.csv"
            df.to_csv(outputfile)
            sg.popup("File Saved", title="")

def display_csv_file(team_url, csv_file_name):
    df = convert_url_to_df(team_url)
    if df is not None:
        if len(df.index) > 0:
            filename = csv_file_name
            if not filename:
                filename = generate_file_name(team_url)
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', 4)
            sg.popup_scrolled(df, font=("Courier", 14), title=filename)

def is_valid_url(team_url):
    if validators.url(team_url):
        split = team_url.split("/")
        if any(char.isdigit() for char in split[-1]):
            if "season" == split[-2]:
                if "roster" == split[-3]:
                    return True
            else:
                if "roster" == split[-2]:
                    return True
        else:
            if "roster" == split[-1]:
                return True
    sg.popup_error("Please enter a valid team roster URL", title="")
    return False

def is_valid_path(filepath):
    if filepath and Path(filepath).exists():
        return True
    sg.popup_error("Please enter a valid file path", title="")
    return False

def clean_url(url):
    return url.strip(" /").replace(" ", "").lower()

    
#-------- GUI Definition ---------- #
def main_window():
    theme = "Dark"
    font_family = "Arial"
    font_size = 14
    sg.theme(theme)
    sg.set_options(font=(font_family, font_size))

    text_column = [[sg.T("Enter a team roster URL:")],
                   [sg.T("Name of CSV file (optional):")],
                   [sg.T("Choose a path to save CSV: ")]]
    input_column = [[sg.I(key="-TEAM_URL-", change_submits=True)],
                    [sg.I(key="-CSV_FILE_NAME-", change_submits=True)],
                    [sg.I(key="-OS_PATH-", change_submits=True), sg.FolderBrowse()]]
    layout = [
            [sg.Column(text_column), sg.Column(input_column)],
            [sg.B("Preview File"), sg.B("Save"), sg.B("Exit", button_color="tomato")]
    ]
    window_title = "Team Roster URL To CSV Converter"
    window = sg.Window(window_title, layout, alpha_channel=0.9)

    while True:
        event, values = window.read(timeout=10)
        if event in (sg.WINDOW_CLOSED, "Exit"):
            break
        if event == "Preview File":
            if is_valid_url(clean_url(values["-TEAM_URL-"])):
                display_csv_file(team_url=clean_url(values["-TEAM_URL-"]), csv_file_name=values["-CSV_FILE_NAME-"])
        if event == "Save":
            if is_valid_path(values["-OS_PATH-"]) and is_valid_url(clean_url(values["-TEAM_URL-"])):
                save_file(team_url=clean_url(values["-TEAM_URL-"]), os_path=values["-OS_PATH-"], csv_file_name=values["-CSV_FILE_NAME-"])
    window.close()

if __name__ == "__main__":
    print("Running main")
    main_window()