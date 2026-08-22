#!/usr/bin/env python3
"""Build a lesson book from local essays.jsonl + tweets.jsonl.

Essay quotes start from a curated canon, then a miner pulls more
standalone PG-shaped sentences from the full corpus. Tweets are
short standalone aphorisms that match a chapter.
"""

from __future__ import annotations

import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from labels import CHAPTER_TOPICS, labeled_topic, load_cache, lookup

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "book"
OUT.mkdir(exist_ok=True)

CHAPTERS = [
    {"id": "start", "section": "STARTUPS", "title": "How to Start"},
    {"id": "want", "section": "STARTUPS", "title": "Something People Want"},
    {"id": "scale", "section": "STARTUPS", "title": "Do Things That Don't Scale"},
    {"id": "growth", "section": "STARTUPS", "title": "Growth"},
    {"id": "fundraising", "section": "STARTUPS", "title": "Fundraising"},
    {"id": "schlep", "section": "STARTUPS", "title": "Schlep Blindness"},
    {"id": "founders", "section": "STARTUPS", "title": "Founders"},
    {"id": "maker", "section": "WORK", "title": "Maker's Schedule"},
    {"id": "great-work", "section": "WORK", "title": "Great Work"},
    {"id": "taste", "section": "WORK", "title": "Taste"},
    {"id": "writing", "section": "MIND", "title": "Writing"},
    {"id": "ideas", "section": "MIND", "title": "Ideas"},
    {"id": "identity", "section": "MIND", "title": "Keep Your Identity Small"},
    {"id": "wealth", "section": "LIFE", "title": "How to Make Wealth"},
    {"id": "cities", "section": "LIFE", "title": "Cities and Ambition"},
    {"id": "young", "section": "LIFE", "title": "What You'll Wish You'd Known"},
    {"id": "nerds", "section": "LIFE", "title": "Nerds"},
]

