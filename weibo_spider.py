

#----------------------------------------------------------------
import requests 
import pickle
import os
from bs4 import BeautifulSoup

from seleniumrequests import Chrome
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import re
import pandas as pd
from datetime import date
from datetime import timedelta
import time


os.chdir("/Users/richardc/Desktop/weibo_scrap/") #---------------------------------| change to path of main folder

#webdriver = Chrome('chromedriver') 


def driver_onboard(headless = False):
 
        option = Options()
        option.add_argument("--disable-infobars")
        option.add_argument("start-maximized")
        option.add_argument("--disable-extensions")

        
        if headless == True: 
            
            option.add_argument("--headless")
            option.add_argument("--window-size=1920x1080")
            
        # Pass the argument 1 to allow and 2 to block
        option.add_experimental_option("prefs", { 
            "profile.default_content_setting_values.notifications": 2 })
        
        PATH = '/Applications/chromedriver'
        driver = webdriver.Chrome(chrome_options=option, executable_path = PATH)


        return driver
    
def save_cookie(driver, slp_time):
        
        driver.get("http://www.weibo.com/")
        time.sleep(slp_time)
        pickle.dump(driver.get_cookies(), open("configuration/cookies/Login_Cookies.pkl", "wb")) 
        driver.quit()

def update_cookie(run=False, time=40): 
    if run == True:
        driver = driver_onboard(headless = False)
        save_cookie(driver, time)
  

def space_eliminator(string): 
    
    string_output = "".join(string.split()).replace("收起全文d", "") 
    return string_output


def extract_hashtags(a_list): 

         hashtag_longstr = str('')
         for hash in a_list: 
             hashtag_longstr = hashtag_longstr+"#"+ hash.replace("#","")
         return hashtag_longstr  

def null_or_num(test_list): 
            
        if test_list:
            return int(test_list[0])
        else:
            return 0 
def extract_feed(card):
        
        feed_info = {}
        primary_msg_pane = card.find("div", class_= "content")
        user_info = primary_msg_pane.find("a", class_ = "name")
        feed_info['prim_profile_link'] = user_info['href']
        feed_info['prim_nick_name']  = user_info['nick-name']
        
        texts  = primary_msg_pane.find_all('p', class_ = 'txt')  
        prim_text  = texts[0].text       #------------------------------------------｜
        feed_info['prim_text'] = space_eliminator(prim_text)
        feed_info['prim_hashtag_count'] = prim_text.count('#')/2
        prim_hashtag = re.findall('#\w+\#',prim_text) 
        feed_info['prim_hashtag'] = extract_hashtags(prim_hashtag)                          
        
        prim_details = primary_msg_pane.find_all("p", class_ = "from")[-1].text
        prim_details = space_eliminator(prim_details)
        feed_info['prim_datetime'] = prim_details.split('来自')[0]
        feed_info['prim_medium'] = prim_details.split('来自')[1]
        
        
        reaction_details  = card.find('div', class_ = "card-act").find_all('li')
        prim_forward  =  re.findall('[0-9]+', reaction_details[1].text)
        feed_info['prim_forward'] = null_or_num(prim_forward)
        prim_comment  = re.findall('[0-9]+', reaction_details[2].text)
        feed_info['prim_comment'] = null_or_num(prim_comment)
        prim_like = re.findall('[0-9]+', reaction_details[3].text)
        feed_info['prim_like']  =   null_or_num(prim_like)
        
        # forwarded message 
        
        
        forwarded_msg_pane = card.find("div", class_="con")
        
        if forwarded_msg_pane:
        
                user_info = forwarded_msg_pane.find("a", class_ = "name")
                feed_info['forward_profile_link'] = user_info['href']
                feed_info['forward_nick_name']  = user_info['nick-name']
                
                texts  = forwarded_msg_pane.find_all('p', class_ = 'txt')  
                forward_text  = texts[-1].text
                feed_info['forward_text'] = space_eliminator(forward_text)
                
                
                #forward_details = forwarded_msg_pane.find("div", class_ = "con")
                forward_details = forwarded_msg_pane.find("div", class_ = "func")
                forward_details = forward_details.find("p", class_ = "from")
                #forward_details = space_eliminator(forward_details)
                feed_info['forward_datetime'] = forward_details.text.split('来自')[0]
                feed_info['medium'] = forward_details.text.split('来自')[1]
                
                
                forward_details = forwarded_msg_pane.find("div", class_ = "func")
                reaction_details  = forward_details.find_all('li')
                forward_forward=  re.findall('[0-9]+', reaction_details[0].text)
                feed_info['forward_forward']  = null_or_num(forward_forward)
                forward_comment = re.findall('[0-9]+', reaction_details[1].text)
                feed_info['forward_comment'] = null_or_num(forward_comment)
                forward_like=  re.findall('[0-9]+', reaction_details[2].text)
                feed_info['forward_like']   = null_or_num(forward_like)
                
                
                feed_info['forward_hashtag_count'] = forward_text.count('#')/2
                forward_hashtag = re.findall('#\w+\#',forward_text) 
                feed_info['forward_hashtag'] = extract_hashtags(forward_hashtag)           
        else:
            
                feed_info['forward_profile_link'] = ""
                feed_info['forward_nick_name']  = ""
                feed_info['forward_text'] = ""
                feed_info['forward_datetime'] = ""
                feed_info['medium']=""
                feed_info['forward_forward']= 0
                feed_info['forward_comment'] = 0
                feed_info['forward_like'] = 0
                feed_info['forward_hashtag_count'] = 0
                feed_info['forward_hashtag'] = ""
                

        return feed_info          


