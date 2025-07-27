#!/usr/bin/env python3
"""
Reddit Character.AI Config Generator

Generate Character.AI character definitions from Reddit user's public posts and comments.

This code was originally written by AI and prompted by fialovy. I'm sure we
won't be disclaiming this in 5 or 2 years, but I kinda feel the need in case
it gets weird...
"""

import praw
import re
import click
import os
import sys
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Conversation:
    """Represents a conversation thread for the character definition."""
    original_text: str
    reply_text: str
    score: int
    length: int

    def format_for_character_ai(self, user_placeholder: str) -> str:
        """Format the conversation for Character.AI definition."""
        # Clean up the text
        original_clean = self._clean_text(self.original_text)
        reply_clean = self._clean_text(self.reply_text)

        # Format as dialog
        return f"{user_placeholder}: {original_clean}\n{{{{char}}}}: {reply_clean}\n\n"

    def _clean_text(self, text: str) -> str:
        """Clean Reddit text for Character.AI format."""
        if not text:
            return ""

        # Remove Reddit formatting
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic
        text = re.sub(r'~~(.+?)~~', r'\1', text)      # Strikethrough
        text = re.sub(r'\^(.+?)', r'\1', text)        # Superscript
        text = re.sub(r'`(.+?)`', r'\1', text)        # Code

        # Remove quotes and references
        text = re.sub(r'^&gt;.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*&gt;.*$', '', text, flags=re.MULTILINE)

        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        # Remove Reddit user references
        text = re.sub(r'/u/\w+', '', text)
        text = re.sub(r'u/\w+', '', text)
        text = re.sub(r'/r/\w+', '', text)
        text = re.sub(r'r/\w+', '', text)

        # Clean up whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple newlines
        text = re.sub(r'[ \t]+', ' ', text)           # Multiple spaces
        text = text.strip()

        # Remove edit markers
        text = re.sub(r'\s*EDIT:.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'\s*Edit:.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)

        return text


class CharacterGenerator:
    """Generates Character.AI definitions from Reddit user data."""

    def __init__(self, reddit_instance: praw.Reddit):
        self.reddit = reddit_instance
        self.max_definition_length = 32000
        self.max_single_conversation_length = 800  # Leave room for multiple conversations
        self.min_comment_length = 10
        self.max_comment_length = 300

    def generate_character_definition(self, username: str, limit: int = 100) -> str:
        """Generate a Character.AI definition from a Reddit user's activity."""
        logger.info(f"Generating character definition for u/{username}")

        try:
            user = self.reddit.redditor(username)
            conversations = self._extract_conversations(user, limit)

            if not conversations:
                return f"No suitable conversations found for u/{username}. The user might have no public activity or all comments are too short/long."

            logger.info(f"Found {len(conversations)} suitable conversations")

            # Sort by score (engagement) and length for better quality
            conversations.sort(key=lambda x: (x.score, -x.length), reverse=True)

            definition = self._build_definition(conversations, username)

            logger.info(f"Generated definition with {len(definition)} characters")
            return definition

        except Exception as e:
            logger.error(f"Error generating definition for u/{username}: {e}")
            raise

    def _extract_conversations(self, user: praw.models.Redditor, limit: int) -> List[Conversation]:
        """Extract conversation pairs from user's comments."""
        conversations = []

        try:
            # Get user's comments
            comments = list(user.comments.new(limit=limit))
            logger.info(f"Processing {len(comments)} comments")

            for comment in comments:
                try:
                    # Skip deleted/removed comments
                    if not comment.body or comment.body in ['[deleted]', '[removed]']:
                        continue

                    # Filter by length
                    if len(comment.body) < self.min_comment_length or len(comment.body) > self.max_comment_length:
                        continue

                    # Get what they were replying to
                    parent = None
                    if comment.is_root:
                        # Reply to a post
                        parent = comment.submission
                        parent_text = parent.title
                        if parent.selftext and len(parent.selftext) < self.max_comment_length:
                            parent_text += f"\n{parent.selftext}"
                    else:
                        # Reply to another comment
                        parent = comment.parent()
                        if hasattr(parent, 'body'):
                            parent_text = parent.body
                        else:
                            continue

                    # Skip if parent is too long or short
                    if not parent_text or len(parent_text) < self.min_comment_length or len(parent_text) > self.max_comment_length:
                        continue

                    # Create conversation
                    conv = Conversation(
                        original_text=parent_text,
                        reply_text=comment.body,
                        score=max(comment.score, 0),
                        length=len(parent_text) + len(comment.body)
                    )

                    # Check if the formatted conversation would be too long
                    formatted_length = len(conv.format_for_character_ai("{{random_user_1}}"))
                    if formatted_length <= self.max_single_conversation_length:
                        conversations.append(conv)

                except Exception as e:
                    logger.debug(f"Error processing comment: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error accessing user comments: {e}")

        return conversations

    def _build_definition(self, conversations: List[Conversation], username: str) -> str:
        """Build the final Character.AI definition from conversations."""
        definition_parts = []
        current_length = 0
        user_counter = 1

        # Add a brief intro
        intro = f"This character is based on the Reddit user u/{username}. Here are examples of how they typically respond:\n\n"
        definition_parts.append(intro)
        current_length += len(intro)

        for conv in conversations:
            # Use different user placeholders for variety
            user_placeholder = f"{{{{random_user_{user_counter}}}}}"
            formatted_conv = conv.format_for_character_ai(user_placeholder)

            # Check if adding this conversation would exceed the limit
            if current_length + len(formatted_conv) > self.max_definition_length:
                break

            definition_parts.append(formatted_conv)
            current_length += len(formatted_conv)

            # Cycle through user placeholders (1-5 for variety)
            user_counter = (user_counter % 5) + 1

        definition = "".join(definition_parts)


        return definition