# (chapter, slug, topic, title, excerpt) — excerpt must appear in that essay's body.
CANON: list[tuple[str, str, str, str, str]] = [
    (
        "start",
        "start",
        "People",
        "You need three things.",
        "You need three things to create a successful startup: to start with good people, to make something customers actually want, and to spend as little money as possible.",
    ),
    (
        "start",
        "start",
        "Ideas",
        "You don't need a brilliant idea.",
        "In particular, you don't need a brilliant idea to start a startup around.",
    ),
    (
        "start",
        "start",
        "Ideas",
        "There is no magic step.",
        "There is no magically difficult step that requires brilliance to solve.",
    ),
    (
        "start",
        "before",
        "Instincts",
        "Startups are counterintuitive.",
        "Startups are very counterintuitive.",
    ),
    (
        "start",
        "before",
        "Users",
        "Be an expert on users, not startups.",
        "The way to succeed in a startup is not to be an expert on startups, but to be an expert on your users and the problem you're solving for them.",
    ),
    (
        "start",
        "notnot",
        "Failure",
        "Failure is cheaper than it looks.",
        "Even the founders who fail don't seem to have such a bad time.",
    ),
    (
        "want",
        "startupideas",
        "Ideas",
        "Don't try to think of startup ideas.",
        "The way to get startup ideas is not to try to think of startup ideas.",
    ),
    (
        "want",
        "startupideas",
        "Problems",
        "Look for problems you have.",
        "It's to look for problems, preferably problems you have yourself.",
    ),
    (
        "want",
        "startupideas",
        "Ideas",
        "The best ideas are wanted, buildable, and overlooked.",
        "The very best startup ideas tend to have three things in common: they're something the founders themselves want, that they themselves can build, and that few others realize are worth doing.",
    ),
    (
        "want",
        "startupideas",
        "Problems",
        "The common mistake is solving a problem no one has.",
        "by far the most common mistake startups make is to solve problems no one has.",
    ),
    (
        "want",
        "organic",
        "Ideas",
        "What do you wish someone would make for you?",
        "The best way to come up with startup ideas is to ask yourself the question: what do you wish someone would make for you?",
    ),
    (
        "want",
        "users",
        "Users",
        "Explain what you've learned from users.",
        "the best advice I could give for getting in, per word, was Explain what you've learned from users.",
    ),
    (
        "scale",
        "ds",
        "Unscalable",
        "Do things that don't scale.",
        "One of the most common types of advice we give at Y Combinator is to do things that don't scale.",
    ),
    (
        "scale",
        "ds",
        "Unscalable",
        "Founders make startups take off.",
        "Actually startups take off because the founders make them take off.",
    ),
    (
        "scale",
        "ds",
        "Users",
        "Recruit users manually.",
        "The most common unscalable thing founders have to do at the start is to recruit users manually.",
    ),
    (
        "scale",
        "ds",
        "Users",
        "Go get them.",
        "You can't wait for users to come to you. You have to go out and get them.",
    ),
    (
        "growth",
        "growth",
        "Definition",
        "A startup is designed to grow fast.",
        "A startup is a company designed to grow fast.",
    ),
    (
        "growth",
        "growth",
        "Definition",
        "Growth is the only essential.",
        "The only essential thing is growth.",
    ),
    (
        "growth",
        "growth",
        "Compass",
        "Growth makes other decisions easy.",
        "if you get growth, everything else tends to fall into place.",
    ),
    (
        "growth",
        "growth",
        "Compass",
        "Use growth as a compass.",
        "You can use growth like a compass to make almost every decision you face.",
    ),
    (
        "growth",
        "aord",
        "Default alive",
        "Know if you're default alive.",
        "Half the founders I talk to don't know whether they're default alive or default dead.",
    ),
    (
        "growth",
        "aord",
        "Default alive",
        "Ask too early, not too late.",
        "instead of starting to ask too late whether you're default alive or default dead, start asking too early.",
    ),
    (
        "fundraising",
        "fundraising",
        "Priority",
        "Raising money is second.",
        "Raising money is the second hardest part of starting a startup.",
    ),
    (
        "fundraising",
        "fundraising",
        "Priority",
        "Making something people want comes first.",
        "The hardest part is making something people want: most startups that die, die because they didn't do that.",
    ),
    (
        "fundraising",
        "fundraising",
        "Investors",
        "Investors are customers, not bosses.",
        "Investors evaluate startups the way customers evaluate products, not the way bosses evaluate employees.",
    ),
    (
        "fundraising",
        "fundraising",
        "Investors",
        "Don't take rejection personally.",
        "Don't take rejection personally.",
    ),
    (
        "fundraising",
        "fundraising",
        "Investors",
        "Avoid inexperienced investors.",
        "Avoid inexperienced investors.",
    ),
    (
        "fundraising",
        "hiresfund",
        "Notes",
        "Notes close faster.",
        "The reason startups have been using more convertible notes in angel rounds is that they make deals close faster.",
    ),
    (
        "fundraising",
        "hiresfund",
        "Investors",
        "Investors follow other investors.",
        "By far the biggest influence on investors' opinions of a startup is the opinion of other investors.",
    ),
    (
        "schlep",
        "schlep",
        "Blindness",
        "Great ideas are hiding in ugly work.",
        "There are great startup ideas lying around unexploited right under our noses.",
    ),
    (
        "schlep",
        "schlep",
        "Blindness",
        "That's schlep blindness.",
        "One reason we don't see them is a phenomenon I call schlep blindness.",
    ),
    (
        "schlep",
        "schlep",
        "Hard work",
        "A company is the schleps it will take on.",
        "A company is defined by the schleps it will undertake.",
    ),
    (
        "schlep",
        "schlep",
        "Hard work",
        "Jump in.",
        "schleps should be dealt with the same way you'd deal with a cold swimming pool: just jump in.",
    ),
    (
        "schlep",
        "schlep",
        "Hard work",
        "Don't shrink from the path.",
        "you should never shrink from it if it's on the path to something great.",
    ),
    (
        "schlep",
        "13sentences",
        "Users",
        "Make a few people really happy.",
        "it's better to make a few people really happy than to make a lot of people semi-happy.",
    ),
    (
        "schlep",
        "13sentences",
        "Cofounders",
        "Pick good cofounders.",
        "Pick good cofounders.",
    ),
    (
        "schlep",
        "13sentences",
        "Launch",
        "Launch fast.",
        "Launch fast.",
    ),
    (
        "schlep",
        "13sentences",
        "Ideas",
        "Let your idea evolve.",
        "Let your idea evolve.",
    ),
    (
        "schlep",
        "13sentences",
        "Users",
        "Understand your users.",
        "Understand your users.",
    ),
    (
        "schlep",
        "13sentences",
        "Users",
        "A few who love you beat many who are lukewarm.",
        "Better to make a few users love you than a lot ambivalent.",
    ),
    (
        "schlep",
        "13sentences",
        "Measure",
        "You make what you measure.",
        "You make what you measure.",
    ),
    (
        "schlep",
        "13sentences",
        "Money",
        "Spend little.",
        "Spend little.",
    ),
    (
        "schlep",
        "13sentences",
        "Money",
        "Get ramen profitable.",
        "Get ramen profitable.",
    ),
    (
        "schlep",
        "startuplessons",
        "Launch",
        "Release a version 1, then listen.",
        "get a version 1 out fast, then improve it based on users' reactions.",
    ),
    (
        "schlep",
        "startupmistakes",
        "Users",
        "The one fatal mistake is not making something users want.",
        "There's just one mistake that kills startups: not making something users want.",
    ),
    (
        "founders",
        "founders",
        "Determination",
        "Past a threshold, determination beats intelligence.",
        "as long as you're over a certain threshold of intelligence, what matters most is determination.",
    ),
    (
        "founders",
        "founders",
        "Flexibility",
        "Modify your dreams on the fly.",
        "The world of startups is so unpredictable that you need to be able to modify your dreams on the fly.",
    ),
    (
        "founders",
        "relres",
        "Resourcefulness",
        "Be relentlessly resourceful.",
        "A couple days ago I finally got being a good startup founder down to two words: relentlessly resourceful.",
    ),
    (
        "founders",
        "relres",
        "Resourcefulness",
        "Don't be hapless.",
        "To be hapless is to be battered by circumstances — to let the world have its way with you, instead of having your way with the world.",
    ),
    (
        "founders",
        "foundermode",
        "Founder mode",
        "Founder mode is not manager mode.",
        "in effect there are two different ways to run a company: founder mode and manager mode.",
    ),
    (
        "founders",
        "foundermode",
        "Founder mode",
        "Founders can do things managers can't.",
        "There are things founders can do that managers can't, and not doing them feels wrong to founders, because it is.",
    ),
    (
        "maker",
        "makersschedule",
        "Schedule",
        "Makers and managers use time differently.",
        "There are two types of schedule, which I'll call the manager's schedule and the maker's schedule.",
    ),
    (
        "maker",
        "makersschedule",
        "Schedule",
        "You can't make things in hour slots.",
        "You can't write or program well in units of an hour.",
    ),
    (
        "maker",
        "makersschedule",
        "Meetings",
        "Meetings are a disaster on a maker's schedule.",
        "When you're operating on the maker's schedule, meetings are a disaster.",
    ),
    (
        "maker",
        "makersschedule",
        "Meetings",
        "One meeting can blow an afternoon.",
        "A single meeting can blow a whole afternoon, by breaking it into two pieces each too small to do anything hard in.",
    ),
    (
        "maker",
        "makersschedule",
        "Meetings",
        "A meeting is an exception.",
        "For someone on the maker's schedule, having a meeting is like throwing an exception.",
    ),
    (
        "great-work",
        "greatwork",
        "Choosing",
        "First, decide what to work on.",
        "The first step is to decide what to work on.",
    ),
    (
        "great-work",
        "greatwork",
        "Choosing",
        "Aptitude, interest, and scope.",
        "it has to be something you have a natural aptitude for, that you have a deep interest in, and that offers scope to do great work.",
    ),
    (
        "great-work",
        "greatwork",
        "Doing",
        "Figure out what to work on by working.",
        "The way to figure out what to work on is by working.",
    ),
    (
        "great-work",
        "greatwork",
        "Doing",
        "Guess, then start.",
        "If you're not sure what to work on, guess. But pick something and get going.",
    ),
    (
        "great-work",
        "greatwork",
        "Doing",
        "Don't let work mean other people's tasks.",
        "Don't let \"work\" mean something other people tell you to do.",
    ),
    (
        "great-work",
        "love",
        "Love",
        "To do something well you have to like it.",
        "To do something well you have to like it.",
    ),
    (
        "great-work",
        "love",
        "Love",
        "Do what you love.",
        "We've got it down to four words: \"Do what you love.\"",
    ),
    (
        "great-work",
        "when",
        "Choosing",
        "Don't wait till the end of college.",
        "Don't wait till the end of college to figure out what to work on.",
    ),
    (
        "taste",
        "taste",
        "Taste",
        "You need taste to make good things.",
        "We need good taste to make good things.",
    ),
    (
        "taste",
        "goodtaste",
        "Taste",
        "If taste is fake, art is fake.",
        "If there's no such thing as good taste, then there's no such thing as good art.",
    ),
    (
        "writing",
        "simply",
        "Simplicity",
        "Write with ordinary words.",
        "I try to write using ordinary words and simple sentences.",
    ),
    (
        "writing",
        "simply",
        "Simplicity",
        "Save the reader's energy for the idea.",
        "The less energy they expend on your prose, the more they'll have left for your ideas.",
    ),
    (
        "writing",
        "simply",
        "Simplicity",
        "Writing simply keeps you honest.",
        "writing simply keeps you honest.",
    ),
    (
        "writing",
        "useful",
        "Usefulness",
        "An essay should be useful.",
        "an essay should be useful.",
    ),
    (
        "writing",
        "useful",
        "Usefulness",
        "Tell people something true, important, and new.",
        "Useful writing tells people something true and important that they didn't already know, and tells them as unequivocally as possible.",
    ),
    (
        "writing",
        "writes",
        "Thinking",
        "Writing is thinking clearly.",
        "To write well you have to think clearly, and thinking clearly is hard.",
    ),
    (
        "writing",
        "writes",
        "Thinking",
        "Writes and write-nots.",
        "The result will be a world divided into writes and write-nots.",
    ),
    (
        "ideas",
        "getideas",
        "Anomalies",
        "Notice what seems strange, missing, or broken.",
        "The way to get new ideas is to notice anomalies: what seems strange, or missing, or broken?",
    ),
    (
        "ideas",
        "getideas",
        "Anomalies",
        "Look at the frontiers of knowledge.",
        "the best place to look for them is at the frontiers of knowledge.",
    ),
    (
        "ideas",
        "ideas",
        "Value",
        "Startup ideas are not million-dollar ideas.",
        "startup ideas are not million dollar ideas",
    ),
    (
        "ideas",
        "ideas",
        "Value",
        "People overvalue ideas.",
        "They overvalue ideas.",
    ),
    (
        "identity",
        "identity",
        "Identity",
        "You can't argue about something that's part of your identity.",
        "people can never have a fruitful argument about something that's part of their identity.",
    ),
    (
        "identity",
        "identity",
        "Identity",
        "Keep your identity small.",
        "The more labels you have for yourself, the dumber they make you.",
    ),
    (
        "identity",
        "say",
        "Fashion",
        "Moral fashions are as real as clothing fashions.",
        "What scares me is that there are moral fashions too.",
    ),
    (
        "identity",
        "say",
        "Fashion",
        "Every era believes ridiculous things.",
        "In every period, people believed things that were just ridiculous, and believed them so strongly that you would have gotten in terrible trouble for saying otherwise.",
    ),
    (
        "identity",
        "mean",
        "Character",
        "Being mean makes you stupid.",
        "being mean makes you stupid.",
    ),
    (
        "identity",
        "mean",
        "Character",
        "Mean people fail.",
        "how consistently successful startup founders turn out to be good people, and how consistently bad people fail as startup founders.",
    ),
    (
        "wealth",
        "wealth",
        "Getting rich",
        "Start or join a startup.",
        "If you wanted to get rich, how would you do it? I think your best bet would be to start or join a startup.",
    ),
    (
        "wealth",
        "wealth",
        "Getting rich",
        "Take on a hard technical problem.",
        "A startup is a small company that takes on a hard technical problem.",
    ),
    (
        "wealth",
        "wealth",
        "Compression",
        "A startup compresses a working life into a few years.",
        "you can think of a startup as a way to compress your whole working life into a few years.",
    ),
    (
        "cities",
        "cities",
        "Ambition",
        "Great cities attract ambitious people.",
        "Great cities attract ambitious people.",
    ),
    (
        "cities",
        "cities",
        "Ambition",
        "The city tells you to try harder.",
        "the city sends you a message: you could do more; you should try harder.",
    ),
    (
        "cities",
        "cities",
        "Messages",
        "New York: make more money.",
        "New York tells you, above all: you should make more money.",
    ),
    (
        "cities",
        "cities",
        "Messages",
        "Boston: be smarter.",
        "the message there is: you should be smarter.",
    ),
    (
        "cities",
        "cities",
        "Messages",
        "The Valley: be more powerful.",
        "the message the Valley sends is: you should be more powerful.",
    ),
    (
        "cities",
        "hubs",
        "Hubs",
        "Death is the default. Hubs are the antidote.",
        "death is the default for startups, and most towns don't save them.",
    ),
    (
        "young",
        "hs",
        "Plans",
        "Don't rush your life's work.",
        "You don't need to be in a rush to choose your life's work.",
    ),
    (
        "young",
        "hs",
        "Taste",
        "Discover what you like.",
        "What you need to do is discover what you like.",
    ),
    (
        "young",
        "hs",
        "Taste",
        "Work on stuff you like.",
        "You have to work on stuff you like if you want to be good at what you do.",
    ),
    (
        "young",
        "hs",
        "Plans",
        "Don't have fixed plans.",
        "In such a world it's not a good idea to have fixed plans.",
    ),
    (
        "nerds",
        "nerds",
        "Popularity",
        "Smart and popular pull in opposite directions.",
        "there is a strong correlation between being smart and being a nerd, and an even stronger inverse correlation between being a nerd and being popular.",
    ),
    (
        "nerds",
        "nerds",
        "Popularity",
        "Being smart seems to make you unpopular.",
        "Being smart seems to make you unpopular.",
    ),
    (
        "nerds",
        "fn",
        "Fierce",
        "Some nerds are fierce.",
        "In fact some nerds are quite fierce.",
    ),
    (
        "nerds",
        "fn",
        "Fierce",
        "Fierce nerds are at least moderately smart.",
        "Not all nerds are smart, but the fierce ones are always at least moderately so.",
    ),
    (
        "want",
        "ycombinator",
        "Motto",
        "Make something people want.",
        "That's why our motto is \"Make something people want.\"",
    ),
    (
        "want",
        "startupideas",
        "Ideas",
        "Live in the future, then build what's missing.",
        "Live in the future, then build what's missing.",
    ),
    (
        "want",
        "want",
        "Desire",
        "You can change what you want to want.",
        "It's possible to change what you want to want.",
    ),
    (
        "growth",
        "ramenprofitable",
        "Ramen",
        "Ramen profitable means you can live on the company.",
        "Ramen profitable means a startup makes just enough to pay the founders' living expenses.",
    ),
    (
        "growth",
        "fundraising",
        "Ramen",
        "Once you cross into ramen profitable, everything changes.",
        "Once you cross into ramen profitable, everything changes.",
    ),
    (
        "maker",
        "procrastination",
        "Work",
        "Good procrastination is avoiding errands.",
        "Good procrastination is avoiding errands to do real work.",
    ),
    (
        "maker",
        "top",
        "Attention",
        "Don't let the wrong idea sit on top.",
        "it's a disaster to let the wrong idea become the top one in your mind.",
    ),
    (
        "maker",
        "selfindulgence",
        "Time",
        "Fake work is how you lose time.",
        "The most dangerous way to lose time is not to spend it having fun, but to spend it doing fake work.",
    ),
    (
        "great-work",
        "hwh",
        "Effort",
        "Great things take hard work.",
        "if you want to do great things, you'll have to work very hard.",
    ),
    (
        "great-work",
        "hwh",
        "Effort",
        "Ability, practice, and effort.",
        "There are three ingredients in great work: natural ability, practice, and effort.",
    ),
    (
        "great-work",
        "early",
        "Fear",
        "Fear of lame work holds people back.",
        "One of the biggest things holding people back from doing great work is the fear of making something lame.",
    ),
    (
        "great-work",
        "early",
        "Doing",
        "Push through the lame stage.",
        "You have to push through this stage to reach the great work that lies beyond.",
    ),
    (
        "great-work",
        "own",
        "Projects",
        "A project of your own is different work.",
        "Working on a project of your own is as different from ordinary work as skating is from walking.",
    ),
    (
        "great-work",
        "work",
        "Fit",
        "If it doesn't feel like work, that's a signal.",
        "If something that seems like work to other people doesn't seem like work to you, that's something you're well suited for.",
    ),
    (
        "great-work",
        "superlinear",
        "Returns",
        "Half as good means no customers.",
        "If your product is only half as good as your competitor's, you don't get half as many customers.",
    ),
    (
        "founders",
        "earnest",
        "Earnestness",
        "Formidable and earnest is nearly unstoppable.",
        "when founders are both formidable (another of our words) and earnest, they're as close to unstoppable as you get.",
    ),
    (
        "founders",
        "word",
        "Resourcefulness",
        "Wise people need one word.",
        "if someone is wise, all you have to do is say one word to them, and they'll understand immediately.",
    ),
    (
        "founders",
        "determination",
        "Determination",
        "Smart is not the deciding factor.",
        "while it certainly helps to be smart, it's not the deciding factor.",
    ),
    (
        "ideas",
        "sun",
        "Insights",
        "The best insights are general and surprising.",
        "The most valuable insights are both general and surprising.",
    ),
    (
        "ideas",
        "smart",
        "Ideas",
        "Smart is not the same as new ideas.",
        "Being very smart was a necessary precondition for having those ideas, but the two are not identical.",
    ),
    (
        "young",
        "vb",
        "Time",
        "If life feels too short for something, drop it.",
        "If you find yourself thinking that life is too short for something, you should try to eliminate it if you can.",
    ),
    (
        "young",
        "todo",
        "Advice",
        "Don't be a cog.",
        "don't be a cog.",
    ),
    (
        "young",
        "lesson",
        "School",
        "The damaging lesson was grades.",
        "The most damaging thing you learned in school wasn't something you learned in any specific class.",
    ),
    (
        "young",
        "addiction",
        "Normal",
        "If you don't seem weird, you're living badly.",
        "if people don't think you're weird, you're living badly.",
    ),
    (
        "nerds",
        "nerds",
        "Popularity",
        "They want to be smart more than popular.",
        "They want to be popular, certainly, but they want even more to be smart.",
    ),
    (
        "nerds",
        "fn",
        "Fierce",
        "Fierce nerds are intelligent.",
        "Another quality you find in most fierce nerds is intelligence.",
    ),
    (
        "nerds",
        "noob",
        "Learning",
        "A noob feeling means you're doing something new.",
        "there are two sources of feeling like a noob: being stupid, and doing something novel.",
    ),
    (
        "nerds",
        "noob",
        "Learning",
        "Feeling like a noob is a good sign.",
        "the more you feel like a noob, the better.",
    ),
    (
        "scale",
        "ds",
        "Users",
        "Set them up on the spot.",
        "When anyone agreed to try Stripe they'd say \"Right then, give me your laptop\" and set them up on the spot.",
    ),
    (
        "scale",
        "ds",
        "Users",
        "Don't email a link. Install it.",
        "More diffident founders ask \"Will you try our beta?\" and if the answer is yes, they say \"Great, we'll send you a link.\"",
    ),
    (
        "scale",
        "superlinear",
        "Unscalable",
        "Do things that don't scale, then they do.",
        "In the startup world, the name for this principle is \"do things that don't scale.\"",
    ),
]

