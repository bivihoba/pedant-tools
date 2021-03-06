from PedantStandartHooks import PedantHooks
from PedantStandartHooks import hook

class Hooks(PedantHooks):

	"""
	PARENT VARS
	self.browser - dict of current browser. self.browser['instance'] - current webdriver instance.

	PARENT FUNCTIONS
	self.log( "log message", level='INFO' ) - write something to pedant log with level 'INFO'
	self.log( "log message", level='WARN' ) - write something to pedant log with level 'WARN'
	self.log( "log message", level='BLABLABLA' ) - write something to pedant running log with level 'BLABLABLA'
	self.wait_js( "return document.readyState != 'complete'", 5000 ) - wait js condition 5000 miliseconds

	HOOKS
	@hook( 'before_items' ) - run before start items iterating. If you raise exception - pedant skip all items and mark report as failed
	@hook( 'before_item' ) - run before url opening in browser. If you raise exception - pedant skip current item
	@hook( 'before_screenshot' ) - run after url opening in browser and before screenshot capture. If you raise exception - pedant skip current item
	@hook( 'after_item' ) - run after screenshot checking and before report save. If you raise exception - pedant do nothind
	@hook( 'after_items' ) - run after all items iterate. If you raise exception - pedant do nothing
	"""


	@hook( 'before_items' )
	def log_my_items( self, items ):
		self.log( "Before all items hook" )
		#self.browser['instance'].implicitly_wait(1)# set implicitly_wait for current browser
		pass


	@hook( 'before_item' )
	def before_item(self, item ):
		#self.wait_js( "return document.readyState != 'complete'", 5000 )
		self.log( 'Log message before item ' + item['unid'] )
		pass


	@hook( 'before_screenshot' )
	def my_method( self, item ):
		self.log( "Before screenshot hook" )
		#element = self.browser['instance'].find_element_by_class_name('input__control')
		pass


	@hook( 'after_item' )
	def after_item( self, item, result ):
		self.log( "After item hook" )
		pass


	@hook( 'after_items' )
	def after_items( self, items ):
		self.log( "After all items hook" )
		#print "after all items:", items
		pass