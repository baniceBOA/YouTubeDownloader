''' YouTube downoader application'''
import ssl 
ssl._create_default_https_context = ssl._create_unverified_context
import traceback
from asyncio import Queue
from pytube import YouTube
from pytube import request
import os 
import threading
import concurrent.futures
from collections import deque
import datetime
from plyer import filechooser, notification
#from plyer.platforms.win.filechooser import WinFileChooser as filechooser
#from plyer.platforms.win.notification import  WindowsNotification as notification

from kivymd.app import App, MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRoundFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.progressbar import MDProgressBar
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import RoundedRectangularElevationBehavior
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelOneLine
from kivymd.uix.card import MDCard
from kivymd.utils.fitimage import FitImage
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.toolbar import MDTopAppBar
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy.utils import platform

if platform == 'android':
	from android.permissions import request_permissions, Permission
	request_permissions([Permission.WRITE_EXTERNAL_STORAGE,Permission.READ_EXTERNAL_STORAGE, Permission.ACCESS_NOTIFICATION_POLICY,Permission.LOCATION_HARDWARE])

from all_file_download import download as image_download
from db import insertvalue, create_connection, select_all

icon_file = 'youtube.ico'


database = 'youtube_db.db'
system_root = '.'
app_root = os.getcwd()
if platform == 'android':
	icon_file = 'youtube.png'
	from android.permissions import request_permissions, Permission
	request_permissions([Permission.WRITE_EXTERNAL_STORAGE,Permission.READ_EXTERNAL_STORAGE, Permission.ACCESS_NOTIFICATION_POLICY,Permission.LOCATION_HARDWARE])
	from plyer import storagepath
	app_root = storagepath.get_downloads_dir()
	database = os.path.join(app_root, 'youtube_db.db')


error_file = os.path.join(app_root, 'error.log')
conn = create_connection(database)

kv = (
'''
#:import get_color_from_hex kivy.utils.get_color_from_hex
<DownLoader>:

<Downloads>:

<SettingsApp>:


MDBoxLayout:
	orientation:'vertical'
	MDTopAppBar:
        title: app.title
        md_bg_color: [1,0,0,0.7]
        pos_hint:{'top':1}


    MDBottomNavigation:
        id:sm
        md_bg_color: app.theme_cls.bg_light
        color_normal: app.theme_cls.opposite_bg_darkest
        color_active: [1,0,0,0.7]

        MDBottomNavigationItem:
        	id: video
        	name:'video'
            icon: "video"
            text: "video"
            on_tab_press:app.change_screen(video)
            DownLoader:
            

        MDBottomNavigationItem:
        	id:download
            icon: "download"
            text: "downloads"
            name:'downloads'
            on_tab_press:app.change_screen(download)
            Downloads:
            	id:download_db
            

        MDBottomNavigationItem:
        	id:setting
            icon: "application-settings"
            text: "settings"
            name:'settings'
            on_tab_press:app.change_screen(setting)
            SettingsApp:
                
          

''')

