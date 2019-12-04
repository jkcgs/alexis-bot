import re

pat_tag = re.compile(r'^<(@!?|#|a?:([a-zA-Z0-9\-_]+):)(\d{10,19})>$')
pat_usertag = re.compile(r'^<@!?(\d{10,19})>$')
pat_channel = re.compile(r'^<#(\d{10,19})>$')
pat_subreddit = re.compile(r'^[a-zA-Z0-9_\-]{2,25}$')
pat_emoji = re.compile(r'<a?(:([a-zA-Z0-9\-_]+):)([0-9]+)>')
pat_normal_emoji = re.compile(r'^:[a-zA-Z\-_]+:$')
pat_snowflake = re.compile(r'^\d{10,19}$')
pat_colour = re.compile(r'^#?[0-9a-fA-F]{6}$')
pat_delta = re.compile(r'^([0-9]+[smhd])+$')
pat_delta_each = re.compile(r'([0-9]+[smhd])+')
pat_invite = re.compile(r'(?:https?://)?(discord(?:app\.com/invite|\.gg|\.me)/[a-zA-Z0-9]+)')
