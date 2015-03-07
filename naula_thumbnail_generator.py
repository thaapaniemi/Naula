#! /usr/bin/env python3
# -*- coding: utf-8 -*-

""" Naula static Thumbnail Gallery Generator

Naula generates static thumbnail preview html-page and thumbnails for jpg/png files in directories
"""

import sys

import os
import shutil
import subprocess

# Default layout template
layout_template = '''
<html>
	<head>
		<link rel="stylesheet" href='http://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css'/>
		<meta name="viewport" content="width=device-width, initial-scale=1"/>
		<title>{{title}}</title>
	</head>
<body>
	<header class="navbar navbar-static-top bs-docs-nav" id="top", role="banner">
				<div class='container'>
					<div class='navbar-header'><div class="navbar-brand"><h1>{{title}}</h1></div>
				</div>
			</div>
	</header>

	<br>

	{%if dirs: %}
	<div class='container'>
		<div class="row"><div class="col-md-1 col-sm-2 col-xs-2">Directories:</div></div>
		{%for row in dirs: %}
		<div class="row">
			{%for d in row: %}
				<div class="col-md-1 col-sm-2 col-xs-2"><h4><a href="{{d}}/index.html">{{d}}</a></h4></div>
			{%endfor%}
		</div>
	{%endfor%}
	</div>
	{%endif%}

	{%if rows: %}
	<div class='container'>
	<div class='jumbotron'>
		{%for row in rows: %}
		<div class="row">
			{%for image in row: %}
				<div class="col-md-2 col-sm-3 col-xs-4"> <a href="{{image.filename}}"> <img src="{{image.thumbfilename}}"></img></a></div>
			{%endfor%}
		</div>
		<br>
		{%endfor%}
	</div></div>
	{%endif%}

</body>
</html>
'''

config = {
	"gallery_paths":[],
	"force_html_generation":False,
	"force_thumbnail_generation":False,
	"whitelist":("jpg","png"),
	"thumbnail_size":96,
	"thumbnail_directory":"tn",
	"template": layout_template,
	"row_columns":5
}

def handle_arguments(config):
	"""Return config list from commandline arguments"""

	import argparse
	parser = argparse.ArgumentParser(description='Generate thumbnail gallery')
	parser.add_argument('path', metavar='PATH', type=str, nargs='+',help='path')
	parser.add_argument('-f', dest='force_html', action='store_const',const=True, default=False,help='Force HTML generation')
	parser.add_argument('-ft', dest='force_thumb', action='store_const',const=True, default=False,help='Force thumbnail generation')
	
	parser.add_argument("-c", dest='row_columns', action='store', type=int, help="pictures in row")
	parser.add_argument("-t", dest='template', action='store', help="Template for layout")
	parser.add_argument("-tn", dest='thumbnail_path', action='store', help="Thumbnail directory name")
	parser.add_argument("-w", dest='whitelist', action='store', help="Comma separated list of extensions that are generated to thumbnails")
	parser.add_argument("-s", dest='thumbnail_size', action='store', type=int, help="size of Thumbnails")

	result = parser.parse_args()

	config["force_html_generation"] = result.force_html
	config["force_thumbnail_generation"] = result.force_thumb
	config["gallery_paths"] = result.path

	if result.row_columns:
		config["row_columns"] = result.row_columns

	if result.thumbnail_path:
		config["thumbnail_directory"] = result.thumbnail_path

	if result.template:
		with open( result.template, "rb" ) as fh:
			config["template"] = fh.read()

	if result.whitelist:
		extensions = result.whitelist.split(",")
		config["whitelist"] = extensions

	if result.thumbnail_size:
		config["thumbnail_size"] = result.thumbnail_size
		
	if result.template or result.whitelist or result.thumbnail_size or result.row_columns:
		config["force_thumbnail_generation"] = True
		config["force_html_generation"] = True



	#print(str(config["gallery_paths"]))

	return config

