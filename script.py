#!/usr/bin/env python3

# ****** # # # # # # # # # # # # # # # # # # # # # # # # # ****** #
# ******                                                   ****** #
# ******   Name: Siddhant Shah                             ****** #
# ******   Date: 24/03/2020                                ****** #
# ******   Desc: Followers of Instagram Account            ****** #
# ******   Email: siddhant.shah.1986@gmail.com             ****** #
# ******                                                   ****** #
# ****** # # # # # # # # # # # # # # # # # # # # # # # # # ****** #


# ! PROJECT REQUIREMENTS 
# ## Script to fetch followers account for a given Instagram account


# >> IMPORTANT IMPORT
from InstagramAPI import InstagramAPI
from oauth2client.service_account import ServiceAccountCredentials
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from termcolor import cprint
from datetime import datetime
import pandas as pd
from colorama import init
from random import choice, randint
import json, requests, os, pyfiglet, time
import gspread, sys, emoji, smtplib, urllib


# >> GLOBAL VARIABLES
LOGGED_INSTA_ACCOUNTS = []         # Main list of all logged insta accounts
INSTA_CREDS = {}
FOLDER_NAME = None
MASTER_ACCOUNT = None
SERVER_HIT_COUNT = 0
CONFIG = {}
FOLLOWERS = {}
GOOGLE_SHEET = None


# >> just for decoration
def intro():
    print()
    print(pyfiglet.figlet_format(" GeekySid"))
    print()
    print('  # # # # # # # # # # # # # # #  # # # # # # # #')
    print('  #                                            #')
    print('  #  SCRAPER FOR INSTAGRAM FOLLOWERS FETCHER   #')
    print('  #             By: SIDDHANT SHAH              #')
    print('  #               Dt: 24/03/2020               #')
    print('  #        siddhant.shah.1986@gmail.com        #')
    print('  #      **Just for Educational Purpose**      #')
    print('  #                                            #')
    print('  # # # # # # # # # # # # #  # # # # # # # # # #')
    print()


# >> reading config data
def read_config():
    global CONFIG
    if os.path.exists('config.json'):
        with open('config.json', 'r') as r:
            CONFIG = json.load(r)
        return True


# >> reading mailing secret file
def read_mailing_file():
    # reding mailing information
    if os.path.exists(f'mailing_secret.json'):
        with open (f'mailing_secret.json', 'r') as r:
            CONFIG['MAILER'] = json.load(r)
            return True


# >> returns randome sleep time
def get_random_sleep(sleep_time):
    if len(sleep_time) > 1:
        return randint(sleep_time[0], sleep_time[1])/10
    else:
        return sleep_time[0]


# ______ XXXXXXXXXXXXXXXXXXXXXX ______
# ______   INSTAGRAM ACCOUNTS   ______
# ______ XXXXXXXXXXXXXXXXXXXXXX ______


# >> CLASS FOR GOOGLE SHEET
class GoogleSheet_Creds(object):
    
    # >> initializing the google sheet with a secret file and a proper sheet number
    def __init__(self, sheet_number):
        global CONFIG
        scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file",
                "https://www.googleapis.com/auth/drive"
            ]

        while True:
            if not os.path.exists(CONFIG['google_sheet_access_creds']):
                cprint(f'  [!] Secret file is not found... Please enter a full path to secret file.', 'red', attrs=['bold'])
                CONFIG['google_sheet_access_creds'] = input().strip()
            else:
                break
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(CONFIG['google_sheet_access_creds'], scope)
        client = gspread.authorize(creds)
        self.sheet = client.open('instagram_users_cred').get_worksheet(sheet_number)
        self.status_column = 4


    # >> getting all credentials in the given sheet
    def get_insta_cred(self):
        creds = self.sheet.get_all_records() 
        filtered_creds = {}

        for cred in creds:
            if cred['status'].lower() == 'active':
                filtered_creds[cred['username']] = {
                    'password': cred['password'],
                    'status': cred['status'],
                    'row_count': cred['row_count']
                }

        if len(filtered_creds.keys()) > 0:
            return filtered_creds
        else:
            return None 


    # >> updating sheet's cell at a given row and column 
    def update_spreadsheet(self, row, column, text):
        self.sheet.update_cell(row, column, text)


    # >> updating status of the cred in google sheet
    def update_cred_status(self, row, text):
        self.sheet.update_cell(row, self.status_column, text)


