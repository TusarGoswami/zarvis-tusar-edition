import os
from shlex import quote
import re
import sqlite3
import struct
import subprocess
import time
import webbrowser
from playsound import playsound
import eel
import pyaudio
import pyautogui
from engine.command import speak

from engine.config import ASSISTANT_NAME
# Playing assiatnt sound function
import pywhatkit as kit
import pvporcupine

from engine.helper import extract_yt_term, remove_words
from hugchat import hugchat


con = sqlite3.connect("jarvis.db")
cursor = con.cursor()

@eel.expose
def playAssistantSound():
    music_dir = "www\\assets\\audio\\start_sound.mp3"
    playsound(music_dir)

    
def openCommand(query):
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "")
    query.lower()

    app_name = query.strip()

    if app_name != "":

        try:
            cursor.execute(
                'SELECT path FROM sys_command WHERE name IN (?)', (app_name,))
            results = cursor.fetchall()

            if len(results) != 0:
                speak("Opening "+query)
                os.startfile(results[0][0])

            elif len(results) == 0: 
                cursor.execute(
                'SELECT url FROM web_command WHERE name IN (?)', (app_name,))
                results = cursor.fetchall()
                
                if len(results) != 0:
                    speak("Opening "+query)
                    webbrowser.open(results[0][0])

                else:
                    speak("Opening "+query)
                    try:
                        os.system('start '+query)
                    except:
                        speak("not found")
        except:
            speak("some thing went wrong")

def searchGoogle(search_term):
    import urllib.parse
    import webbrowser
    from engine.command import speak
    
    encoded_search = urllib.parse.quote_plus(search_term)
    url = f"https://www.google.com/search?q={encoded_search}"
    speak(f"Searching Google for {search_term}")
    webbrowser.open(url)

def checkLeetcode():
    import requests
    from engine.command import speak
    from engine.config import LEETCODE_USERNAME
    
    url = 'https://leetcode.com/graphql'
    query = '''
    query getUserProfile($username: String!) {
      matchedUser(username: $username) {
        submitStats: submitStatsGlobal {
          acSubmissionNum {
            difficulty
            count
          }
        }
      }
    }
    '''
    variables = {'username': LEETCODE_USERNAME}
    payload = {
        'query': query,
        'variables': variables
    }
    
    speak(f"Checking your LeetCode profile for {LEETCODE_USERNAME}...")
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json', 'Referer': 'https://leetcode.com'})
        data = response.json()
        
        if 'data' in data and data['data'].get('matchedUser') is not None:
            stats = data['data']['matchedUser']['submitStats']['acSubmissionNum']
            solved = next((item['count'] for item in stats if item['difficulty'] == 'All'), 0)
            speak(f"You have solved a total of {solved} problems on LeetCode. Great job!")
            
            # Optionally actually open LeetCode for them
            import webbrowser
            webbrowser.open(f"https://leetcode.com/u/{LEETCODE_USERNAME}/")
        else:
            speak("Sorry, I could not find that LeetCode user name. Please check the config file.")
    except Exception as e:
        print(f"LeetCode API Error: {e}")
        speak("I encountered an error while trying to fetch your LeetCode stats.")

def checkGithub(query):
    import requests
    import webbrowser
    from engine.command import speak
    from engine.config import GITHUB_USERNAME
    
    speak(f"Fetching your GitHub profile statistics...")
    url = f"https://api.github.com/users/{GITHUB_USERNAME}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            public_repos = data.get("public_repos", 0)
            followers = data.get("followers", 0)
            following = data.get("following", 0)
            
            # Check intent dynamically
            query_lower = query.lower()
            if "follower" in query_lower:
                speak(f"You currently have {followers} followers on GitHub.")
            elif "following" in query_lower or "follow" in query_lower:
                speak(f"You are currently following {following} people on GitHub.")
            elif "repo" in query_lower or "stat" in query_lower:
                speak(f"You currently have {public_repos} public repositories on GitHub.")
            else:
                speak(f"You have {public_repos} repositories and {followers} followers on your GitHub profile.")
            
            # Show the profile on screen
            webbrowser.open(f"https://github.com/{GITHUB_USERNAME}")
        else:
            speak("I could not reach GitHub right now. Please try again later.")
            print(f"GitHub API Error: {response.text}")
    except Exception as e:
        print(f"GitHub Request Error: {e}")
        speak("I encountered an error trying to fetch your GitHub stats.")

def PlayYoutube(query):
    search_term = extract_yt_term(query)
    speak("Playing "+search_term+" on YouTube")
    kit.playonyt(search_term)


