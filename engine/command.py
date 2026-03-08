import pyttsx3
import speech_recognition as sr
import eel
import time
def speak(text):
    text = str(text)
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices') 
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 174)
    # eel calls are optional – they fail when called from background threads
    # before the browser is fully connected. Voice always works regardless.
    try:
        eel.DisplayMessage(text)
    except Exception:
        pass
    engine.say(text)
    try:
        eel.receiverText(text)
    except Exception:
        pass
    engine.runAndWait()


def takecommand():
    r = sr.Recognizer()

    with sr.Microphone() as source:
        print('listening....')
        try:
            eel.DisplayMessage('listening....')
        except Exception:
            pass

        # Calibrate to current ambient noise level
        r.adjust_for_ambient_noise(source, duration=0.5)
        r.dynamic_energy_threshold = False
        r.energy_threshold = max(r.energy_threshold * 1.2, 150)
        r.pause_threshold = 1.2        # wait 1.2 s of silence before ending
        r.non_speaking_duration = 0.4

        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=12)
        except Exception as e:
            print("microphone error:", e)
            return ""
    try:
        print('recognizing')
        try:
            eel.DisplayMessage('recognizing....')
        except Exception:
            pass
        query = r.recognize_google(audio, language='en-in')
        print(f"user said: {query}")
        time.sleep(2)
       
    except Exception as e:
        print("recognition error:", e)
        return ""
    
    return query.lower()

@eel.expose
def allCommands(message=1):
    # Wake-words that should NEVER be processed as commands
    WAKE_PHRASES = ["hey friday", "hey jarvis", "ok friday", "okay friday"]

    if message == 1:
        # Voice input: do NOT display user speech as a chat bubble
        query = takecommand()
        print(query)
    else:
        # Typed input: show it in chat as a sender bubble
        query = message
        try:
            eel.senderText(query)
        except Exception:
            pass

    # Guard: ignore if empty or is a wake-word phrase
    if not query or any(w in query.strip() for w in WAKE_PHRASES):
        try:
            eel.ShowHood()
        except Exception:
            pass
        return

    try:
        import re
        
        # ==========================================
        # 1. NLP Text Normalization & Cleaning
        # ==========================================
        query_text = query.strip()
        
        # ==========================================
        # 2. Intent Detection
        # ==========================================
        is_open_all = "open all leetcode" in query_text or "open all questions" in query_text
        is_solve_leetcode = not is_open_all and (any(word in query_text for word in ["solve leetcode", "leetcode problem", "solve problem", "solve lead code"]) or ("solve" in query_text and any(word in query_text for word in ["leetcode", "lead code", "leet code"])))
        is_run_solution = "run the solution" in query_text or "run solution" in query_text
        is_submit_solution = "submit the solution" in query_text or "submit solution" in query_text
        is_leetcode = not is_solve_leetcode and not is_open_all and any(word in query_text for word in ["leetcode", "lead code", "leet code"])
        is_github = "github" in query_text and any(word in query_text for word in ["my", "profile", "show", "check"])
        
        # Extract search intent safely
        search_target_text = re.sub(r'open\s+.*?\s+and\s+', '', query_text)
        search_match = re.search(r'\b(search for|search|google|find)\b\s+(.*)', search_target_text)
        
        is_open = not is_solve_leetcode and (query_text.startswith("open ") or " open " in query_text)
        is_youtube = "on youtube" in query_text
        is_time = "time" in query_text
        is_communication = any(word in query_text for word in ["send message", "phone call", "video call"])
        
        # ==========================================
        # 3. Smart Command Router
        # ==========================================
        if is_open_all:
            import engine.leetcode_bot as lb
            lb.open_all()
            
        elif is_run_solution:
            import engine.leetcode_bot as lb
            lb.run_code()
            
        elif is_submit_solution:
            import engine.leetcode_bot as lb
            lb.submit_code()
            
        elif is_solve_leetcode:
            # LEETCODE SOLVER
            import engine.leetcode_bot as lb
            from engine.features import chatBot
            lb.solve_and_insert(query_text, chatBot, chatBot)
            
        elif is_leetcode:
            # PERSONAL PROFILE QUERY: LeetCode
            from engine.features import checkLeetcode
            checkLeetcode()
            
        elif is_github:
            # PERSONAL PROFILE QUERY: GitHub
            import webbrowser
            speak("Showing your GitHub profile on screen")
            webbrowser.open("https://github.com/TusarGoswami")
            
        elif search_match:
            # WEB SEARCH
            from engine.features import searchGoogle
            searchGoogle(search_match.group(2).strip())
            
        elif is_youtube:
            # WEB NAVIGATION: Youtube Override
            from engine.features import PlayYoutube
            PlayYoutube(query_text)
            
        elif is_open:
            # SYSTEM & SMART URL NAVIGATION
            from engine.features import openCommand
            openCommand(query_text)
            
        elif is_time:
            # SYSTEM SENSOR: Time
            import datetime
            strTime = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"Sir, the time is {strTime}")
            
        elif is_communication:
            # SYSTEM ACTION: WhatsApp/Mobile Calls
            from engine.features import findContact, whatsApp, makeCall, sendMessage
            contact_no, name = findContact(query_text)
            if(contact_no != 0):
                speak("Which mode you want to use whatsapp or mobile")
                preferance = takecommand()

                if "mobile" in preferance:
                    if "send message" in query_text or "send sms" in query_text: 
                        speak("what message to send")
                        message = takecommand()
                        sendMessage(message, contact_no, name)
                    elif "phone call" in query_text:
                        makeCall(name, contact_no)
                    else:
                        speak("please try again")
                elif "whatsapp" in preferance:
                    message = ""
                    if "send message" in query_text:
                        message = 'message'
                        speak("what message to send")
                        query_text = takecommand()
                    elif "phone call" in query_text:
                        message = 'call'
                    else:
                        message = 'video call'
                                        
                    whatsApp(contact_no, query_text, message, name)
                    
        else:
            # GENERAL KNOWLEDGE / CHATBOT FALLBACK
            from engine.features import chatBot
            chatBot(query_text)
    except Exception as e:
        print("error:", e)
    
    try:
        eel.ShowHood()
    except Exception:
        pass