# >> class or each dummy insta accounts
class InstaDummyAccount(object):
    def __init__(self, username, password, proxy=None):
        '''
            Instance Variables
            self.username ==>   username of the insta account class represents
            self.password   ==> password of the insta account class represents
            self.account    ==> holds class instance of the insta account
        '''
        self.username = username
        self.password = password
        self.proxy = proxy
        self.account = None


    # >> log into instagram
    def login(self):
        '''
            Function that login instagram account isntance and set instance variables depending on the outcome of function
        '''

        if self.account == None:
            if self.username is not None and self.password is not None:
                try:
                    self.account = InstagramAPI(self.username, str(self.password))
                    return self.account.login()
                except Exception as e:
                    cprint(f"    [!] Error occured while trying to log into Instagram for user {self.username}", "red")
                    cprint(f"    [!] Exception => {str(e)}\n", "red")
            else:
                cprint(f"    [!] Either Username or Password is not provided\n", "red")
        else:
            cprint(f"   [+] Dummy Account, {self.username} is already loggedin\n", "yellow")
        return None


    def __str__(self):
        return f"{self.account.username}"


# >> logging individual accounts into instagram
def login_insta_indv(username, password, row_count):
    global LOGGED_INSTA_ACCOUNTS

    insta_account = InstaDummyAccount(username, password)

    if insta_account.login():
        # if insta_account.account.isLoggedIn:
        LOGGED_INSTA_ACCOUNTS.append(insta_account)
        cprint(f"    [{len(LOGGED_INSTA_ACCOUNTS)}] Logged into instagram with user, {username}\n", "green")
        return True
    else:
        print(insta_account.account.isLoggedIn)
        GOOGLE_SHEET.update_cred_status(row_count, 'problem')
        cprint(f"    [X] Unable to Login into instagram for user {username}. Maybe credentials are wrong or account is blocked.\n", "red")


# >> function that logs all dummy account into insta
def login_all_accounts(sleep_time):
    global LOGGED_INSTA_ACCOUNTS
    LOGGED_INSTA_ACCOUNTS = []

    counter = 0

    for username in INSTA_CREDS.keys():
        if login_insta_indv(username, INSTA_CREDS[username]['password'], INSTA_CREDS[username]['row_count']):
            if CONFIG['max_dummy_account'] > 0 and counter == CONFIG['max_dummy_account']:
                break
            counter += 1

        time.sleep(get_random_sleep(sleep_time))

    cprint(f"\n  [+] Total {len(LOGGED_INSTA_ACCOUNTS)} dummy accounts in use\n", "green", attrs=["bold"])

    # notifying myself if logged account is less then minimum number of required logged account
    if len(LOGGED_INSTA_ACCOUNTS) == 0:
        if 'MAILER' in CONFIG.keys():
            CONFIG['max_server_hit_count'] = 100
            subject = emoji.emojize(":thumbs_down:") + " JOSH FOLLOWERS Script  Terminated"
            body = f'Hello, <p />Unable to log into any instagram account. Please check.<p /><p /> {CONFIG["MAILER"]["EMAIL_SIGNATURE"]}'
            # print(subject)
            send_mail(subject, body)
            print('\n\n')
            cprint(f'  [XX] EXITING SCRIPT AS UNABLE TO LOG INTO ANY INSTAGRAM ACCOUNT.... ', 'red', 'on_white', attrs=['bold'])
            print('\n\n')
            exit()
    elif len(LOGGED_INSTA_ACCOUNTS) < CONFIG['minimum_dummy_accounts']:

        if 'MAILER' in CONFIG.keys():
            CONFIG['max_server_hit_count'] = 100
            subject = emoji.emojize(":thumbs_down:") + " JOSH FOLLOWERS Script - Need More  Insta Account"
            body = f'Hello, <p />There are only {len(LOGGED_INSTA_ACCOUNTS)} logged account where required number of logged account is {CONFIG["minimum_dummy_accounts"]}. Please check.<p /><p /> {CONFIG["MAILER"]["EMAIL_SIGNATURE"]}'
            # print(subject)
            send_mail(subject, body)
    else:
        if os.path.exists('config.json'):
            with open('config.json', 'r') as r:
                data = json.load(r)
                CONFIG['max_server_hit_count'] = data['max_server_hit_count']