def getcards(soup): 
    cards = soup.find_all("div", class_="card-wrap")
    return cards


def runpage(cards):

    df = pd.DataFrame()
    for card in cards: 
        try:
            feed_info = extract_feed(card)
            df = df.append(feed_info, ignore_index = True)
        except:
            pass
        
    return df
    
def main_perpage(soup): 
    
    cards = getcards(soup)
    df = runpage(cards)
    return df
    
#------------------------------------------------------------------------------

# define parameters (# yyyy-mm-dd; freq (per ? hr))  # collected up till 10/6
    
startdate ="2020-09-01"
enddate ="2021-06-01"
freq = 6
keyword_ls = ['康希諾', '復星', '杨森制药', '生物新技術', '科兴', '莫德納', '阿斯利康']



for keyword in keyword_ls:



#------------------------------------------------------------------------------

        
        
        # update cookie (run, time)
        #update_cookie(True, 40)
        
        # load in cookies and navigate to page; get link to all pages 
        s = requests.Session()
        
        
        for cookie in pickle.load(open("configuration/cookies/Login_Cookies.pkl","rb")): 
             s.cookies.set(cookie['name'], cookie['value'])
        
        
        
        
        # compute param 
        
        hrs = [hr for hr in range(24)]
        hrs.append(0)
        
        delta = date.fromisoformat(enddate) - date.fromisoformat(startdate) 
        
        nowstart = startdate
        nowend = nowstart
        
        
        # loop
        
        for day in range(int(delta.days+1)):
        
            for round in range(int(24/freq)): 
                
                starthr = hrs[round*freq]
                endhr = hrs[(round+1)*freq]
        
                if endhr == 0: 
                    nowend = date.fromisoformat(nowend) + timedelta(days=1)
                    nowend = nowend.strftime("%Y-%m-%d")
                print(f'Searching {keyword} -- {nowstart}:{starthr}hr to {nowend}:{endhr}hr')
                url = f"https://s.weibo.com/weibo?q={keyword}&typeall=1&suball=1&timescope=custom:{nowstart}-{starthr}:{nowend}-{endhr}&Refer=g"
        
                
                # search
                fetch_loop_flag = True
                while fetch_loop_flag == True:
                    try:
                        response = s.get(url, timeout = 5)
                        soup = BeautifulSoup(response.content)
                        fetch_loop_flag =False
                    except: 
                        fetch_loop_flag =True
                    
        
                
                try:     
                        page_links = soup.find('div', class_="m-page").find_all("a")
                        page_links = ['https://s.weibo.com/' + x['href'] for x in page_links[1:]]
                        
                except: 
                        page_links  =[url,url]
                        
                #----------------------------------------------------------------------
                
                
                
                
                search_result  = pd.DataFrame()
                
                for index, link in enumerate(page_links[:-1]): 
                    
                    page_loop_flag=True
                    while page_loop_flag==True:
                        try:
                            response = s.get(link,timeout = 5)
                            soup = BeautifulSoup(response.content)
                            page_loop_flag =False
                        except:
                            page_loop_flag =True
                    cards = getcards(soup)
                    df = pd.DataFrame()
                    for card in cards:
                        try:
                            ouput_dict123 = extract_feed(card)
                            df = df.append(ouput_dict123, ignore_index=True)
                        except:
                            pass
                        
                    
                    
                    #page = main_perpage(soup)
                    search_result = search_result.append(df)
                    print(f'Completed Page {index+1}.')
                    time.sleep(0.25)
                    
                
                search_result.to_csv(f"new_output/{nowstart}_{starthr}_{keyword}.csv")
                    
                
            nowstart = date.fromisoformat(nowstart) + timedelta(days=1)  
            nowstart = nowstart.strftime("%Y-%m-%d")
            
        print("Completed.")
                #----------------------------------------------------------------------
