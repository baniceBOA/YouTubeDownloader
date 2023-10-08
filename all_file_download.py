
import logging
from urllib.request import urlopen, Request
import os
import socket
from functools import lru_cache
from plyer import storagepath
from kivy.utils import platform

logger = logging.getLogger(__name__)

#The application should be able to download all the files and be able to continue
# a paused download
#The files can be downloaded concurrently



class Chunker:
    def __init__(self, file_size=int(2**10*1024), chunk_size=1024*1024):
        ''' The chunker split the file into managerable file size for downloads
        Parameters
        =========
        file_size:
            the size of the file to be downloaded in  bytes
        chunk_size:
            the size of the file being downloaded in bytes
        '''
        self.file_size = file_size
        self.chunk_size = chunk_size
        self.gb = 1024*1024*1024
        self.mb = 1024*1024
        self.new = 0
    def chunk(self):
        ''' reduces the chunk on every call on the same object
        Parameters
        =========
            None
        
        returns:
            chunk_size
        the chunk of the file
        '''
        if self.chunk_size == 1024*1024:
            if self.file_size < self.mb:
            	return self.chunk_size
            if self.file_size >= self.mb and self.file_size < self.gb:
                # the file is greater than an mb
                # therefore download it chunk by chunk
                return int(self.file_size/(1024))
            if self.file_size > self.gb:
                #increase the chunk_size for the download to go a little faster
                
                return int(self.file_size/(1024))
        else:
            return self.chunk_size




def download(url='',filename=None,path=None, file_type='', progress_callback=None, complete_callback=None) -> None:
	''' download a url  the given,
	Parameters
	==========

	url: 
		The link to download
	header: 
		header to be passed to the server,  
		The header is a dcitionary
	file_type:
		Type of file downloading  defaults to a
		empty string
	progess_callback:
		A call back for the download process
	complete_callback:
		A callback for when the download is complete
	return:
		None
	'''
	downloaded = 0 
	bytes_remaining = 0
	state = False
	
	file_size = filesize(url)
	if not file_type:
		file_type = url.split('/')[-1][-3:]
		print(url)

	file_path = os.getcwd() if path == None else path
	if platform == 'android':
		file_path = storagepath.get_downloads_dir()

	if filename:
		filename += file_type
	else:
		filename = url.split('/')[-1]
	if filename.endswith(file_type):
		# we are downloading the appropriate file
		if filename in os.listdir(file_path):
			#the file is in the downloads 
			#if it is an incomplete download continue downloading else avoid downloading a duplicate
			file_path = os.path.join(file_path, filename)
			existsize = os.path.getsize(file_path)
			logger.info('FOUND FIlE CONTINUE DOWNLOADING')
			print('Found file continue downloading')
			
			with open(file_path, 'ab') as f:
				_stream = continue_download(url, existsize)
				while True:
					if state:
						state = progress_callback(file_size, bytes_remaining)
						continue
					else:
						chunk = next(_stream,None)
						if chunk:
							f.write(chunk)
							downloaded += len(chunk)
							bytes_remaining = file_size - downloaded
							if progress_callback:
								state = progress_callback( file_size, bytes_remaining)
							else:
								pass
						else:
							if complete_callback:
								complete_callback(filename, file_path)
							break

		else:
			if path:
				file_path = os.path.join(path, filename)
			elif file_path.endswith(file_type):
				file_path = file_path
			else:
				_path = os.path.join(file_path, filename)
				if ':' in path:
					raw = os.path.sep
					file_path = _path.replace(':', raw)
				else:
					file_path = _path
			print(file_path)
			with open(file_path,'wb') as f:
				_stream = stream(url)
				while True:
					if state:
						state = progress_callback(file_size, bytes_remaining)
						continue
					else:
						chunk = next(_stream,None)
						
						if chunk:
							
							f.write(chunk)
							downloaded += len(chunk)
							bytes_remaining = file_size - downloaded
							if progress_callback:
					 			state = progress_callback(file_size, bytes_remaining) # the progress callback alsways return the state of the download False continue True stop
						else:
							if complete_callback:
								complete_callback(filename, file_path)
							break
	else:
		raise ValueError('Kindly provide an appropriate file extension')


@lru_cache
def filesize(url):
	return int(urlopen(url).info()['Content-Length'])

def stream(url, headers={}, method='GET'):
	''' streams a url for either upload or download
	Parameters
	==========
	url:
		link to stream
	header:
		The header to be passed to the calling function
		The header is a dictionary 
	method:
		The type of request being perfomed, can be one of 
		'GET', 'POST', 'DELETE'
	returns:
		a Generator of the responces contents

	'''
	header = {"User-Agent": "Mozilla/5.0", "accept-language": "en-US,en"}
	if headers:
		header.update(headers)
	request = Request(url, headers=header, method=method)
	response = urlopen(request)
	file_size = filesize(url)
	chunker = Chunker(file_size=int(file_size))
	def generator():
		''' Generate the chunk for the download '''
		try:
			import request
			resp = requests.get(url, stream=True)
			if 'Content-Length' in resp.headers:
				#Our file has a file size and it a  file size
				#proceed
				#use the iter_content from requests library
				return resp.iter_content(chunk_size=chunker.chunk())
		except:
			#the request library is not present
			#use the standard package of the file
			downloaded = 0
			chunk_size = chunker.chunk()
			while downloaded < file_size:
				stop_pos = min(downloaded+chunk_size, file_size)
				
				download_bytes = f'bytes={downloaded}-{stop_pos}' 
				req = Request(url, headers=header,  method=method)
				req.add_header('Range',download_bytes)
				response = urlopen(req, timeout=socket._GLOBAL_DEFAULT_TIMEOUT)
				chunk = response.read()
				if chunk:
					 downloaded += len(chunk)
					 yield chunk
				else:
					break
	gen = generator()
	
	return gen

def continue_download(url,file_size):
	''' this function resumes an incomplete download 
	Parameters
	==========
	url:
		the link of the download
	filesize:
		the filesize that is already downloaded
	returns
	=======
		 It returns a generator of the download
		 this is because a generator is memory safe 
	'''

	downloaded = file_size
	
	file_size = filesize(url)
	chunker = Chunker(file_size=file_size)
	chunk_size = chunker.chunk()
	while downloaded < file_size:
		stop_pos = min(downloaded+chunk_size, file_size)
		download_bytes = f'bytes={downloaded}-{stop_pos}' 
		req = Request(url)
		req.add_header('Range',download_bytes)
		response = urlopen(req, timeout=socket._GLOBAL_DEFAULT_TIMEOUT)
		chunk = response.read()
		if chunk:
			 downloaded += len(chunk)
			 
			 yield chunk
		else:
			break
def progress_callback( file_size, bytes_remaining):
	logger.info(f'downloaded  {int(file_size/1000000)}  MB')
	print(f'downloaded  {int(bytes_remaining/1000000)} MB')
	return False
def complete_callback(filename, file_path):
	logger.info('File download complete')
	print('download complete')

if __name__ == '__main__':
	download('http://127.0.0.1:5000/uploads/locked.mp4', progress_callback=progress_callback, complete_callback=complete_callback)