# >> function that logs out all dummy account from insta
def logout_all_accounts(sleep_time):
    global LOGGED_INSTA_ACCOUNTS
    cprint(f'\n  [+] Starting to Log out of all Instagram Accounts\n', 'blue')

    for _ in LOGGED_INSTA_ACCOUNTS:
        time.sleep(get_random_sleep(sleep_time))
    
    LOGGED_INSTA_ACCOUNTS = []


# >> checking for new creds in google sheet
def check_for_new_creds():
    global INSTA_CREDS
    cprint(f'\n  [+] Checking for New Instagram Credentials', 'yellow', attrs=['bold'])
    
    new_creds = GOOGLE_SHEET.get_insta_cred()
    # existing_uname = INSTA_CREDS.keys()
    # new_cred_count = 0

    for new_uname in new_creds.keys():
        # # print(json.dumps(new_creds[new_uname], indent=4))

        # if new_uname in existing_uname:
        #     if not new_creds[new_uname]['status'].lower() == 'active':
        #         INSTA_CREDS.pop(new_uname)
        # else:
        #     if login_insta_indv(new_uname, new_creds[new_uname]['password'], new_creds[new_uname]['row_count']):
                INSTA_CREDS[new_uname] = {
                    'password': new_creds[new_uname]['password'],
                    'row_count': new_creds[new_uname]['row_count']
                }
                # new_cred_count += 1
                # time.sleep(3)
    
    # cprint(f'      [>] New Creds Added: {new_cred_count}', 'green', attrs=['bold'])
    cprint(f'      [>] Total Logged Accounts: {len(LOGGED_INSTA_ACCOUNTS)} new creds added to script\n', 'green', attrs=['bold'])


# >> return logged user one by ones
def get_current_logged_user():
    global SERVER_HIT_COUNT

    while True:
        # checking if mserver has hit max time
        if SERVER_HIT_COUNT > CONFIG['max_server_hit_count']:
            cprint(f'\n\n    [+] Server Hit has reached max count ({CONFIG["max_server_hit_count"]}) or We need more Accounts. Filtering any Blocked Account', 'magenta', attrs=['bold'])

            # ckecking for new creds from spreadsheet
            check_for_new_creds()

            # logging out of all accounts
            login_all_accounts([20, 35])

            # resetting server hit count
            SERVER_HIT_COUNT = 0

        index = ((SERVER_HIT_COUNT+1) % len(LOGGED_INSTA_ACCOUNTS))-1
        cur_account = LOGGED_INSTA_ACCOUNTS[index]
        SERVER_HIT_COUNT += 1

        # checking if account is logged in
        if cur_account.account.isLoggedIn:
            return cur_account

        else:
            LOGGED_INSTA_ACCOUNTS.remove(cur_account)


# ______ XXXXXXXXXXXXXXXXXXXXXXXXXXXXX ______
# ______   FETCHING USER'S FOLLOWERS   ______
# ______ XXXXXXXXXXXXXXXXXXXXXXXXXXXXX ______


