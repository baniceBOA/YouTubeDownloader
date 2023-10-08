
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import StringProperty
from kivymd.uix.card import MDCard
from kivy.lang import Builder

kv = '''
<SearchItem>:
	MDBoxLayout:
		orientation:'vertical'
		size_hint_y:None
		height:dp(360)
		spacing:'2sp'
		padding:dp(25), 0, dp(25), 0
		MDLabel:
			text:root.title
			valign:'center'
		FitImage:
			source:root.thumbnail
			size_hint_y:None
			height:dp(200)
			size_hint_x:None
			width:dp(300)
		MDLabel:
			text:f'video duration {root.length}'
			valign:'center'
			font_size:"20dp"
		
		MDBoxLayout:
			ThreeLineListItem:
				text:root.title
				secondary_text:root.channel
				tertiary_text:root.views
			MDIconButton:
				id:download_btn
				icon:'download'
				on_release:app.download(root.url)

'''
Builder.load_string(kv)

class SearchItem(MDCard):
	thumbnail = StringProperty()
	title = StringProperty()
	channel = StringProperty()
	views = StringProperty()
	length = StringProperty()
	url = StringProperty()


class TestApp(MDApp):
	def build(self):
		return SearchItem(thumbnail='D:/files/images/IMG-20220313-WA0011.jpg', length='40m', url='My work', title='My test', channel='My channel', views='34')
	def download(self, url):
		print(f'download {url}')

if __name__ == '__main__':
	TestApp().run()