class DownLoader(MDFloatLayout, ThemableBehavior):
	''' Provides the interfaces to download the images '''
	link = StringProperty()
	value = NumericProperty()
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.theme_cls.primary_palette = 'Red'
		self.link_input = MDTextField(size_hint_x=None,
									hint_text='Paste Link here',
									width=Window.size[0]*0.75, 
									mode='rectangle',
									padding = '8sp',
									radius=[12,12,50,50])

		self.set_path = MDLabel(size_hint_x=None,
								size_hint_y=None,
								height = Window.size[1]*0.05,
								text=f'path {app_root}',
								valign='center' ,
								width=Window.size[0]*0.75)
		self.padding = 10
		#give the text field a position
		self.link_input.pos_hint = {'top':1 }
		self.set_path.pos_hint = {'top':0.89 }


		#provides a widget for the downloading files 
		self.label = MDLabel(text='Downloading ', halign='center',  size_hint_y=None, height=dp(25))
		self.download_content = MDList()
		self.download_content.pos_hint = {'center_x':0.5}

		self.download_content.add_widget(self.label)

		#scroll the download content
		self.scroller_download = ScrollView()
		self.scroller_download.pos_hint = {'top':0.81, 'center_x':0.5}
		self.scroller_download.add_widget(self.download_content)

		#The download button
		self.download_btn = MDRoundFlatButton(text='Download')
		self.download_btn.bind(on_release=self.get_streams)
		self.download_btn.pos_hint = {'top':0.98, 'center_x':0.9}

		#the Browse button used for selecting path to save the file
		self.browse_path_btn = MDRoundFlatButton(text='Browse')
		self.browse_path_btn.pos_hint = {'top':0.88, 'center_x':0.9}
		self.browse_path_btn.bind(on_release=self.select_file_path)

		#filemanager
		self.filemanager = FileManager()
		self.download_cancelled = False

		# The Spinner
		self._processing = Processing()


		#Add the widget to the main classes
		self.add_widget(self.browse_path_btn)
		self.add_widget(self.set_path)
		self.add_widget(self.download_btn)
		self.add_widget(self.link_input)
		self.add_widget(self.scroller_download)
		Window.bind(on_resize=self.update_size)

	def update_size(self, *args):
		''' update the sizes on window size chaning '''
		self.link_input.width = Window.size[0]*0.75	
		self.set_path.width = Window.size[0]*0.75
		

	def get_streams(self, touch):
		''' it process the link'''
		url = self.link_input.text
		path = self.set_path.text
		if 'youtube' or 'youtu.be' in self.link_input.text.lower() and self.link_input.text.startswith('http'):
			if self._processing not  in self.children[:]:
				self.add_widget(self._processing)
			threading.Thread(target=self.processing, args=()).start()
		elif not self.link_input.text:
			self.show_error('paste a link ')
		else:
			if self.link_input.text.startswith('http'):
				filename = url.split('/')[-1][:-4]
				self.download_label = DownloadLabel(text=filename, 
												source='', path=app_root)
				self.download_content.add_widget(self.download_label)
				notification.notify(title='Downloading',app_name='YouTubeDownloader', app_icon=r'youtube.png',ticker=f'{filename} is Downloading', message=f'{filename} is Downloading')
				threading.Thread(target=image_download, 
								 kwargs={'url':url, 
								 		 'filename':filename,
								 		 'path':path if self.set_path.text else app_root,
										 'progress_callback':self.progress, 
										 'complete_callback':self.complete}).start()
		
	




	@mainthread
	def show_error(self, error, title='Error'):
		''' Display the error that has been encounter '''
		if self._processing in self.children[:]:
			self.remove_widget(self._processing)
		dialog_btn = MDFlatButton(
								text='CANCEL',
								theme_text_color="Custom",
								text_color=[0.0876272632, 0.077627263, 0.76263723, 1])
		self.download_error = MDDialog(title=f'[color=ff3333]{title}[/color]', text=f'[color=ff3333]{error}[/color]', buttons=[dialog_btn])
		dialog_btn.bind(on_release=self.close_error)
		self.download_error.open()
	def close_error(self, touch):
		self.download_error.dismiss()
	def processing(self):
		''' get the resolutions available for the video'''
		import time
		resolution = ['1080p','720p','480p','360p','240p']
		tag = [96, 95, 83, 93, 92]
		if 'm.youtube' in self.link_input.text:
		 	self.clean_link()
		try:
			self.yt = YouTube(self.link_input.text)	
		except Exception as e:
			self.show_error('An Error occured while downloading check your url link', title='Fetching Error')
			return None
		self.res_dict = {}
		end = len(resolution)-1
		start = 0
		for t, res in zip(tag, resolution):

			try:
				stream = self.yt.streams.get_by_resolution(res)
			except Exception as e:
				self.show_error(e,title='Resolution')
				traceback.print_exc(file=error_file)
				return None
			self.check_progress(start, end=end)
			if stream:
				self.res_dict[res] =  stream
			start += 1
		self.update_window()

	@mainthread
	def clean_link(self):
		link = self.link_input.text.replace('m.youtube','youtube')
		self.link_input.text = link
	@mainthread
	def check_progress(self, current, end):
		''' Check the progress of the loop '''
		if current == end and self._processing in self.children[:]:
			self.remove_widget(self._processing)
		


	@mainthread		
	def update_window(self):
		''' pop a window for the user to select the prefered quality'''
		resolution = ['2160p','1440p','1080p','720p','480p','360p','240p']
		self.res = Resolution()
		self.download_dialog = MDDialog(title='Select Download Quality', type='custom', content_cls=self.res)
		#{round(self.res_dict[res].filesize/1000000,2)}
		for res in resolution:
			if res in self.res_dict:
				self.res.add_widget(CustomBtn(text=f'{res}  filesize {round(self.res_dict[res].filesize/1000000,2)} MB',theme_text_color='Custom', text_color=[1,0.3,0,0.5], on_release=self._download))
		self.download_dialog.open()
		

	@mainthread
	def _download(self, touch):
		
		''' internal '''
		self.value = 0
		text = touch.text.split(' ')[0]
		stream = self.res_dict[text]
		path = storagepath.get_downloads_dir() if platform == 'android' else self.set_path.text
		if not path:
			path = app_root
		self.download_label = DownloadLabel(text=self.yt.title, 
											file_size=int(stream.filesize/1000000), 
											source=self.yt.thumbnail_url, path=app_root)
		self.download_paused = self.download_label.pause
		self.download_cancelled = False
		self.download_content.add_widget(self.download_label)
		touch.text_color = self.theme_cls.primary_color
		self.download_dialog.dismiss()
		toast('Download Started')
		notification.notify(title='Downloading',app_name='YouTubeDownloader', app_icon=icon_file,ticker=f'{self.yt.title} is Downloading', message=f'{self.yt.title} is Downloading')
		threading.Thread(target=image_download, kwargs={'url':stream.url,'filename':self.yt.title,'file_type':'.mp4', 'progress_callback':self.progress, 'complete_callback':self.complete, 'path':app_root}).start()
		#self.download(stream.url,self.yt.title, stream.filesize, path)
		self.yt = None
		self.link_input.text = ''
	
	def download(self, url, title, filesize, path):
		''' downloads the files '''

		downloaded = 0
		bytes_remaining = 0
		try:
			title = title.replace(' ', '_')
			file_path = r"" + f"{os.path.join(path,f'{title}.mp4')}"
			with open(file_path,'wb') as f:
				stream = request.stream(url)
				while True:
					if self.download_cancelled:
						break
					if self.download_label.pause:
						continue
					chunk = next(stream, None)
					if chunk:
						f.write(chunk)
						downloaded += len(chunk)
						bytes_remaining = filesize-downloaded
						
						self.progress(filesize, bytes_remaining)
					else:
						self.complete(title, path)
						break
		except Exception as e:
			self.show_error(e, title='Download Error')
			with open(error_file, 'a') as file:
				traceback.print_exc(file=file)
			self.download_cancelled = True



		
		
	@mainthread
	def complete(self, title, path):
		''' action perfomed when the download is complete'''
		toast('Download Complete')
		self.download_label.complete = True
		self.download_label.path = os.path.join(path, f'{title}.mp4')
		
		notification.notify(title='Download Complete', app_name='YouTubeDownloader',app_icon=icon_file, message=f'{title} \n Download Complete')


	@mainthread
	def progress(self, filesize, bytes_remaining):
		''' the action perfomed while downloading is taking place '''
		
		self.value = int(100 - bytes_remaining/filesize*100)
		self.download_label.value = int(100 - bytes_remaining/filesize*100)
		self.download_label.downloaded_size = int((filesize - bytes_remaining)/1000000)
		self.download_label.file_size = int(filesize/1000000)
		self.download_paused = self.download_label.pause # check if the download is paused
		if self.download_label.pause:
			toast('Download Paused')
			return self.download_label.pause
		if self.download_cancelled:
			toast('Download Cancelled') 

	def select_file_path(self, touch):
		''' selected the path to save the file'''
		try:
			filechooser.choose_dir(on_selection=self.selected)
		except Exception as e:
			self.show_error(e)
			traceback.print_exc(file=error_file)
			self.filemanager.exit_manager =self._exit_manager
			self.filemanager.select_path =self._select_path
			self.filemanager.show(app_root)
		if self.filemanager.path:
			self.set_path.text = self.filemanager.path

	def _select_path(self, path):
		'''It will be called when you click on the file name
		or the catalog selection button.
		:type path: str;
		:param path: path to the selected directory or file;
		'''
		self._exit_manager()
		self.set_path.text = path
	def _exit_manager(self, *args):
		'''Called when the user reaches the root of the directory tree.'''
		self.manager_open = False
		self.filemanager.close()
	@mainthread
	def selected(self, path):
		''' register the selected path '''
		
		if isinstance(path, (list, tuple)):
			if len(path) >= 1 :
				self.set_path.text = path[0]
			else:
				pass
		else:
			raise ValueError(f'path not in iteratable should be List of Tuple but got {type(path)}')



