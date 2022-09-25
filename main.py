import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urlparse
import sys

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

# Prints progress bar (retrieved from https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters)
def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()

# Returns true if the url is absolute (begins with example.com) or not, used for joining netlocs with images that do not have absolute urls
def is_absolute(url):
    return bool(urlparse(url).netloc)


# Converts html element to stripped text
def html_to_text(elem):
    if elem:
        elem = elem.text.strip()
        return ' '.join(elem.split())
    else:
        return ''

# Converts team roster data for non-dynamically generated Sidearm and WMT websites into a Pandas DataFrame
def get_team_data(url):
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
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"})
    if (r.status_code // 100 != 2):
        print(r.status_code, "HTTP error")
        quit()

    #Parses url text into soup
    soup = BeautifulSoup(r.text, "html.parser")

    #For these two WMT websites, we have to find the image separately on each athlete's bio since images do not appear on the main roster
    if (urlparse(url).netloc == "arkansasrazorbacks.com") or (urlparse(url).netloc == "vucommodores.com"):
        
        roster = soup.find(team_hashmap[urlparse(url).netloc][0])
        athletes = roster.find_all(team_hashmap[urlparse(url).netloc][1])

        for i, athlete in enumerate(athletes):
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
                    athlete_url = "https://" + urlparse(url).netloc + athlete_url
                
                r = requests.get(athlete_url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"})
                
                soup = BeautifulSoup(r.text, "html.parser")
                person = soup.find('section', {'class': re.compile(r'bio')})
                image_url = person.find('img')['src']

                #Removes dimmension parameters from image url
                image_url = re.sub('-\d+[Xx]\d+', '', image_url)

                if not is_absolute(image_url):
                    image_url = "https://www." + urlparse(url).netloc + image_url 

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
            printProgressBar(i+1, len(athletes), prefix='Progress:', suffix='Complete', length=50)

    # All of other WMT websites in the hashmap, which do have the athlete images on the main roster
    elif (urlparse(url).netloc in team_hashmap):

        roster = soup.find(*team_hashmap[urlparse(url).netloc][0])
        athletes = roster.find_all(*team_hashmap[urlparse(url).netloc][1])

        for i, athlete in enumerate(athletes):

            if (urlparse(url).netloc == "lsusports.net") or (urlparse(url).netloc == "ukathletics.com") or (urlparse(url).netloc == "gamecocksonline.com"):
                name = athlete.find("span", {"itemprop": "name"})["content"]
                image_url = athlete.find(
                    "span", {"itemprop": "image"})["content"]
                # These two websites have the images loaded in a strange format with two https:// links
                # applying urlparse(image_url).path[1:] fixes it
                if (urlparse(url).netloc == "ukathletics.com") or (urlparse(url).netloc == "gamecocksonline.com"):
                    image_url = urlparse(image_url).path[1:]
            
            else:
                name = athlete.find("img")['title']
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
            printProgressBar(i+1, len(athletes), prefix='Progress:', suffix='Complete', length=50)

    elif re.search("sidearm", r.text):
        teams = soup.find_all("ul", {"class": "sidearm-roster-players"})
        roster = []
        if teams:
            for team in teams:
                athletes = team.find_all(
                    "li", {"class": "sidearm-roster-player"})
                roster.extend(athletes)
            for i, athlete in enumerate(roster):
                name = athlete.find(
                    "div", {"class", "sidearm-roster-player-name"})
                name = html_to_text(name)

                first_name = name.split(" ", 1)[0]
                data["First Name"].append(first_name)

                last_name = name.split(" ", 1)[1]
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
                printProgressBar(i+1, len(roster), prefix='Progress:', suffix='Complete', length=50)

        else:
            print("Error: unable to find data from dynamically generated roster")
            quit()
    else:
        print("Error: invalid website")
        quit()

    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    url = str(sys.argv[1])
    url = url.replace("www.", "")
    df = get_team_data(url)
    path = os.path.join(os.getcwd(), "data")

    #Make new data directory if it does not already exist
    if os.path.exists(path) == False:
        os.mkdir(path)

    team_website_netloc = urlparse(url).netloc
    #Removes .com, .net, or .edu from netloc
    team_website_folder = team_website_netloc[:-4]
    team_dir_path = os.path.join(path, team_website_folder)

    #Make new team directory as child to data if it does not already exist
    if os.path.exists(team_dir_path) == False:
        os.mkdir(team_dir_path)

    #Creates csv file name
    if (url[-1] == "/"):
        csv_file_path = os.path.join(team_dir_path, url.split(
            "/")[-3] + "-" + url.split("/")[-2] + ".csv")
    else:
        csv_file_path = os.path.join(team_dir_path, url.split(
            "/")[-2] + "-" + url.split("/")[-1] + ".csv")

    #Load data to appropriate csv file path
    df.to_csv(csv_file_path)