CHAPTER_KEYWORDS = {
    "start": (
        "start a startup", "starting a startup", "just start",
        "why to start", "before the startup", "how to start",
        "starting startups", "how not to die",
    ),
    "want": (
        "startup idea", "startup ideas",
        "live in the future", "something people want",
        "problems you have", "organic startup",
        "make something someone", "make something people",
        "people actually want", "users actually want",
    ),
    "scale": (
        "don't scale", "doesn't scale", "do things that don't",
        "recruit users", "unscalable", "recruit users manually",
        "handholding", "manually",
    ),
    "growth": (
        "growth rate", "default alive", "default dead",
        "grow fast", "designed to grow", "ramen profitable",
        "the only essential", "startup = growth",
    ),
    "fundraising": (
        "fundraising", "raise money", "raising money",
        "convertible note", "convince investors", "venture capital",
        "investor herd", "angel investor", "investors", "investor",
        "get acquired",
    ),
    "schlep": (
        "schlep", "unglamorous", "launch fast",
        "version 1 out", "schlep blindness",
    ),
    "founders": (
        "relentlessly resourceful", "founder mode",
        "good cofounder", "cofounder", "determination",
        "earnest", "formidable", "hapless", "founder control",
        "the right kind of stubborn", "founders", "founder",
    ),
    "maker": (
        "maker's schedule", "manager's schedule",
        "meetings are a disaster", "a single meeting",
        "top idea in your mind", "fake work", "good procrastination",
        "meetings are", "meetings",
    ),
    "great-work": (
        "great work", "do what you love", "what to work on",
        "work hard", "project of your own", "doesn't seem like work",
        "early work", "superlinear",
    ),
    "taste": (
        "good taste", "good design", "good art", "copy what you like",
    ),
    "writing": (
        "write simply", "good writing", "writing is thinking",
        "write well", "an essay", "ordinary words", "write-nots",
        "ideas into words", "write like you talk", "writing",
    ),
    "ideas": (
        "new ideas", "good ideas", "notice anomalies",
        "crazy new ideas", "general and surprising",
        "think for yourself",
    ),
    "identity": (
        "identity small", "keep your identity", "labels you have",
        "what you can't say", "moral fashion", "being mean",
        "orthodox privilege",
    ),
    "wealth": (
        "make wealth", "create wealth", "get rich",
        "how people get rich", "compress your whole working",
    ),
    "cities": (
        "startup hub", "great cities", "you should be smarter",
        "silicon valley", "ambitious people", "startup hubs",
    ),
    "young": (
        "when you're young", "wish you'd known", "what you like",
        "life is short", "lesson to unlearn", "don't be a cog",
        "in high school",
    ),
    "nerds": (
        "nerds are", "fierce nerds", "being a nerd",
        "why nerds", "being a noob", "nerds", "nerd",
    ),
}

