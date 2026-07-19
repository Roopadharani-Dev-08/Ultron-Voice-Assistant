import random
import wikipedia
import pywhatkit
import pyjokes
import webbrowser
from utils import clean_text, get_current_time, get_current_date, log

# Predefined conversational responses
CONVERSATION_RESPONSES = {
    "hello": [
        "Hello! How can I help you today?",
        "Hi there! How can I assist you?",
        "Greetings! How may I help you?"
    ],
    "hi": [
        "Hi! How's it going?",
        "Hello! What can I do for you?",
        "Hi there! I'm listening."
    ],
    "good morning": [
        "Good morning! I hope you have a wonderful day.",
        "Good morning! How can I help you start your day?"
    ],
    "good evening": [
        "Good evening! I hope your day went well. How can I assist you tonight?"
    ],
    "how are you": [
        "I am doing great, thank you for asking! How are you?",
        "I'm functioning at full capacity! How can I help you today?"
    ],
    "who are you": [
        "I am Ultron, your personal voice assistant.",
        "My name is Ultron. I'm a desktop assistant designed to help you with voice commands."
    ],
    "what is your name": [
        "I am Ultron.",
        "You can call me Ultron. I'm your desktop voice assistant."
    ],
    "thank you": [
        "You're very welcome!",
        "Happy to help!",
        "My pleasure!"
    ],
    "bye": [
        "Goodbye! Have a great day!",
        "Bye! Hope to talk to you again soon."
    ]
}

def execute_wikipedia_search(query: str) -> str:
    """
    Searches Wikipedia for the query and returns a 4-5 line summary.
    Handles disambiguation and missing page errors.
    """
    log("Wikipedia", f"Searching for: {query}")
    wikipedia.set_lang("en")
    try:
        # Fetch summary (sentences=4 should give ~4-5 lines of text)
        summary = wikipedia.summary(query, sentences=4, auto_suggest=False)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        # Try to get the summary for the first option listed
        first_option = e.options[0]
        log("Wikipedia", f"Disambiguation encountered. Trying first option: {first_option}")
        try:
            summary = wikipedia.summary(first_option, sentences=4, auto_suggest=False)
            return f"There are multiple matches. Here is information about '{first_option}':\n\n{summary}"
        except Exception:
            options_list = ", ".join(e.options[:3])
            return f"Your search '{query}' is ambiguous. It could refer to: {options_list}, etc. Please be more specific."
    except wikipedia.exceptions.PageError:
        log("Wikipedia", f"Page not found for: {query}")
        return f"I couldn't find any Wikipedia pages matching '{query}'. Please try another search."
    except Exception as e:
        log("Wikipedia", f"Error occurred: {str(e)}")
        return f"Sorry, I encountered an error searching Wikipedia: {str(e)}"

def process_command(raw_text: str) -> str:
    """
    Processes the raw spoken text, identifies the intent, and returns
    the text response that the assistant should say and display.
    """
    cleaned = clean_text(raw_text)
    log("Commands", f"Processing: '{raw_text}' -> cleaned: '{cleaned}'")
    
    if not cleaned:
        return "I didn't catch that. Could you please repeat?"

    # 1. Date and Time commands
    if cleaned in ["what time is it", "tell me the time", "time please", "what is the time"]:
        return f"The current time is {get_current_time()}."
    
    if cleaned in ["what is todays date", "whats todays date", "what day is today", "what is the date", "whats the date", "tell me the date"]:
        return f"Today is {get_current_date()}."

    # 2. Jokes
    if cleaned in ["tell me a joke", "make me laugh", "say a joke", "tell a joke", "joke please"]:
        try:
            return pyjokes.get_joke()
        except Exception as e:
            log("Jokes", f"Error fetching joke: {e}")
            return "Why did the computer go to the doctor? Because it had a virus! (Sorry, I couldn't fetch a fresh joke right now.)"

    # 3. Play YouTube songs/videos (starts with "play ")
    if cleaned.startswith("play "):
        song_query = raw_text[5:].strip()  # Use raw text to preserve case for YouTube search query
        if not song_query:
            return "What would you like me to play?"
        log("YouTube", f"Playing: '{song_query}'")
        try:
            pywhatkit.playonyt(song_query)
            return f"Playing '{song_query}' on YouTube."
        except Exception as e:
            log("YouTube", f"Error: {e}")
            # Fallback: open YouTube search in web browser
            search_url = f"https://www.youtube.com/results?search_query={song_query.replace(' ', '+')}"
            webbrowser.open(search_url)
            return f"Opening YouTube search for '{song_query}' in your browser."

    # 4. Wikipedia queries (starts with "what is " or "who is ")
    if cleaned.startswith("what is ") or cleaned.startswith("who is ") or cleaned.startswith("whats ") or cleaned.startswith("whos "):
        # Extract search query
        # We find the prefix in the cleaned text, then slice raw_text from that index
        prefixes = ["what is ", "who is ", "whats ", "whos "]
        search_query = ""
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                # Slice raw text based on prefix length
                search_query = raw_text[len(prefix):].strip()
                break
        
        # Strip question marks at the end if any
        if search_query.endswith("?"):
            search_query = search_query[:-1].strip()
            
        if not search_query:
            return "What would you like me to look up?"
            
        return execute_wikipedia_search(search_query)

    # 5. Basic Conversation Matching
    # Check for direct key matches
    for key, responses in CONVERSATION_RESPONSES.items():
        if cleaned == key or cleaned.startswith(key + " ") or cleaned.endswith(" " + key):
            return random.choice(responses)

    # 6. Fallback internet search
    # If we don't recognize the command, search Google
    log("Fallback", f"Unknown command: '{raw_text}'. Performing web search.")
    try:
        search_url = f"https://www.google.com/search?q={raw_text.replace(' ', '+')}"
        webbrowser.open(search_url)
        return f"I wasn't sure how to handle '{raw_text}', so I've opened a web search for you."
    except Exception as e:
        log("Fallback", f"Error opening browser: {e}")
        return "I am not sure how to answer that. Could you try asking in a different way?"