# >> saving max_id to the txt file
def save_next_max_id(max_id):
    max_id_file = f'{FOLDER_NAME}/next_max_id.txt'

    if not os.path.isdir(FOLDER_NAME):
        os.mkdir(FOLDER_NAME)

    with open(max_id_file, 'w') as f:
        f.write(max_id)


# >> returns max id
def get_max_id():
    max_id_file = f'{FOLDER_NAME}/next_max_id.txt'
    if os.path.exists(max_id_file):
        with open(max_id_file, "r") as r:
            max_id = r.read()
            return max_id.strip() 
    else:
        return ''


# >> returns previously fetched posts stored in json file
def get_fetched_followers_from_json():
    post_file = f'{FOLDER_NAME}/followers_data.json'
    if os.path.exists(post_file):
        with open(post_file, 'r') as r:
            return json.load(r)
    else:
        return {}


# >> STORING POSTS DATA IN JSON FILE
def save_follower_data_to_json():
    post_file = f'{FOLDER_NAME}/followers_data.json'
    with open(post_file, 'w') as file:
        json.dump(FOLLOWERS, file)


# >> function to apply try catch while pulling specific datapoints from fetched posts
def try_except(post_dict, field):
    try:
        return post_dict.get(field, '')
    except:
        return None


# >> FUNCTION TO FETCH FOLLOWERS FRO A GIVEN ACCOUNT
def fetch_followers(user_id, sleep_time, save_after):
    global SERVER_HIT_COUNT
    global FOLLOWERS

    has_more_followers = True
    page_count = 0
    followers_count = 0

    max_id = get_max_id()
    FOLLOWERS = get_fetched_followers_from_json()

    while has_more_followers:
        current_logged_user = get_current_logged_user()
        page_count = page_count + 1
        page_follower_count = 0

        cprint(f"\n      [>] Fetching Followers from page # {page_count} for account {MASTER_ACCOUNT} with account {current_logged_user}", "cyan")

        current_logged_user.account.getUserFollowers(user_id, maxid=max_id)
        SERVER_HIT_COUNT += 1
        result = current_logged_user.account.LastJson

        with open('follower_json.json', 'w') as w:
            json.dump(result, w)
        # print(json.dumps(result, indent=4))
        # input()

        if 'users' in result.keys():
            for follower in result['users']:    # looping through all the fetched posts
                try:
                    if not follower["pk"] in list(FOLLOWERS.keys()):
                        FOLLOWERS[follower["pk"]] = {
                            "username": follower["username"],
                            "is_private": follower["is_private"],
                            "fetched": False
                        }
                        page_follower_count += 1        # increasing with every post fetched
                        followers_count += 1

                except Exception as e:
                    cprint(f'***EXPECTION: {str(e)}', 'red', attrs=['bold'])

            # storing post and user data to the csvss
            cprint(f'          [>>] Fetched {page_follower_count} Followers for this page. Total Followers fetched so far: {len(FOLLOWERS.keys())}', 'yellow')

            save_follower_data_to_json()

            if ('next_max_id' in result.keys()):
                max_id = result.get('next_max_id', '')
                save_next_max_id(max_id)
                if has_more_followers:
                    has_more_followers = True
                time.sleep(get_random_sleep(sleep_time))
            else:
                cprint(f'\n          [>>] Seems like we have fetched all Followers ({len(FOLLOWERS.keys())})', 'green')
                break
            if CONFIG['max_followers_count'] > 0 and len(FOLLOWERS.keys()) > CONFIG['max_followers_count']:
                cprint(f'          [>>] Seems like we have fetched required number of Followers ({len(FOLLOWERS.keys())})', 'green')
                break
        else:
            cprint('        [✖] There seems to be no data fetched. Please try again with proper Account', 'yellow')
            break

        time.sleep(get_random_sleep(sleep_time))

    save_follower_data_to_json()