def run_ext(array,stdin=None):
	"""Run external process"""
	import subprocess
	
	ssh = subprocess.Popen(array, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	if stdin is not None:
		ssh.stdin.write( stdin )
	
	out, err = ssh.communicate()

	#print out
	#print err

	return (out,err)

def make_thumbnail_with_mogrify(inputfile,outputdir,**kwargs):
	"""Create thumbnail with ImageMagic:mogrify

	Keyword arguments:
	inputfile -- file to be thumbnailed
	outputdir -- path to thumbnail directory
	"""

	thumb_size = str( kwargs["thumbnail_size"] )

	cmd_array = ["/usr/bin/mogrify"]

	params = {
		"resize":thumb_size + "x" + thumb_size,
		"background":"white",
		"gravity":"center",
		"extent":thumb_size + "x" + thumb_size,
		"format":"jpg",
		"quality":"80",
		"path":outputdir
	}

	for key in params:
		value = params[key]

		cmd_array.append("-"+key)
		cmd_array.append(value)
	cmd_array.append(inputfile)
	(out,err) =run_ext(cmd_array)

	return

def make_thumbnail_with_pillow(inputfile,outputdir,**kwargs):
	"""Create thumbnail with Pillow imaging library

	Keyword arguments:
	inputfile -- file to be thumbnailed
	outputdir -- path to thumbnail directory
	"""

	from PIL import Image

	outputfile = os.path.basename(inputfile)
	outputfile = outputfile.split(".")
	outputfile[-1] = "jpg"
	outputfile = outputdir + ".".join(outputfile)

	image = Image.open(inputfile)
	thumb_size = ( int( kwargs["thumbnail_size"] ), int( kwargs["thumbnail_size"] ) )
	

	image.thumbnail(thumb_size)

	image.save(outputfile)

	return

def generate_html_with_template(template,**kwargs):
	""" Generate static HTML page from jinja2 template"""
	
	from jinja2 import Template
	template = Template( template )
	return template.render(**kwargs)



def make_html(files,dirs,path,**kwargs):
	"""Generate static HTML page of files and folders

	Keyword arguments:
	files -- list of files
	dirs -- list of subdirectories showed in result page
	path -- ouput path of generated html
	"""

	whitelist = kwargs["whitelist"]	
	cols = int(kwargs["row_columns"])

	printable_dirs = []
	current_row = []
	for i,d in enumerate( sorted(dirs) ):
		if i % 5 == 0 and len(current_row) > 0:
			printable_dirs.append(current_row)
			current_row = []

		if d != kwargs["thumbnail_directory"]:
			current_row.append(d)
	
	if len(current_row) > 0:
		printable_dirs.append(current_row)


	rows = []
	
	current_row = []
	for i,f in enumerate( sorted(files) ):
		if i % 5 == 0 and len(current_row) > 0:
			rows.append(current_row)
			current_row = []

		f_out = f.split(".")
		f_out[-1] = "jpg"
		f_out = ".".join(f_out)

		ff = {
			"filename":f,
			"thumbfilename":kwargs["thumbnail_directory"]+"/"+f_out
		}

		if f.split(".")[-1] in whitelist:
			current_row.append(ff)
	
	if len(current_row) > 0:
		rows.append(current_row)

	template_kwargs = {
		"rows":rows,
		"dirs":printable_dirs,
		"title":path.split("/")[-1]
	}

	
	t = generate_html_with_template( kwargs["template"], **template_kwargs )

	if len(printable_dirs) > 0 or len(files) > 0:
		with open(path+"/index.html","wb") as fh:
			fh.write( bytes(t,'UTF-8') )


def main(path,config):
	"""Generate thumbnails and static html pages recursively for each directory"""
	
	for (dirpath, dirnames, filenames) in os.walk(path):
		thumbpath = dirpath + "/"+ config["thumbnail_directory"]

		if dirpath.find("/"+config["thumbnail_directory"]) > 0:
			pass
		else:
			new_content = False

			if len(filenames) > 0 and os.path.isdir( thumbpath ) is False:
				os.makedirs( thumbpath )

			for filename in filenames:
				if not os.path.exists( thumbpath +"/"+ filename ) or config["force_thumbnail_generation"]:
					if filename.split(".")[-1] in config["whitelist"]:
						new_content = True
						
						try:
							make_thumbnail_with_pillow( dirpath+"/"+filename, thumbpath+"/", **config )
						except ImportError as e:
							print("ImportError: " + str(e))
							print("Using Fallback: mogrify")
							make_thumbnail_with_mogrify( dirpath+"/"+filename, thumbpath+"/", **config )


			if new_content or not os.path.exists(dirpath+"/index.html") or config["force_html_generation"]:
				make_html(filenames,dirnames,dirpath,**config)

if __name__ == '__main__':
	config = handle_arguments(config)
	
	for path in config["gallery_paths"]:
		main(path,config)
