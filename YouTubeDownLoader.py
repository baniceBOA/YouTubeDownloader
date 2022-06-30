''' YouTube downoader application'''

from pytube import YouTube
from bs4 import BeautifulSoup
import os 
import threading
import concurrent.futures

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRoundFlatButton
from kivymd.uix.textfield import MDTextFieldRound, MDTextField
from kivymd.uix.progressbar import MDProgressBar
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import RoundedRectangularElevationBehavior
from kivymd.uix.card import MDCard
from kivymd.utils.fitimage import FitImage
from kivy.clock import Clock, mainthread


class DownLoader(MDFloatLayout, ThemableBehavior):
	''' Provides the interfaces to download the images '''
	link = StringProperty()
	value = NumericProperty()
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.link_input = MDTextField(size_hint_x=None, width='360dp')
		self.set_path = MDTextField(size_hint_x=None, width='360dp')
		self.link_input.pos_hint = {'top':0.9}
		self.set_path.pos_hint = {'top':0.1}
		self.link = self.link_input.text
		self.download_content = MDBoxLayout(orientation='vertical',spacing='30sp', adaptive_height=True)
		self.scroller_download = ScrollView()
		self.scroller_download.pos_hint = {'top':0.75}
		self.scroller_download.add_widget(self.download_content)
		self.label = MDLabel(text='Select the Quality of Your Download')
		self.finished = MDBoxLayout(orientation='vertical',spacing='30sp', adaptive_height=True)
		self.scroller_finished = ScrollView()
		self.scroller_finished.add_widget(self.finished)
		self.download_content.add_widget(self.label)
		self.download_btn = MDRoundFlatButton(text='Download')
		self.download_btn.bind(on_release=self.get_streams)
		self.download_btn.pos_hint = {'top':0.9, 'center_x':0.6}
		self.add_widget(self.set_path)
		self.add_widget(self.download_btn)
		self.add_widget(self.link_input)
		self.add_widget(self.scroller_download)
	def on_link(self, *args):
		''' process the link to download the vide0'''
		youtube = YouTube(link)
		for stream in youtube.streams:
			print(streams)
	def get_streams(self, touch):
		''' it process the link'''
		threading.Thread(target=self.processing, args=()).start()
			

	def processing(self):
		
		resolution = ['2160p','1440p','1080p','720p','480p','360p','240p']

		self.yt = YouTube(self.link_input.text, on_complete_callback=self.complete, on_progress_callback=self.progress)
		self.res_dict = {}
		for res in resolution:
			stream = self.yt.streams.get_by_resolution(res)
			if stream:
				self.res_dict[res] =  stream
		self.update_window()
	@mainthread		
	def update_window(self):
		resolution = ['2160p','1440p','1080p','720p','480p','360p','240p']
		self.res = Resolution()
		self.download_dialog = MDDialog(title='Download', type='custom', content_cls=self.res)
		for res in resolution:
			if res in self.res_dict:
				self.res.add_widget(CustomBtn(text=res,theme_text_color='Custom', text_color=[1,0.3,0,0.5], on_release=self._download))
		self.download_dialog.open()
		
	@mainthread
	def _download(self, touch):
		
		''' internal '''
		self.value = 0
		stream = self.res_dict[touch.text]
		path = self.set_path.text
		if not path:
			path = os.getcwd()
		self.download_label = DownloadLabel(text=self.yt.title, source=self.yt.thumbnail_url)
		self.download_content.add_widget(self.download_label)
		touch.text_color = self.theme_cls.primary_color
		self.download_dialog.dismiss()
		threading.Thread(target=self.download, args=(stream, path)).start()

		
		
	def download(self, stream, path=None):
		''' downloads the files '''
		
		if path:
			stream.download(path)
		else:
			stream.download()
		
		
	@mainthread
	def complete(self, stream, filepath):
		''' action perfomed when the download is complete'''
		print('download complete')
		self.download_label.complete = True
	@mainthread
	def progress(self, stream, chunk, bytes_remaining):
		''' the action perfomed while downloading is taking place '''
		self.value = int(100 - bytes_remaining/stream.filesize*100)
		self.download_label.value = int(100 - bytes_remaining/stream.filesize*100)





class CustomBtn(MDFlatButton, ThemableBehavior):
	pass



class DownloadLabel(MDCard, RoundedRectangularElevationBehavior):
	source = StringProperty()
	text = StringProperty()
	value = NumericProperty()
	complete = BooleanProperty(False)
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		
		self.thumbnail = FitImage(source=self.source, radius=self.radius, size_hint_x=None, width=self.height)
		self.size_hint_y = None
		self.height =  '56dp'
		self.text_label = MDLabel(text=f'{self.text} is complete {self.value}%')
		self.progress = MDProgressBar(value=self.value)
		self.box = MDBoxLayout(orientation='vertical')
		self.box.add_widget(self.text_label)
		self.box.add_widget(self.progress)
		self.add_widget(self.thumbnail)
		self.add_widget(self.box)
	def on_complete(self, *args):
		''' removes the progressbar '''
		self.box.remove_widget(self.progress)
		self.box.add_widget(MDLabel(text='Download Complete'))
	def on_value(self,*args):
		self.progress.value = self.value
		self.text_label.text = f'{self.text} is complete {self.value}%'

class Resolution(BoxLayout): 
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.orientation = 'vertical'
		self.size_hint_y = None
		self.height = '160dp'
	



class YouTubeDownloaderApp(MDApp):
	def build(self):
		return DownLoader()


if __name__ == '__main__':
	YouTubeDownloaderApp().run()