# >> function that returns userid of the insta account that clients needs to scrape
def get_userid(user):
    current_logged_user = get_current_logged_user()

    # serach details abot the user
    current_logged_user.account.searchUsername(user)
    search_user = current_logged_user.account.LastJson

    if "message" in search_user.keys():     # if usernameis not found
        print(search_user["message"])
        return (None, None)
    else:
        userid = search_user["user"]["pk"]
        is_private = search_user["user"]["is_private"]

        cprint(f"\n      [>] {user.upper()} accounts Detail: ", "yellow")
        cprint(f"          [>>] Fullname          -> {search_user['user']['full_name']}", "magenta")
        cprint(f"          [>>] Userid            -> {userid}", "magenta")
        cprint(f"          [>>] Media Count       -> {search_user['user']['media_count']}", "magenta")
        cprint(f"          [>>] Followers  Count  -> {search_user['user']['follower_count']}", "magenta")
        cprint(f"          [>>] Followings Count  -> {search_user['user']['following_count']}", "magenta")
        cprint(f"          [>>] Biography         -> {search_user['user']['biography']}", "magenta")
        cprint(f"          [>>] Private Account   -> {search_user['user']['is_private']}", "magenta")
        cprint(f"          [>>] Verified Account  -> {search_user['user']['is_verified']}", "magenta")
        cprint(f"          [>>] Any URL           -> {search_user['user']['external_url']}", "magenta")
        print()

        return (userid, is_private)


# ______ XXXXXXXXXXXXXXXXXXXXXXXXXXX ______
# ______   FETCHING FOLLOWERS DATA   ______
# ______ XXXXXXXXXXXXXXXXXXXXXXXXXXX ______


# >> FUNCTION TO FETCH USER DATA FROM INSTAGRAM FRO A GIVEN ACCOUNT
def fetch_indv_follower_data(sleep_time):
    global FOLLOWERS
    global SERVER_HIT_COUNT

    FOLLOWERS = get_fetched_followers_from_json()
    user_count = 0

    for user in list(FOLLOWERS.keys()):
        user_count += 1

        if FOLLOWERS[user]['fetched']:
            cprint(f'\n      [{user_count}] Fetching Data for user: {FOLLOWERS[user]["username"]}', 'cyan')
            cprint(f'          [>>] Already Fetched', 'yellow')

        elif FOLLOWERS[user]['is_private']:
            cprint(f'\n      [{user_count}] Fetching Data for user: {FOLLOWERS[user]["username"]}', 'cyan')
            save_follower_data_to_json()
            FOLLOWERS[user]['fetched'] = True
            cprint(f'          [>>] User is Private', 'magenta')
        
            # time.sleep(get_random_sleep(sleep_time))

        else:
            try:
                current_logged_user = get_current_logged_user()
                cprint(f'\n      [{user_count}] Fetching Data for user: {FOLLOWERS[user]["username"]} ({current_logged_user})', 'cyan')
                current_logged_user.account.getUsernameInfo(user)
                SERVER_HIT_COUNT += 1
                result = current_logged_user.account.LastJson

                with open('user_json.json', 'w') as w:
                    json.dump(result, w)
                # print(json.dumps(result, indent=4))
                # input()

                try:
                    field = 'full_name'
                    FOLLOWERS[user][field] = result['user'].get('full_name', '')
                except:
                    FOLLOWERS[user][field] = None
                try:
                    field = 'biography'
                    FOLLOWERS[user][field] = result['user'].get('biography', '').replace("\n", " ")
                except:
                    FOLLOWERS[user][field] = None
                try:
                    field = 'media_count'
                    FOLLOWERS[user][field] = result['user'].get('media_count', 0)
                except:
                    FOLLOWERS[user][field] = None
                try:
                    field = 'follower_count'
                    FOLLOWERS[user][field] = result['user'].get('follower_count', 0)
                except:
                    FOLLOWERS[user][field] = None
                try:
                    field = 'following_count'
                    FOLLOWERS[user][field] = result['user'].get('following_count', 0)
                except:
                    FOLLOWERS[user][field] = None
                try:
                    field = 'is_private'
                    FOLLOWERS[user][field] = result['user'].get('is_private', True)
                except:
                    FOLLOWERS[user][field] = None
                try:
                    field = 'is_verified'
                    FOLLOWERS[user][field] = result['user'].get('is_verified', False)
                except:
                    FOLLOWERS[user][field] = None

                FOLLOWERS[user]['fetched'] = True

                save_follower_data_to_json()
                cprint(f'          [>>] Fetched', 'yellow')

            except Exception as e:
                cprint(f'\n          [X] Exception: {str(e)}\n', 'red', attrs=['bold'])
        
            time.sleep(get_random_sleep(sleep_time))

    cprint(f'      [>] Fetched data for a total of {user_count} users.', 'green')


