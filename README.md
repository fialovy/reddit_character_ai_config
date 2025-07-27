# Reddit Character.AI Config Generator

This tool generates
[Character.AI character definitions](https://book.character.ai/character-book/character-attributes/definition) 
based on a Reddit user's
public posts and comments. It was written for [fialovy](https://github.com/fialovy)
primarily via the Github Copilot in agent mode.


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

It intentionally does NOT look in the project directory; please do not
get into the habit of storing credentials files like that! D:

## Usage

### Command Line (Recommended)
```bash
uv run characteraiconfig <reddit_username_of_interest>
```

### Examples
```bash
# Basic usage
uv run characteraiconfig someuser

# With more comments and save to file
uv run characteraiconfig someuser --limit 200 --output character_def.txt

# Verbose mode to see what's happening
uv run characteraiconfig someuser --verbose
```


### What is it actually doing?:
- Fetch the user's recent comments and the posts/comments they were replying to
- Format them as Character.AI dialog examples, where the target user's comments are `{{char}}` responses. In other word, this user is 'the character.' The users who created the posts and/or comments that the target user responded to will be formatted as separate `{{random_user_1}}`, `{{random_user_2}}`, etc.
- Generate a character definition (max 32,000 characters)
- Output the formatted definition ready for Character.AI