def hotword():
    porcupine=None
    paud=None
    audio_stream=None
    try:
       
        # pre trained keywords    
        porcupine=pvporcupine.create(keywords=["jarvis","alexa"]) 
        paud=pyaudio.PyAudio()
        audio_stream=paud.open(rate=porcupine.sample_rate,channels=1,format=pyaudio.paInt16,input=True,frames_per_buffer=porcupine.frame_length)
        
        # loop for streaming
        while True:
            keyword=audio_stream.read(porcupine.frame_length)
            keyword=struct.unpack_from("h"*porcupine.frame_length,keyword)

            # processing keyword comes from mic 
            keyword_index=porcupine.process(keyword)

            # checking first keyword detetcted for not
            if keyword_index>=0:
                print("hotword detected")

                # pressing shorcut key win+j
                import pyautogui as autogui
                autogui.keyDown("win")
                autogui.press("j")
                time.sleep(2)
                autogui.keyUp("win")
                
    except:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()



# find contacts
def findContact(query):
    
    words_to_remove = [ASSISTANT_NAME, 'make', 'a', 'to', 'phone', 'call', 'send', 'message', 'wahtsapp', 'video']
    query = remove_words(query, words_to_remove)

    try:
        query = query.strip().lower()
        cursor.execute("SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?", ('%' + query + '%', query + '%'))
        results = cursor.fetchall()
        print(results[0][0])
        mobile_number_str = str(results[0][0])

        if not mobile_number_str.startswith('+91'):
            mobile_number_str = '+91' + mobile_number_str

        return mobile_number_str, query
    except:
        speak('not exist in contacts')
        return 0, 0
    
def whatsApp(mobile_no, message, flag, name):
    

    if flag == 'message':
        target_tab = 12
        jarvis_message = "message send successfully to "+name

    elif flag == 'call':
        target_tab = 7
        message = ''
        jarvis_message = "calling to "+name

    else:
        target_tab = 6
        message = ''
        jarvis_message = "staring video call with "+name


    # Encode the message for URL
    encoded_message = quote(message)
    print(encoded_message)
    # Construct the URL
    whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"

    # Construct the full command
    full_command = f'start "" "{whatsapp_url}"'

    # Open WhatsApp with the constructed URL using cmd.exe
    subprocess.run(full_command, shell=True)
    time.sleep(5)
    subprocess.run(full_command, shell=True)
    
    pyautogui.hotkey('ctrl', 'f')

    for i in range(1, target_tab):
        pyautogui.hotkey('tab')

    pyautogui.hotkey('enter')
    speak(jarvis_message)

# ── AI Chat Backend ──────────────────────────────────────────────────────────
# Primary  : Google Gemini – tries models in order of free-tier availability
# Fallback : Wikipedia (only if the result is actually relevant to the query)
# ─────────────────────────────────────────────────────────────────────────────

_gemini_client = None

# Models tried in order – tested and confirmed available for this API key
GEMINI_MODELS = [
    "gemini-2.5-flash",        # ✅ confirmed working
    "gemini-2.0-flash-001",    # stable snapshot
    "gemini-2.0-flash",        # latest (may hit quota)
]

_SYSTEM_PROMPT = (
    "You are Zarvis, a smart and friendly AI assistant. "
    "Keep answers concise and spoken-friendly (2-4 sentences max). "
    "No markdown, no bullet points — plain natural spoken English only."
)

def _get_gemini_client():
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client
    try:
        from google import genai
        from engine.config import GEMINI_API_KEY
        if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            return None
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("[ChatBot] Gemini client ready ✅")
        return _gemini_client
    except Exception as e:
        print(f"[ChatBot] Gemini init error: {e}")
        return None


def _gemini_ask(user_input):
    """Try each model in GEMINI_MODELS; on 429 wait the suggested retry delay."""
    client = _get_gemini_client()
    if not client:
        return None

    full_prompt = f"{_SYSTEM_PROMPT}\n\nUser: {user_input}\nZarvis:"

    for model_name in GEMINI_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt
            )
            text = response.text.strip()
            if text:
                print(f"[ChatBot] {model_name} ▶ {text}")
                return text
        except Exception as e:
            err = str(e)
            if "429" in err:
                # Extract retry delay if provided (e.g. "retryDelay: '16s'")
                import re
                delay_match = re.search(r"'(\d+)s'", err)
                delay = int(delay_match.group(1)) + 1 if delay_match else 5
                print(f"[ChatBot] {model_name} quota hit – waiting {delay}s then trying next model...")
                time.sleep(delay)
            else:
                print(f"[ChatBot] {model_name} error: {e}")

    return None  # all models failed