class CustomBtn(MDFlatButton, ThemableBehavior):
	pass



class DownloadLabel(MDCard, RoundedRectangularElevationBehavior):
	source = StringProperty()
	text = StringProperty()
	value = NumericProperty()
	downloaded_size = NumericProperty()
	file_size = NumericProperty()
	complete = BooleanProperty(False)
	path = StringProperty('')
	pause = BooleanProperty(False)
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		
		self.thumbnail = FitImage(source=self.source, radius=self.radius, size_hint_x=None, width=self.height)
		self.size_hint_y = None
		self.height =  '64dp'
		self.text_label = MDLabel(text=f'{self.text} is complete {self.value}%')
		self.file_size_label = MDLabel(text=f'{self.downloaded_size}MB | {self.file_size}MB')
		self.progress = MDProgressBar(value=self.value)
		self.pause_play_btn = MDIconButton(icon='pause')
		self.pause = False
		self.pause_play_btn.bind(on_release=self.toggle_pause_play)
		self.box = MDBoxLayout(orientation='vertical')
		self.box.add_widget(self.text_label)
		self.box.add_widget(self.file_size_label)
		self.box.add_widget(self.progress)
		self.add_widget(self.thumbnail)
		self.add_widget(self.box)
		self.add_widget(self.pause_play_btn)
	def toggle_pause_play(self, touch):
		''' changes for pause to play and vice versa '''
		self.pause = not self.pause
		self.pause_play_btn.icon = 'play' if self.pause else 'pause'
	

	def on_complete(self, *args):
		''' removes the progressbar '''
		file_type = self.source.split('/')[-1][-3:]
		filename = self.text.replace(' ','_')
		#image_download(url=self.source, filename=filename, file_type=file_type, path=self.path)
		threading.Thread(target=image_download, kwargs={'url':self.source,'file_type':'.jpg', 'filename':filename, 'path':app_root}).start()
		thumbnail_file = filename+file_type
		insertvalue(conn, thumbnail=thumbnail_file,title=self.text, path=self.path)
		self.box.remove_widget(self.progress)
		self.box.add_widget(MDLabel(text='Download Complete'))

	def on_value(self,*args):
		self.progress.value = self.value
		self.text_label.text = f'{self.text} is complete {self.value}%'
		self.file_size_label.text = f'{self.downloaded_size}MB|{self.file_size}MB '

