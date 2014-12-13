#from threading import Thread
from time import gmtime, strftime
import threading
import thread
import PedantStandartHandlers
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os,sys,json,hashlib,Image,ImageChops,ImageDraw,time,uuid,urllib2,shutil

class Worker(threading.Thread):


	def initStop(self):
		self.stop = True

	def __init__(self, browser, items, timestamp, data_storage_root ):
		self.log_str = ''
		self.handler = False
		self.finished_ids = {}
		self.handled = False
		self.stop = False
		
		super(Worker, self).__init__()
		#browser dict may be using in another worker, need copy
		self.browser = browser.copy()
		self.items = list(items)
		self.timestamp = str(timestamp)
		self.root = data_storage_root
		self.pathes = self.calculatePathes()
		self.createFolders()

	def log( self, line = False, level="INFO"):
		if (line):
			self.log_str += strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' [' + level + '] ' + line + "\n"
		else:
			log = self.log_str
			self.log_str = ''
			return log

	"""
	init browser
	"""
	def initBrowser(self):
		#launch browser
		if ( self.browser.has_key( 'wd_url' ) ):
			#caps
			caps = getattr( DesiredCapabilities , self.browser['type'].upper() )
			if self.browser.has_key('desired_capabilities'):
				caps = dict( caps.items() + self.browser['desired_capabilities'].items() )
			#print caps
			try:
				self.browser['instance'] = webdriver.Remote(
						command_executor=str(self.browser['wd_url']),
						desired_capabilities=caps,
						keep_alive=False )
				self.log( "Connected to browser: " + str( self.browser ) )
			except:
				self.log( "Can not connect to browser: " + str( self.browser ) , "ERROR" )
				print "\n >>> Can not connect to browser: " + str( self.browser ) 
				thread.exit()
		else:
			print "\n >>> Browser without wd_url in thread: " + str(self.browser)
			self.log( "Browser without wd_url in thread" , "ERROR" )
			thread.exit()

		self.browser['instance'].set_window_size( self.browser['window_size'][0],self.browser['window_size'][1] )

	"""
	init handler instance
	"""
	def initHandler(self):
		sys.path.insert(0, os.path.dirname(__file__))
		import PedantStandartHandlers
		try:
			sys.path.insert(0, os.getcwd())
			import PedantHandlers
			self.log( "Handler founded in cwd" )
			self.handler = PedantHandlers.PedantHandlers( self.browser )
			self.log( "Handler init success" )
		except:
			self.handler = PedantStandartHandlers.PedantStandartHandlers( self.browser )

	"""
	run this
	@return void
	"""
	def run(self):
		#start browser
		self.initBrowser()
		self.initHandler()
		for item in self.items:
			if ( self.stop ):
				self.log( "Skipping url " + item['url'] )
				continue
			self.log( "Files for left (for current worker): " + str( ( len(self.items) - len(self.finished_ids) ) ) )
			self.log( "Start checking for url " + item['url'] )
			start_time = time.time()
			self.browser['instance'].get( item['url'] )
			item['load_time'] = round( time.time() - start_time , 2)
			#handler before screen
			self.handler.before_screenshot( item, self.browser )
			#print "Handler <before_screenshot> error with item <" +item['unid']+ ">"
			self.browser['instance'].save_screenshot( self.pathes[ item['unid'] ]['abs']['actual_report_path'] )
			try:
				self.screen_processing( item )
			except:
				print "Item <" + item['unid'] + "> error:", sys.exc_info()[0]
				self.log( "Error while screen processing for resource" + item['url'] )
			self.finished_ids[ item['unid']+self.browser['unid'] ] = True
			self.log( "Finished checking for url " + item['url'] )
		self.browser['instance'].close()
		self.handled = True
		self.log( "Disconnect from selenium browser with unid " + self.browser['unid'] )
		return

	"""
	This function calculate pathes
	@return void
	"""
	def calculatePathes(self):
		# iterate items and calculate pathes
		pathes = {}
		for item in self.items:
			path_suffix = item['unid'] + os.sep + self.browser['unid'] + os.sep
			pathes[ item['unid'] ] = {
				'abs': {
					'approved_dir': self.root + os.sep + 'approved' + os.sep + path_suffix,
					'report_dir': self.root + os.sep + 'reports' + os.sep + self.timestamp + os.sep + path_suffix,
					'approved_path': self.root + os.sep + 'approved' + os.sep + path_suffix + 'approved.png',
					'actual_report_path': self.root + os.sep + 'reports' + os.sep + self.timestamp + os.sep + path_suffix + 'actual.png',
					'approved_report_path': self.root + os.sep + 'reports' + os.sep + self.timestamp + os.sep + path_suffix + 'approved_report.png',
					'diff_report_path': self.root + os.sep + 'reports' + os.sep + self.timestamp + os.sep + path_suffix + 'diff.png', 
				}
			}
		return pathes

	"""
	This function create folders for items
	return void
	"""
	def createFolders(self):
		for item_unid,item_dict in self.pathes.iteritems():
			if ( os.path.isdir( item_dict['abs']['report_dir'] ) == False ):
				os.makedirs( item_dict['abs']['report_dir'] , 0777 )

	"""
	This function do work with taked screenshot
	@param item - dict with info about scanning item
	@param screenshot - png in string. Taked screenshot 
	"""
	def screen_processing(self, item ):
		#check actual screenshot
		if os.path.isfile( self.pathes[ item['unid'] ]['abs']['actual_report_path'] ):
			#try find approve screenshot
			if os.path.isfile( self.pathes[ item['unid'] ]['abs']['approved_path'] ):

				#if find - call compare screesnhots and copy approved to report folder
				compare_res = self.compare_screenshots(
					self.pathes[ item['unid'] ]['abs']['approved_path'],
					self.pathes[ item['unid'] ]['abs']['actual_report_path'],
					self.pathes[ item['unid'] ]['abs']['diff_report_path']
					)

				shutil.copyfile( self.pathes[ item['unid'] ]['abs']['approved_path'], self.pathes[ item['unid'] ]['abs']['approved_report_path'] )
				## if has diff - report error
				if ( compare_res ):
					self.save_result( "diff" , item )
				## else - report success
				else:
					self.save_result( "success", item )
			#have not approved
			else:
				self.save_result( "approve404", item )
		else:
			self.log( "Screenshot saving error. Path: " + actual_path , "ERROR" )
			print "\n >>> ERROR: Can not save actual screenshot in: " + actual_path + "\n"
			return True

	def save_result(self,msg,item):
		#print "save result for file \n" 
		obj = open( self.pathes[item['unid']]['abs']['report_dir'] + os.sep + 'report.json' , 'wb')
		self.log( "Save report for item: " + item['url'] )
		bro = self.browser.copy()
		del bro['instance']
		json.dump( {
				'item' : item,
				'browser' : bro,
				'window_size': self.browser['window_size'],
				'msg' : msg,
				}, 
				obj)
		obj.close

	"""
	This function compare two images and save difference in diff_path
	@param approved_path string - path to approved image
	@param actual_path string - path to actual image
	@param diff_path string - path to save difference image
	@return bool - True if images has a difference, and false if images the same
	"""
	def compare_screenshots(self,approved_path, actual_path, diff_path ):
		#
		dataA = open(approved_path, 'rb').read()
		dataB = open(actual_path, 'rb').read()

		if hashlib.md5(dataA).hexdigest() != hashlib.md5(dataB).hexdigest():
			#make one size
			# ToDo 
			imageA = Image.open(approved_path)
			imageB = Image.open(actual_path)
			#if sizes not match - resize smalled
			if ( imageA.size != imageB.size ):
				#get max image size
				w_size = max( [ imageA.size[0] , imageB.size[0] ] )
				h_size = max( [ imageA.size[1] , imageB.size[1] ] )
				#make new size image
				imageA = imageA.transform( ( w_size , h_size ), Image.EXTENT , [0,0,w_size,h_size] )
				imageB = imageB.transform( ( w_size , h_size ), Image.EXTENT , [0,0,w_size,h_size] )

			#calculate dirty diff
			diff = ImageChops.difference(imageA, imageB).convert("RGB")
			#generate pretty diff image 
			background = Image.new('RGBA', imageA.size, (200, 200, 200, 100))
			mask = Image.new('L', imageB.size, 0xC0)
			imageA.paste(background, (0,0) , mask)
			imageA = imageA.convert("RGBA")
			diffArray = list(diff.getdata())
			# create pretty diff image
			prettyDiffArray = [ (255,0,0,180) if diffArray[key] != (0,0,0) else x for key,x in enumerate(imageA.getdata())]
			#make diff from imageA
			imageA.putdata( prettyDiffArray )
			#save diff
			imageA = imageA.convert("RGB")
			imageA.save( diff_path , "PNG" )
			return True

		return False