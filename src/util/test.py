import inquirer

questions = [
      inquirer.Text('user', message='Please enter your github username', validate=lambda _, x: x != '.'),
      inquirer.Password('password', message='Please enter your password'),
      inquirer.Text('repo', message='Please enter the repo name', default='default'),
      inquirer.Checkbox('topics', message='Please define your type of project?', choices=['common', 'backend', 'frontend'], ),
      inquirer.Text('organization', message='If this is a repo from a organization please enter the organization name, if not just leave this blank'),
      inquirer.Confirm('correct',  message='This will delete all your current labels and create a new ones. Continue?', default=False),
]

answers = inquirer.prompt(questions)

# Ask again, using previous values as defaults

answers = inquirer.prompt(questions, answers=answers)
print(answers)
# 
# import inquirer
# questions = [
#   inquirer.List('size',
#                 message="What size do you need?",
#                 choices=['Jumbo', 'Large', 'Standard', 'Medium', 'Small', 'Micro'],
#             ),
# ]
# answers = inquirer.prompt(questions)

# # import os
# # import sys
# # import re

# # import inquirer

# # questions = [
# #     inquirer.List('size',
# #                   message="What size do you need?",
# #                   choices=['Jumbo', 'Large', 'Standard', 'Medium', 'Small', 'Micro'],
# #               ),
# # ]

# # answers = inquirer.prompt(questions)

# # print(answers)


# import inquirer
# questions = [
#   inquirer.Text('name', message="What's your name"),
#   inquirer.Text('surname', message="What's your surname"),
#   inquirer.Text('phone', message="What's your phone number")
# ]
# answers = inquirer.prompt(questions)
# print(answers)




# questions = [
#   inquirer.List('size',
#                 message="What size do you need?",
#                 choices=['Jumbo', 'Large', 'Standard', 'Medium', 'Small', 'Micro'],
#             ),
# ]
# answers = inquirer.prompt(questions)