TWEET_KEYWORDS = CHAPTER_KEYWORDS

SLUG_CHAPTER = {
    "start": "start", "before": "start", "notnot": "start", "ycstart": "start",
    "badeconomy": "start", "mit": "start", "really": "start", "die": "start",
    "ycombinator": "start", "whyyc": "start", "webstartups": "start",
    "startupideas": "want", "organic": "want", "users": "want", "want": "want",
    "ambitious": "want", "bronze": "want", "airbnb": "want", "good": "want",
    "ds": "scale",
    "growth": "growth", "aord": "growth", "ramenprofitable": "growth",
    "pinch": "growth",
    "fundraising": "fundraising", "hiresfund": "fundraising", "fr": "fundraising",
    "startupfunding": "fundraising", "convince": "fundraising",
    "investors": "fundraising", "guidetoinvestors": "fundraising",
    "herd": "fundraising", "angelinvesting": "fundraising",
    "venturecapital": "fundraising", "superangels": "fundraising",
    "invtrend": "fundraising", "equity": "fundraising", "corpdev": "fundraising",
    "schlep": "schlep", "13sentences": "schlep",
    "startuplessons": "schlep", "startupmistakes": "schlep",
    "founders": "founders", "relres": "founders", "foundermode": "founders",
    "determination": "founders", "persistence": "founders", "word": "founders",
    "earnest": "founders", "5founders": "founders", "foundersatwork": "founders",
    "control": "founders", "safe": "founders",
    "makersschedule": "maker", "top": "maker", "procrastination": "maker",
    "distraction": "maker", "head": "maker", "selfindulgence": "maker",
    "greatwork": "great-work", "love": "great-work", "when": "great-work",
    "own": "great-work", "genius": "great-work", "superlinear": "great-work",
    "work": "great-work", "early": "great-work", "hwh": "great-work",
    "gh": "great-work", "todo": "great-work",
    "taste": "taste", "goodtaste": "taste", "goodart": "taste",
    "copy": "taste", "desres": "taste",
    "simply": "writing", "useful": "writing", "writes": "writing",
    "goodwriting": "writing", "essay": "writing", "best": "writing",
    "talk": "writing", "speak": "writing", "writing44": "writing",
    "words": "writing", "read": "writing",
    "getideas": "ideas", "ideas": "ideas", "newideas": "ideas",
    "sun": "ideas", "discover": "ideas", "smart": "ideas", "think": "ideas",
    "identity": "identity", "say": "identity", "conformism": "identity",
    "orth": "identity", "heresy": "identity", "mean": "identity",
    "disagree": "identity",
    "wealth": "wealth", "richnow": "wealth", "earn": "wealth",
    "gap": "wealth", "ace": "wealth",
    "cities": "cities", "hubs": "cities", "startuphubs": "cities",
    "siliconvalley": "cities", "america": "cities", "pgh": "cities",
    "maybe": "cities", "seesv": "cities",
    "hs": "young", "college": "young", "do": "young", "lesson": "young",
    "vb": "young", "addiction": "young",
    "nerds": "nerds", "fn": "nerds", "noob": "nerds", "gba": "nerds",
}