class Resolution(MDBoxLayout): 
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.orientation = 'vertical'
		self.adaptive_height=True

	
class FileManager(MDFileManager):
	''' gives acces to the file system '''
	path = StringProperty('')
	

class FileDownLoader:

	def __init__(self, on_complete_callback=None, on_progress_callback=None) -> None:
		''' Makes the downloads synchoronous
		can download more than one'''
		self.threads = []
		self.queue = deque()
		self.complete = on_complete_callback
		self.progress = on_progress_callback
	def _download(self, url=None,title=f'Video_{datetime.datetime.now()}',filesize=None, path=None, file_type='.mp4'):
		
		if title.endswith(file_type):
			pass
		else:
			title = title + file_type
		file_path = os.path.join(path, title)
		downloaded = 0
		bytes_remaining = 0
		if not filesize:
			filesize = request.filesize(url)
		if os.path.exists(file_path):
			exists_file_size =  os.path.getsize(file_path)
			if exists_file_size >= filesize:
				#the file was downloaded completely
				return
			else:
				#get the remaining part of the file
				remainder = filesize - exists_file_size
				header = {'Range': f'bytes={remainder}-'}
				response = request._excute_request(url, method='GET', headers=header)
				with open(file_path, 'ab') as f:
					chunk = response.read()
					if chunk:
						f.write(chunk)
		else:	  
			with open(file_path,'wb') as f:
				stream = request.stream(url)
				while True:
					chunk = next(stream, None)
					if chunk:
						f.write(chunk)
						if filesize:
							downloaded += len(chunk)
							bytes_remaining = filesize-downloaded
						self._processing(chunk, bytes_remaining)
					else:
						self.complete(title, path)
				

	def _progress(self, chunk, bytes_remaining):
		self.progress(chunk, bytes_remaining)

		
	def update_thread(self, th):
		# update the thread of app
		if th not in self.threads:
			self.queue.append(th)
	def download(self, url,filesize, path):
		'''set the Download'''
		th = threading.Thread(target=self._download, args=(url, filesize, path))
		self.update_thread(th)
		self.run()
	def run(self, size=5):
		''' start the threads'''
		if len(self.queue) > 0  and len(self.queue) <= size:
			thread = self.queue.popleft()
			thread.start()

