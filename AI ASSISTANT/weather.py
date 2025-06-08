#https://www.google.com/search?q=weather+in+ratnagiri
# user agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36
# span id=wob_tm

from requests_html import HTMLSession
import Speech_to_text 

def weather():
    s = HTMLSession()
    query = "Ratnagiri"
    url = f"https://www.google.com/search?q=weather+in+{query}"
    r= s.get(url,headers={'User_agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'})
    temp = r.html.find('span.wob_tm',first=True).text
    unit = r.html.find('div.vk_bk wob-unit span.wob_t',first=True).text
    desc = r.html.find('span#wob_dc',first=True).text
    return temp+" "+unit+" "+desc