# import os
# import sys
# import re

# import inquirer

# questions = [
#     inquirer.List('size',
#                   message="What size do you need?",
#                   choices=['Jumbo', 'Large', 'Standard', 'Medium', 'Small', 'Micro'],
#               ),
# ]

# answers = inquirer.prompt(questions)

# print(answers)


import inquirer
questions = [
  inquirer.Text('name', message="What's your name"),
  inquirer.Text('surname', message="What's your surname"),
  inquirer.Text('phone', message="What's your phone number")
]
answers = inquirer.prompt(questions)
print(answers)




questions = [
  inquirer.List('size',
                message="What size do you need?",
                choices=['Jumbo', 'Large', 'Standard', 'Medium', 'Small', 'Micro'],
            ),
]
answers = inquirer.prompt(questions)