SKIP_ESSAY_SLUGS = frozenset({
    "spam", "better", "ffb", "softwarepatents", "rootsoflisp", "iflisp",
    "lwba", "progbot", "noop", "weird", "fix", "diff", "hundred",
    "javacover", "pypar", "polls", "prop62", "real", "nft", "tablets",
    "segway", "twitter", "langdes", "popular", "lies",
})

ESSAY_CAP = 22
TWEET_CAP = 12

MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}

SKIP_TWEET = re.compile(
    r"(?i)("
    r"just posted|new essay|someone asked|office hours|"
    r"yc (is now|batch|cycle|alumni|interview)|"
    r"my son|my kids|\d+ yo|took \d|"
    r"thanks @|walking |ran into|"
    r"#|covid|yahoo|republicans|legalizing|venue|"
    r"i'm trying|i read recently|i hope |i love |"
    r"wow,|email from|in the uk|"
    r"does anyone|anyone know|anyone still|"
    r"finished the first|last night|hacker news|"
    r"winter \d{4}|summer \d{4}|we.re going to|"
    r"released better|voting ring|gmail|aga while|"
    r"woke movies|ron conway|infrared|fighter planes"
    r")"
)

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
MONTH_PREFIX = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{4}\s+"
)
PAREN_PREFIX = re.compile(r"^\([^)]{0,160}\)\s+")
FOOTNOTE = re.compile(r"\[\d+\]")
SKIP_SENT = re.compile(
    r"(?i)("
    r"want to start a startup\?|if you liked this|japanese translation|"
    r"translated into|click here|this essay|in this essay|"
    r"y combinator\.\s+(january|february|march|april|may|june|july|"
    r"august|september|october|november|december)|"
    r"^notes?\b|thanks to |last night|yesterday|a couple days ago|"
    r"just posted|figure \d|table \d|don't click|this site isn't|"
    r"\bdh\d|check your privilege|are you with us|as often as you see|"
    r"literally a prison|torture is amusing|cubist trick|"
    r"declare the type|bottom-up programming|scotty|you're kirk|"
    r"don't fix windows|good pitcher|would, if you're|"
    r"narrowness of the well|solve \(b\)|pointy-haired|"
    r"blameless life|spoil your house|bought instagram|"
    r"ad what most people would agree was absurdum"
    r")"
)
GOLD_SHAPE = re.compile(
    r"(?i)("
    r"^the way to |"
    r"^don't |"
    r"^never |"
    r"^always |"
    r"^it's (better|easier|harder|a mistake|possible|rare) |"
    r"^better to |"
    r"^a startup is |"
    r"^startups (are|have|take|need|die|don't) |"
    r"^you (can't|can|have to|need to|don't|should|make|won't) |"
    r"^the (best|only|hardest|most|reason|mistake) |"
    r"^live in the future|"
    r"^make something |"
    r"^keep your |"
    r"^do (what|things) |"
    r"^good (procrastination|taste|writing|design) is "
    r")"
)
GENERAL = re.compile(
    r"(?i)\b("
    r"startup|startups|founder|founders|idea|ideas|user|users|"
    r"investor|investors|growth|work|writing|essay|taste|"
    r"wealth|rich|city|cities|nerd|nerds|identity|schlep|"
    r"meeting|meetings|ambition|you|your|don't"
    r")\b"
)
CONTRAST = re.compile(
    r"(?i)\b(but |instead|rather than|the mistake|the problem is|the reason)\b"
)
MOTTO = re.compile(r'"([^"]{18,120})"')


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def essay_date(body: str) -> str:
    m = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
        body[:300],
    )
    if not m:
        return ""
    return f"{m.group(2)}-{MONTHS[m.group(1).lower()]}"


