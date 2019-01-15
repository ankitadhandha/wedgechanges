from ExamplePage import ExamplePage
from time import *


class ShowTime(ExamplePage):

	def writeContent(self):
		self.write('<p>', asctime(localtime(time())))
