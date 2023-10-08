import os
import certifi

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['SSL_CERT_DIR'] = os.path.dirname(certifi.where())
os.environ['REQUESTS_CA_BUNDLE']=certifi.where()



from you_downloader import YouTubeDownloaderApp

YouTubeDownloaderApp().run()