def month_label(iso: str | None) -> str:
    return (iso or "")[:7]


def tweet_is_lesson(text: str) -> bool:
    t = html.unescape(text).strip()
    if not (40 <= len(t) <= 240):
        return False
    if re.search(r"https?://|t\.co/|www\.|@", t):
        return False
    if SKIP_TWEET.search(t):
        return False
    if t.startswith(("And ", "But ", "So ", "Which ", "Plus ")):
        return False
    if not re.search(r"[.!?]$", t):
        return False
    if t.count("I ") + t.count("I'm ") > 1:
        return False
    if not GENERAL.search(t):
        return False
    return bool(GOLD_SHAPE.search(t) or CONTRAST.search(t) or re.search(r"(?i)\b(you|your|don't)\b", t))


def best_chapter(text: str) -> str | None:
    low = text.lower()
    hits = []
    for cid, keys in CHAPTER_KEYWORDS.items():
        score = sum(len(k) for k in keys if k in low)
        if score:
            hits.append((score, cid))
    if not hits:
        return None
    hits.sort(reverse=True)
    return hits[0][1]


SENTENCE_STARTERS = frozenset({
    "A", "An", "Always", "Better", "Do", "Don't", "For", "Good", "If",
    "In", "It", "It's", "Keep", "Live", "Make", "Never", "Once", "Startups",
    "The", "There", "They", "To", "We", "When", "You", "You'll", "You're",
    "You've",
})