def _wikipedia_ask(user_input):
    """
    Search Wikipedia only for clear factual/entity queries.
    Returns None if the result doesn't seem relevant to what was asked.
    """
    try:
        import wikipedia
        wikipedia.set_lang("en")

        # Search first to get the most relevant page title
        results = wikipedia.search(user_input, results=3)
        if not results:
            return None

        # Try each search result until we find a relevant one
        query_words = set(
            w.lower() for w in user_input.split()
            if len(w) > 3 and w.lower() not in
            {"what","when","where","which","that","this","have","does","with","from","tell","about","please"}
        )

        for title in results:
            try:
                summary = wikipedia.summary(title, sentences=2, auto_suggest=False)
                summary_lower = summary.lower()
                # Relevance check: at least 1 query keyword must appear in the result
                if any(w in summary_lower for w in query_words):
                    print(f"[ChatBot] Wikipedia ({title}) ▶ {summary}")
                    return summary.strip()
            except Exception:
                continue

        return None  # nothing relevant found
    except Exception as e:
        print(f"[ChatBot] Wikipedia error: {e}")
        return None


def chatBot(query, speak_out=True):
    """
    Answer any question or task.
    Priority: Gemini (model chain) → Wikipedia (relevance-checked) → fallback msg.
    """
    user_input = query.strip()

    # ── 1. Google Gemini (tries multiple models) ──────────────────────────────
    result = _gemini_ask(user_input)
    if result:
        if speak_out:
            speak(result)
        return result

    # ── 2. Wikipedia (relevance-validated) ───────────────────────────────────
    result = _wikipedia_ask(user_input)
    if result:
        if speak_out:
            speak(result)
        return result

    # ── 3. Final fallback ─────────────────────────────────────────────────────
    if not _get_gemini_client():
        msg = ("I need a Gemini API key to answer. "
               "Please add your free key to engine/config.py under GEMINI_API_KEY.")
    else:
        msg = "I'm sorry, I couldn't find an answer right now. Please try again in a moment."
    print(f"[ChatBot] fallback ▶ {msg}")
    if speak_out:
        speak(msg)
    return msg


def solveLeetcode(query):
    import re
    import webbrowser
    from engine.command import speak

    # Extract language
    lang_match = re.search(r'\bin\s+([a-zA-Z\+\#]+)', query.lower())
    language = lang_match.group(1).capitalize() if lang_match else "Python"
    
    # Extract problem name/number
    problem_text = query.lower()
    for phrase in ["solve lead code problem", "solve problem", "solve leetcode problem", "leetcode problem", "solve leetcode", "solve lead code", "solve"]:
        problem_text = problem_text.replace(phrase, "")
    if " in " in problem_text:
        problem_text = problem_text.split(" in ")[0]
        
    problem_name = problem_text.strip()
    if not problem_name:
        speak("I couldn't catch the problem name. Please try again.")
        return
        
    # Generate slug (e.g. "two sum" -> "two-sum")
    slug = re.sub(r'[^a-z0-9]+', '-', problem_name.lower()).strip('-')
    
    url = f"https://leetcode.com/problems/{slug}/"
    speak(f"Opening LeetCode problem {problem_name} and generating {language} solution...")
    webbrowser.open(url)
    
    # Generate solution using our AI
    ai_prompt = f"Solve the LeetCode problem '{problem_name}' in {language}. Provide a very brief 1-sentence explanation of the approach, the optimal time complexity, and the code implementation."
    
    speak("Thinking of the optimal solution. Please wait...")
    solution = chatBot(ai_prompt, speak_out=False)
    
    print("\n" + "="*50)
    print(f"LEETCODE SOLUTION: {problem_name.upper()} ({language})")
    print("="*50)
    print(solution)
    print("="*50 + "\n")
    
    speak(f"I have generated the {language} solution for {problem_name} and displayed it on your screen.")

# android automation

def makeCall(name, mobileNo):
    mobileNo =mobileNo.replace(" ", "")
    speak("Calling "+name)
    command = 'adb shell am start -a android.intent.action.CALL -d tel:'+mobileNo
    os.system(command)


# to send message
def sendMessage(message, mobileNo, name):
    from engine.helper import replace_spaces_with_percent_s, goback, keyEvent, tapEvents, adbInput
    message = replace_spaces_with_percent_s(message)
    mobileNo = replace_spaces_with_percent_s(mobileNo)
    speak("sending message")
    goback(4)
    time.sleep(1)
    keyEvent(3)
    # open sms app
    tapEvents(136, 2220)
    #start chat
    tapEvents(819, 2192)
    # search mobile no
    adbInput(mobileNo)
    #tap on name
    tapEvents(601, 574)
    # tap on input
    tapEvents(390, 2270)
    #message
    adbInput(message)
    #send
    tapEvents(957, 1397)
    speak("message send successfully to "+name)