def setup_reddit_client() -> praw.Reddit:
    """Initialize PRAW Reddit client with config from praw.ini."""
    # Look for praw.ini in multiple locations (in order of preference)
    possible_paths = [
        Path.home() / ".config" / "praw.ini",  # XDG config directory
        Path.home() / ".praw.ini",             # PRAW's default location
        Path.home() / "reddit_credentials" / "praw.ini",  # Dedicated folder
    ]

    config_path = None
    for path in possible_paths:
        if path.exists():
            config_path = path
            logger.info(f"Using praw.ini from: {config_path}")
            break

    if not config_path:
        logger.error("praw.ini not found in any of these locations:")
        for path in possible_paths:
            logger.error(f"  - {path}")
        logger.error("")
        logger.error("Recommended setup:")
        logger.error("1. Create directory: mkdir -p ~/.config")
        logger.error("2. Copy template: cp praw.ini.template ~/.config/praw.ini")
        logger.error("3. Edit ~/.config/praw.ini with your Reddit API credentials")
        logger.error("4. Get credentials from https://www.reddit.com/prefs/apps/")
        sys.exit(1)

    try:
        reddit = praw.Reddit(config_interpolation="basic",
                           praw_config_file=str(config_path),
                           site_name="reddit_character_ai_config")
        # Test the connection
        reddit.user.me()  # This will fail if not properly authenticated
        return reddit
    except Exception as e:
        logger.error(f"Failed to authenticate with Reddit API: {e}")
        logger.error("Please check your praw.ini configuration")
        sys.exit(1)


@click.command()
@click.argument('username')
@click.option('--limit', '-l', default=100, help='Number of recent comments to analyze (default: 100)')
@click.option('--output', '-o', help='Output file path (default: stdout)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(username: str, limit: int, output: str, verbose: bool):
    """
    Generate a Character.AI character definition from a Reddit user's posts and comments.

    USERNAME: The Reddit username to analyze (without the u/ prefix)

    Example:
        python reddit_character_ai_config.py someuser
        python reddit_character_ai_config.py someuser --limit 200 --output character_def.txt
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Remove u/ prefix if present
    if username.startswith('u/'):
        username = username[2:]

    click.echo(f"🤖 Generating Character.AI definition for u/{username}")

    try:
        # Setup Reddit client
        reddit = setup_reddit_client()

        # Generate character definition
        generator = CharacterGenerator(reddit)
        definition = generator.generate_character_definition(username, limit)

        if not definition:
            click.echo("❌ No suitable content found for this user", err=True)
            sys.exit(1)

        # Output the definition
        if output:
            output_path = Path(output)
            output_path.write_text(definition, encoding='utf-8')
            click.echo(f"✅ Character definition saved to {output_path}")
            click.echo(f"📏 Definition length: {len(definition)}/32000 characters")
        else:
            click.echo("\n" + "="*50)
            click.echo("CHARACTER.AI DEFINITION")
            click.echo("="*50)
            click.echo(definition)
            click.echo("="*50)
            click.echo(f"📏 Length: {len(definition)}/32000 characters")

    except KeyboardInterrupt:
        click.echo("\n❌ Operation cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
