def str_times(time):
	"""
	Given a time in seconds. Return a string "Ww Dd Hh Mm". Where W/D/H/M are gerater than 0
	"""

	days_per_week = 5
	hours_per_day = 8

	weeks = time // (days_per_week * hours_per_day * 60 * 60)
	days = (time // (hours_per_day * 60 * 60)) % days_per_week
	hours = (time // (60 * 60)) % hours_per_day
	minutes = (time // 60) % 60

	lst = []
	syms = ['w', 'd', 'h', 'm']

	for i, x in enumerate([weeks, days, hours, minutes]):
		if x > 0:
			lst.append(str(x) + syms[i] )

	lst2 = [str(x) + syms[i] for i, x in enumerate([weeks, days, hours, minutes]) if x > 0]

	print(" ".join(lst))
	print(" ".join(lst2))
	
str_times(60 * 100)
str_times(61)
str_times(60 * 60 * 120 + 120)
str_times(0)
