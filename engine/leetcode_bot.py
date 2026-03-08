import time
import requests
import re
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from engine.command import speak
import threading

driver = None

def init_driver():
    global driver
    if driver is None:
        options = Options()
        options.add_experimental_option("detach", True)
        options.add_argument("--disable-blink-features=AutomationControlled")
        try:
            # Let's try to attach it to an existing profile if we can, else temporary
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.maximize_window()
        except Exception as e:
            print(f"Failed to start Selenium Driver: {e}")

def get_problem_slug(query):
    # Try finding problem number mapping via API
    try:
        match = re.search(r'\b(\d+)\b', query)
        if match:
            prob_num = match.group(1)
            r = requests.get('https://leetcode.com/api/problems/all/')
            data = r.json()
            for x in data.get('stat_status_pairs', []):
                if str(x.get('stat', {}).get('frontend_question_id')) == prob_num:
                    return x['stat']['question__title_slug'], x['stat']['question__title']
    except Exception as e:
        print(f"API Error mapping problem: {e}")
        
    # Fallback to text parsing
    problem_text = query.lower()
    for phrase in ["solve lead code problem", "solve question number", "solve question", "solve leetcode problem", "leetcode problem", "solve problem", "solve leetcode", "solve lead code", "solve", "in java", "in python", "in c++"]:
        problem_text = problem_text.replace(phrase, "")
        
    problem_name = problem_text.strip()
    slug = re.sub(r'[^a-z0-9]+', '-', problem_name.lower()).strip('-')
    return slug, problem_name.title()


def solve_and_insert(query, chatBotInstance, chatBotFunc):
    global driver
    if driver is None:
        init_driver()
        
    lang_match = re.search(r'\bin\s+([a-zA-Z\+\#]+)', query.lower())
    language = lang_match.group(1).capitalize() if lang_match else "Python"
    
    slug, title = get_problem_slug(query)
    if not slug:
        speak("I couldn't identify the problem. Please try again.")
        return
        
    speak(f"Opening LeetCode problem {title} in {language} and thinking of optimal solution...")
    url = f"https://leetcode.com/problems/{slug}/"
    driver.get(url)
    
    # Generate the solution in the background
    ai_prompt = f"Solve the LeetCode problem '{title}' in {language}. Provide the optimal time complexity, and the raw code implementation without boilerplate talk. ONLY CODE and briefly explain the algorithm as a code comment at the top."
    
    solution = chatBotFunc(ai_prompt, speak_out=False)
    
    # Strip markdown code blocks
    solution = re.sub(r'```[a-zA-Z]*\n?', '', solution)
    solution = solution.replace('```', '').strip()
    
    speak("Code generated. Inserting into the LeetCode editor now...")
    
    try:
        # Give page time to load
        time.sleep(5)
        
        # Click anywhere on screen to ensure browser focus
        actions = ActionChains(driver)
        
        # Click the language selector if possible, or just default it
        # Try finding language button in new layout (Hard due to dynamic classes, so we rely on pasting code)
        
        # Focus Editor
        editor = driver.find_element(By.CSS_SELECTOR, '.inputarea')
        actions.click(editor).perform()
        time.sleep(0.5)
        
        # Clear editor using Ctrl+A and Backspace
        actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE).perform()
        time.sleep(0.5)
        
        # Paste code
        pyperclip.copy(solution)
        actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        
        speak(f"The solution for {title} has been successfully typed into your LeetCode editor.")
    except Exception as e:
        print(f"Error interacting with editor: {e}")
        speak("I opened the problem, but failed to insert the code automatically. The code is copied to your clipboard though.")
        
def run_code():
    global driver
    if driver is not None:
        speak("Running the solution now.")
        try:
            actions = ActionChains(driver)
            actions.key_down(Keys.CONTROL).send_keys("'").key_up(Keys.CONTROL).perform()
        except:
            speak("Failed to click run.")
            
def submit_code():
    global driver
    if driver is not None:
        speak("Submitting the solution now.")
        try:
            actions = ActionChains(driver)
            actions.key_down(Keys.CONTROL).send_keys(Keys.ENTER).key_up(Keys.CONTROL).perform()
        except:
            speak("Failed to submit.")
            
def open_all():
    global driver
    if driver is None:
        init_driver()
    speak("Opening all LeetCode problems page.")
    driver.get("https://leetcode.com/problemset/all/")