class Processing(MDBoxLayout, ThemableBehavior):
    ''' Display the processing pop up with a spinner '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.theme_cls.widget_style = 'desktop'
        
        self.theme_cls.material_style = "M3"
        x, y = Window.size
        self.theme_cls.style = 'Dark'
        self.theme_cls.accent_palette = "Teal"
        self.size = (x/2, dp(60))
        self.md_bg_color = self.theme_cls.opposite_bg_light
        self.spacing = '12sp'
        self.padding = '8sp'
        self.pos_hint={'center_y':0.5, 'center_x':0.5}
        self.spinner = MDSpinner(size_hint=(None,None),
                                size=(self.size[1]-dp(16), self.size[1]-dp(16)), 
                                determinate=False,
                                palette = [
                                            [0.28627450980392155, 0.8431372549019608, 0.596078431372549, 1],
                                            [0.3568627450980392, 0.3215686274509804, 0.8666666666666667, 1],
                                            [0.8862745098039215, 0.36470588235294116, 0.592156862745098, 1],
                                            [0.8784313725490196, 0.9058823529411765, 0.40784313725490196, 1],
                                        ])
        self.label = MDLabel(text='Processing', theme_text_color='Custom', text_color=self.theme_cls.opposite_text_color)
        self.add_widget(self.spinner)
        self.add_widget(self.label)
        Window.bind(on_resize=self.update_size)
    def update_size(self, *args):
    	self.spinner.size = (self.size[1]-dp(16), self.size[1]-dp(16))


class DataContainer(MDCard):
	thumbnail = StringProperty()
	title = StringProperty()
	path =StringProperty()
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.size_hint_y = None
		self.height = '64dp'
		self.info = MDBoxLayout(
								orientation='vertical',
								spacing='2sp'

			)
		self._title = MDLabel(text=self.title)
		self._path = MDLabel(text=self.path)
		self.thumb = FitImage(source=self.thumbnail, size_hint_x=None, width=self.height)
		self.info.add_widget(self._title)
		self.info.add_widget(self._path)
		self.add_widget(self.thumb)
		self.add_widget(self.info)

class Downloads(MDBoxLayout):
	data = ListProperty()
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.orientation = 'vertical'
	
		toolbar = MDTopAppBar(title='Downloads', md_bg_color=[0,0,0,1])
		self.scroll = ScrollView()
		self.list = MDList()
		self.scroll.add_widget(self.list)
		self.add_widget(toolbar)
		self.add_widget(self.scroll)
		self.data = select_all(conn)
	def on_data(self, *args):
		for data in self.data:
			
			d = DataContainer(title=data[1], thumbnail=data[2], path=data[3])
			self.list.add_widget(d)



class SettingsApp(MDBoxLayout):
	''' the settings of the kivy application '''
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		self.settings = {'colors':['Red','Yellow','Teal','BlueGray'],
						 'style':['Light', 'Dark'],
						 }
		self.spacing = '8sp'
		self.scroll = ScrollView()
		self.list = MDList()
		self.scroll.add_widget(self.list)
		self.add_widget(self.scroll)
		for k, v in self.settings.items():
			xp = MDExpansionPanel(
				icon = '',
				content = Content(),
				panel_cls = MDExpansionPanelOneLine(text=k)
				)
			self.list.add_widget(xp)
			xp.content.data = v
			xp = None



class Content(MDGridLayout):
	data = ListProperty()
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.cols = 1
		self.size_hint_y = None
		self.height = Window.size[1]*0.25

		self.scroll = ScrollView()
		self.list = MDList()
		self.scroll.add_widget(self.list)
		self.add_widget(self.scroll)

	
	def on_data(self, *args):
		for d in self.data:
			btn = CustomBtn(text=str(d))
			btn.bind(on_release=self.change_setting)
			self.list.add_widget(btn)
	def change_setting(self, touch):
		self.theme_cls = App.get_running_app().theme_cls
		print(f'changing setting to {touch.text}')
		
		if touch.text in ['Light' , 'Dark' ] :
			self.theme_cls.theme_style = touch.text
		else:
			self.theme_cls.primary_palette = touch.text
			

class YouTubeDownloaderApp(MDApp):
	def build(self):
		self.icon = icon_file
		self.title = 'YouTubeDownloader'
		root = Builder.load_string(kv)
		return root
	def change_screen(self, touch):
		self.root.ids.sm.current = touch.text
	
	def on_start(self):
		import certifi
		os.environ['SSL_CERT_FILE'] = certifi.where()
		os.environ['SSL_CERT_DIR'] = os.path.dirname(certifi.where())
		os.environ['REQUESTS_CA_BUNDLE']=certifi.where()
		self.root.ids.download_db.data = select_all(conn)
	def on_pause(self):
		return True
	def on_stop(self):
		print('Stopping the application')
		


if __name__ == '__main__':
	YouTubeDownloaderApp().run()