def clean_sentence(text: str) -> str:
    s = html.unescape(norm(text))
    s = MONTH_PREFIX.sub("", s)
    s = PAREN_PREFIX.sub("", s)
    s = FOOTNOTE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    heading = re.match(r"^([A-Z][A-Za-z']{1,20}) ([A-Z].*)$", s)
    if heading and heading.group(1) not in SENTENCE_STARTERS:
        s = heading.group(2)
    return s


def make_title(text: str) -> str:
    first = SENT_SPLIT.split(text, maxsplit=1)[0].strip()
    if len(first) <= 72:
        return first
    cut = first[:69].rsplit(" ", 1)[0]
    return cut + "…"


LABELS: dict[str, dict] = {}


def infer_topic(chapter: str, text: str, fallback: str = "") -> str:
    return labeled_topic(LABELS, chapter, text, fallback)


def essay_is_nugget(s: str) -> bool:
    if not (48 <= len(s) <= 210):
        return False
    if not re.search(r"[.!?]$", s):
        return False
    if not s[0].isupper():
        return False
    if s.startswith((
        "And ", "But ", "So ", "Which ", "Plus ", "Or ", "Nor ", "Yet ",
        "Because ", "That ", "That's ", "This ", "These ", "Those ",
        "Then ", "There ", "I ", "I've ", "I'd ", "When I ",
    )):
        return False
    if re.search(r"https?://|www\.|@\w", s):
        return False
    if s.count(",") > 3:
        return False
    if s.count("(") != s.count(")"):
        return False
    if SKIP_SENT.search(s):
        return False
    if s.count(" I ") + s.count(" I'm ") + s.count(" I've ") > 1:
        return False
    if not GENERAL.search(s):
        return False
    if GOLD_SHAPE.search(s):
        return True
    if CONTRAST.search(s) and 55 <= len(s) <= 170 and re.search(r"(?i)\b(you|your|don't)\b", s):
        return True
    return False


def nugget_score(s: str) -> int:
    pts = 0
    if GOLD_SHAPE.search(s):
        pts += 4
    if CONTRAST.search(s):
        pts += 2
    if re.search(r"(?i)\b(you|your|don't)\b", s):
        pts += 2
    if 55 <= len(s) <= 170:
        pts += 2
    elif 42 <= len(s) <= 200:
        pts += 1
    caps = sum(1 for w in s.split() if w[:1].isupper())
    if caps > 5:
        pts -= 2
    return pts


def assign_chapter(text: str, slug: str) -> str | None:
    keyed = best_chapter(text)
    preferred = SLUG_CHAPTER.get(slug)
    if keyed:
        low = text.lower()
        strength = sum(len(k) for k in CHAPTER_KEYWORDS[keyed] if k in low)
        if strength >= 12:
            return keyed
        if preferred:
            return preferred
        return keyed
    if preferred and nugget_score(text) >= 6:
        if preferred == "nerds" and not re.search(
            r"(?i)\b(nerd|nerds|fierce|noob|unpopular|smart)\b", text
        ):
            return None
        return preferred
    return None


def essay_candidates(essay: dict, min_score: int = 7) -> list[tuple[int, str]]:
    slug = essay["slug"]
    if slug in SKIP_ESSAY_SLUGS:
        return []
    body = clean_sentence(essay.get("body") or "")
    out: list[tuple[int, str]] = []
    seen: set[str] = set()
    for raw in SENT_SPLIT.split(body):
        s = clean_sentence(raw)
        if not essay_is_nugget(s):
            continue
        if nugget_score(s) < min_score:
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append((nugget_score(s), s))
    for m in MOTTO.finditer(body):
        motto = clean_sentence(m.group(1))
        if not motto.endswith((".", "!", "?")):
            motto += "."
        if not GOLD_SHAPE.search(motto):
            continue
        if not essay_is_nugget(motto):
            continue
        key = motto.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append((nugget_score(motto) + 2, motto))
    return out


def cap(text: str) -> str:
    text = html.unescape(text).strip()
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


def next_sentence(body: str, excerpt: str) -> str:
    """If the excerpt is a short label, pull the sentence after it."""
    if len(excerpt) >= 40 and excerpt.endswith((".", "!", "?")):
        return excerpt
    blob = norm(body)
    idx = blob.lower().find(norm(excerpt).lower())
    if idx < 0:
        return excerpt
    rest = blob[idx + len(excerpt) :].lstrip()
    nxt = re.split(r"(?<=[.!?])\s+", rest, maxsplit=1)[0].strip()
    if 24 <= len(nxt) <= 180 and nxt[:1].isupper() and not nxt.startswith("("):
        joined = f"{excerpt} {nxt}" if excerpt.endswith((".", "!", "?")) else f"{excerpt.rstrip('.')} {nxt}"
        if len(joined) <= 220:
            return joined
    return excerpt


def quote(
    *,
    topic: str,
    title: str,
    excerpt: str,
    source: str,
    href: str,
    kind: str,
    date: str,
) -> dict:
    excerpt = cap(excerpt)
    title = cap(title)
    return {
        "topic": topic,
        "title": title,
        "headline": excerpt,
        "source": source,
        "href": href,
        "kind": kind,
        "date": date,
    }


CHAPTER_TOPIC = {ch["id"]: ch["title"] for ch in CHAPTERS}


