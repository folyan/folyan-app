import random

CHOICES = ("rock", "scissors", "paper")
BEATS = {"rock": "scissors", "scissors": "paper", "paper": "rock"}

def check_win(player):
	bot = random.choice(CHOICES)
	if player == bot:
		return "tie"
	return "win" if BEATS[player] == bot else "lose"