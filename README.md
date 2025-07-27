# Reddit Character.AI Config Generator

[character.ai](https://character.ai/) is a fun platform that lets you create, configure, and talk to your own AI characters. You can set up
a character with just a name, tagline, and brief description of their personality. But it's even more fun and powerful to create an advanced
**[character definition](https://book.character.ai/character-book/character-attributes/definition)** with some sample conversations!


**What if you could make any Redditor (e.g., yourself) into a character?**

This tool can help you do just that by pulling the public comments and replies of the user of your choice and formatting them into
sample conversations. More specifically, it formats the target Reddit user's comments into the things said by `{{char}}`.
The users who created the posts and/or comments that the target user responded to will be formatted as separate
`{{random_user_1}}`, `{{random_user_2}}`, etc.

It's still up to you to set up the basics like your character's name, avatar, and initial description, but this script
will hopefully help you provide a lot more training data under "More options."


This is also [fialovy's](https://github.com/fialovy) first personal "vibe coding" (via Github Copilot agent) project as they say,
so caveat emptor. I'm sure we won't be writing disclaimers like this in 5 or even 2 years (and I promise I wrote
_this_ part myself), but I figured it was worth noting... "bAcK in myyy day"....etc.



## Setup

1. **Create a Reddit application** at https://www.reddit.com/prefs/apps/
   - Choose "script" as the app type
   - Note your `client_id` (under the app name) and `client_secret`

2. **Set up your credentials** (recommended location):
   ```bash
   # Create config directory
   mkdir -p ~/.config
   
   # Copy and edit the template
   cp praw.ini.template ~/.config/praw.ini
   
   # Edit with your credentials
   vim ~/.config/praw.ini  # or your preferred editor
   ```

3. **Run?!**

`uv run` will handle dependencies automatically, hopefully.

The tool will automatically look for `praw.ini` in these locations (in order):
- `~/.config/praw.ini` (recommended)
- `~/.praw.ini` (PRAW default)
- `~/reddit_credentials/praw.ini` (alternative)

It intentionally does NOT look in the project directory (see, I promise I reviewed and adjusted after the agent originally tried to do this as a fallback);
please do not get into the habit of storing credentials files like that! 

## Usage

### Command Line (Recommended)
```bash
uv run reddit_character_ai_config.py <reddit_username_of_interest>
```

### Examples
```bash
# Basic usage
uv run reddit_character_ai_config.py someuser

# With more comments and save to file for easy pasting into character.ai's "Definition" field under "More options"
uv run reddit_character_ai_config.py someuser --limit 200 --output character_def.txt

# Verbose mode to see what's happening
uv run reddit_character_ai_config.py someuser --verbose
```