def main() -> None:
    global LABELS
    LABELS = load_cache()
    essays = {e["slug"]: e for e in load_jsonl(DATA / "essays.jsonl")}
    tweets = load_jsonl(DATA / "tweets.jsonl")
    buckets: dict[str, list[dict]] = defaultdict(list)
    used: set[str] = set()
    canon_keys: set[str] = set()
    missing = 0

    for chapter, slug, topic, title, excerpt in CANON:
        essay = essays.get(slug)
        if not essay:
            print(f"missing essay slug: {slug}")
            missing += 1
            continue
        if norm(excerpt).lower() not in norm(essay["body"]).lower():
            print(f"NOT IN {slug}: {excerpt[:90]}")
            missing += 1
            continue
        key = excerpt.lower()
        if key in used:
            continue
        used.add(key)
        canon_keys.add(key)
        buckets[chapter].append(
            quote(
                topic=infer_topic(chapter, excerpt, topic),
                title=title,
                excerpt=next_sentence(essay["body"], excerpt),
                source=essay["title"],
                href=essay["url"],
                kind="essay",
                date=essay_date(essay["body"]),
            )
        )

    mined_counts: dict[str, int] = defaultdict(int)
    mined: list[tuple[int, str, dict, str]] = []
    for essay in essays.values():
        for score, excerpt in essay_candidates(essay):
            dest = assign_chapter(excerpt, essay["slug"])
            if not dest:
                continue
            key = excerpt.lower()
            if key in used:
                continue
            mined.append((score, dest, essay, excerpt))
    mined.sort(reverse=True, key=lambda row: (row[0], -len(row[3])))
    for score, dest, essay, excerpt in mined:
        key = excerpt.lower()
        if key in used:
            continue
        if mined_counts[dest] >= ESSAY_CAP:
            continue
        used.add(key)
        mined_counts[dest] += 1
        buckets[dest].append(
            quote(
                topic=infer_topic(dest, excerpt),
                title=make_title(excerpt),
                excerpt=excerpt,
                source=essay["title"],
                href=essay["url"],
                kind="essay",
                date=essay_date(essay["body"]),
            )
        )

    thin = {
        ch["id"]
        for ch in CHAPTERS
        if sum(1 for q in buckets[ch["id"]] if q["kind"] == "essay") < 16
    }
    if thin:
        extra: list[tuple[int, str, dict, str]] = []
        for essay in essays.values():
            for score, excerpt in essay_candidates(essay, min_score=6):
                dest = assign_chapter(excerpt, essay["slug"])
                if dest not in thin:
                    continue
                key = excerpt.lower()
                if key in used:
                    continue
                extra.append((score, dest, essay, excerpt))
        extra.sort(reverse=True, key=lambda row: (row[0], -len(row[3])))
        for score, dest, essay, excerpt in extra:
            key = excerpt.lower()
            if key in used:
                continue
            have = sum(1 for q in buckets[dest] if q["kind"] == "essay")
            if have >= 16:
                continue
            used.add(key)
            buckets[dest].append(
                quote(
                    topic=infer_topic(dest, excerpt),
                    title=make_title(excerpt),
                    excerpt=excerpt,
                    source=essay["title"],
                    href=essay["url"],
                    kind="essay",
                    date=essay_date(essay["body"]),
                )
            )

    tweet_pool: list[tuple[int, str, dict, str]] = []
    for tweet in tweets:
        if tweet.get("type") != "original":
            continue
        text = html.unescape(tweet.get("text") or "").strip()
        if not tweet_is_lesson(text):
            continue
        dest = best_chapter(text)
        if not dest:
            continue
        key = text.lower()
        if key in used:
            continue
        tweet_pool.append((nugget_score(text), dest, tweet, text))
    tweet_pool.sort(reverse=True, key=lambda row: (row[0], -len(row[3])))
    tweet_counts: dict[str, int] = defaultdict(int)
    for score, dest, tweet, text in tweet_pool:
        key = text.lower()
        if key in used:
            continue
        if tweet_counts[dest] >= TWEET_CAP:
            continue
        used.add(key)
        tweet_counts[dest] += 1
        buckets[dest].append(
            quote(
                topic=infer_topic(dest, text),
                title=make_title(text),
                excerpt=text,
                source="@paulg",
                href=tweet.get("url") or f"https://x.com/paulg/status/{tweet['id']}",
                kind="tweet",
                date=month_label(tweet.get("created_at")),
            )
        )

    book_chapters = []
    for i, ch in enumerate(CHAPTERS, 1):
        cid = ch["id"]
        order = CHAPTER_TOPICS[cid]
        quotes = []
        for q in buckets[cid]:
            key = q["headline"].lower()
            hit = lookup(LABELS, cid, q["headline"])
            if hit and hit.get("is_lesson") is False and key not in canon_keys:
                continue
            q["topic"] = infer_topic(cid, q["headline"], q.get("topic") or "")
            quotes.append(q)
        quotes.sort(
            key=lambda q: (
                order.index(q["topic"]) if q["topic"] in order else len(order),
                0 if q["kind"] == "essay" else 1,
            )
        )
        book_chapters.append(
            {
                "num": f"{i:02d}",
                "id": cid,
                "section": ch["section"],
                "title": ch["title"],
                "quotes": quotes,
            }
        )

    nq = sum(len(c["quotes"]) for c in book_chapters)
    payload = {
        "title": "PAUL GRAHAM",
        "subtitle": "LESSONS & NOTES",
        "dek": f"{len(essays)} essays. {nq} lessons. In his own words.",
        "disclaimer": "Personal reader. Not affiliated with Paul Graham or Y Combinator.",
        "sources": ["paulgraham.com", "@paulg"],
        "chapters": book_chapters,
    }
    (OUT / "data.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    (OUT / "data.js").write_text("window.BOOK = " + json.dumps(payload, ensure_ascii=False) + ";\n")
    ne = sum(1 for c in book_chapters for q in c["quotes"] if q["kind"] == "essay")
    nt = sum(1 for c in book_chapters for q in c["quotes"] if q["kind"] == "tweet")
    print(f"Wrote {len(book_chapters)} chapters, {nq} lessons ({ne} essay, {nt} tweet), {missing} canon misses")
    for c in book_chapters:
        e = sum(1 for q in c["quotes"] if q["kind"] == "essay")
        t = sum(1 for q in c["quotes"] if q["kind"] == "tweet")
        print(f"  {c['num']} {c['id']:12} {len(c['quotes']):3}  essay={e:2} tweet={t:2}")


if __name__ == "__main__":
    main()