# ______ XXXXXXXXXXXXXXXXXXXXXXX ______
# ______      MAIN FUNCTION      ______
# ______ XXXXXXXXXXXXXXXXXXXXXXX ______


# >> function that converts JSON to CSV
def convert_json_to_csv():
    global FOLLOWERS

    FOLLOWERS = get_fetched_followers_from_json()
    followers_list = []
    for user in FOLLOWERS:
        followers_list.append(FOLLOWERS[user])
    
    csv_file = f'{FOLDER_NAME}/{MASTER_ACCOUNT}.csv'
    # pd.DataFrame(followers_list).to_csv(csv_file, index=False)
    pd.DataFrame(followers_list).to_csv(csv_file, index=False, columns=[''])

    cprint(f'\n      [>] Done\n', 'green')


# >> displays total time taken for entire script to run
def time_calculator(start_time):
    end_time = time.time()

    time_diff = (end_time-start_time)
    hrs = int((time_diff)//3600)
    mins = int(((time_diff)%3600)//60)
    secs = int(((time_diff)%3600)%60)
    time_string = f'  [🕐] Total Time taken: {hrs}hrs {mins}mins {secs}secs  '
    time.sleep(5)

    print('\n')
    cprint("="*len(time_string), 'grey', 'on_white', attrs=['bold'])
    cprint(time_string, 'grey', 'on_white', attrs=['bold'])
    cprint("="*len(time_string), 'grey', 'on_white', attrs=['bold'])
    print('\n')


# >> function that connects to smtp and send mail
def send_mail(subject, body):

    # information fetcheed from settings.py to connect to smtp
    smtp_user = CONFIG['MAILER']['EMAIL_USER']
    smtp_pass = CONFIG['MAILER']['EMAIL_PASS']
    smtp_address = CONFIG['MAILER']['EMAIL_HOST']
    smtp_port = CONFIG['MAILER']['EMAIL_PORT']
    
    with smtplib.SMTP_SSL(smtp_address, smtp_port) as smtp:
        smtp.login(smtp_user, smtp_pass)
        try:
            for mail_to in CONFIG['mail_to']:
                #  message setting for self mail
                msg = MIMEMultipart()
                msg['To'] = 'mail_to'
                msg['Subject'] = subject
                msg['From'] = smtp_user

                msg.attach(MIMEText(body, 'html'))

                smtp.sendmail(smtp_user, mail_to, msg.as_string())
        except Exception as e:
            print("Exception: ", str(e))


# >> main function
def main():
    global FOLDER_NAME
    global MASTER_ACCOUNT
    global INSTA_CREDS
    global GOOGLE_SHEET


    # ! GETTING DUMMY INSTA CREDS 
    GOOGLE_SHEET = GoogleSheet_Creds(CONFIG['google_sheet_number'])
    INSTA_CREDS = GOOGLE_SHEET.get_insta_cred()


    # ! LOGGING INTO DUMMY INSTA LOGGED ACCOUNT 
    if CONFIG['login']:
        sleep_time = [20, 35]
        print('\n')
        cprint(f'  [+] Starting to Log into Instagram using Dummy Accounts', 'blue', 'on_white', attrs=['bold'])
        print()
        login_all_accounts(sleep_time)


    # ! PULLING FOLLOWERS FOR GIVEN USERS 
    if CONFIG['fetch_followers_id']:
        for master_account in CONFIG['master_account']:
            MASTER_ACCOUNT = master_account
            print('\n')
            cprint(f'  [+] FETCHING FOLLOWERS FOR ACCOUNT => {MASTER_ACCOUNT.upper()}  ', 'blue', 'on_white', attrs=['bold'])

            if not os.path.isdir(f'{os.getcwd()}/Data/'):
                os.mkdir(f'{os.getcwd()}/Data/')

            if not os.path.isdir(f'{os.getcwd()}/Data/{MASTER_ACCOUNT}'):
                os.mkdir(f'{os.getcwd()}/Data/{MASTER_ACCOUNT}')

            FOLDER_NAME = f'{os.getcwd()}/Data/{MASTER_ACCOUNT}'

            user_id, is_private = get_userid(MASTER_ACCOUNT)
            if user_id:
                if is_private:
                    cprint(f'      [>>] The account is private and hence we can\'t fetch Followers fro the same.', 'red', attrs=['bold'])
                else:
                    sleep_time = [35,50]
                    save_after = 100
                    fetch_followers(user_id, sleep_time, save_after)
            else:
                cprint(f'      [>>] Can\'t locate account with username {MASTER_ACCOUNT}', 'red', attrs=['bold'])


    # ! PULLING FOLLOWERS FOR GIVEN USERS 
    if CONFIG['fetch_followers_data']:
        for master_account in CONFIG['master_account']:
            MASTER_ACCOUNT = master_account
            print('\n')
            cprint(f'  [+] FETCHING FOLLOWERS DATA  ', 'blue', 'on_white', attrs=['bold'])
            FOLDER_NAME = f'{os.getcwd()}/Data/{MASTER_ACCOUNT}'
            sleep_time = [35,50]

            fetch_indv_follower_data(sleep_time)


    # ! CONVERT JSON TO CSV 
    if CONFIG['convert_json_to_csv']:
        for master_account in CONFIG['master_account']:
            MASTER_ACCOUNT = master_account
            print('\n')
            cprint(f'  [+] CREATING CSV FILE FOR user {MASTER_ACCOUNT} data from JSON ', 'blue', 'on_white', attrs=['bold'])
            FOLDER_NAME = f'{os.getcwd()}/Data/{MASTER_ACCOUNT}'
            convert_json_to_csv()

    
    cprint(f'\n  [🎉] SCRIPT HAS SUCCESSFULLY EXECUTED ', 'blue', 'on_white', attrs=['bold'])


# >> this is where script starts executing
if __name__ == '__main__':
    start_time = time.time()
    intro()
    if read_config():# and read_mail_config():
        mail = read_mailing_file()
        try:
            main()
            subject = emoji.emojize(":thumbs_up:") + " JOSH Followers Fetched"
            body = 'Hello, <p />The script has successfully Executed. <p /><p />' + CONFIG['MAILER']['EMAIL_SIGNATURE']

        except Exception as err:
            cprint(f'\n\n  [X] Exception: {str(err)}', 'red', attrs=['bold'])
            subject = emoji.emojize(":thumbs_down:") + " JOSH Failed Followers Fetched"
            body = 'Hello, <p />The script has thrown an error while executing with an error <br /><span style="color:red">'+str(err) + '.<p /><p />' + CONFIG['MAILER']['EMAIL_SIGNATURE']
    
        if mail:
            send_mail(subject, body)

    time_calculator(start_time)