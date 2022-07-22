#!/usr/bin/env python3

import json

import numpy as np
import pandas as pd
import os
import glob
import sys
import csv


class ChartsEditor:


	def __init__(self):

		# Input .csv files to be processed
		self.input_folder_name = 'Temp_Files/ChartsEditor/To_Process'

		# Folder for ouput processed html files
		self.processed_charts_folder = 'Temp_Files/ChartsEditor/Processed'

		# Folder for google charts HTML templates
		self.html_templates_folder = 'Temp_Files/ChartsEditor/HTML_Templates'

		# google charts HTML template name 
		self.geo_chart_static_all_template_name = 'GeoChart_Static_T_all_Country.html'

		# Movie Title flag for HTML template files
		self.movie_title_flag = "FILME"
		
		'''
		self.input_csv_path = 'Output_-_Moonfall.2022.1080p.AMZN.WEBRip.DDP5.1.x_Analysed_Unique_T_final___Chart_Country.csv'

		self.input_html_file_path = 'templates/uniqueCountry.html'

		self.output_html_file_path = 'templates/uniqueCountry_ready.html'
		'''

	# Verify files in folder
	def FilesToProcess(self, script_path, extension):
		
		files_to_process_folder_path = os.path.join(script_path, self.input_folder_name)

		#print(files_to_process_folder_path)

		os.chdir(files_to_process_folder_path)
		files_names_array = glob.glob('*.{}'.format(extension))

		return files_names_array, files_to_process_folder_path


	
	def ProcessGeoChartStaticAll(self, script_path, input_file_name, input_file_path, template_html_file_name, movie_title):

		try:
			input_html_template_path = os.path.join( script_path, self.html_templates_folder, template_html_file_name) 

			output_html_path = os.path.join( script_path, self.processed_charts_folder, input_file_name.split('/')[0].split('.csv')[0]+'__'+template_html_file_name.split('_')[0]+'__Done.html')


			# === Transform rows as list of lists (to Google Chart recognize)
			data_csv = pd.read_csv(input_file_path, sep=',', encoding = 'utf-8')

			#title = "Paises de todas as conexoes ao torrent Moonfall (2022)"

			# Columns heads: string, number
			countries = data_csv[[ data_csv.columns[0], data_csv.columns[1] ]]
			#countries['Country_occurences'] = countries['Country_occurences'].astype(str)

			d = countries.values.tolist()
			c = countries.columns.tolist()
			d.insert(0,c)


			# === Edit the HTML file
			with open(input_html_template_path, 'r') as input_html_file:
			    html_file_lines = input_html_file.readlines()

			for i_line, str_line in enumerate(html_file_lines):
				if str_line.endswith('arrayToDataTable();\n'):

					html_data_chart_array = str_line.split('(',1)

					output_str = html_data_chart_array[0] + "(" + str(d) + html_data_chart_array[1]

					html_file_lines[i_line] = output_str

				if self.movie_title_flag in str(str_line):
					html_data_chart_array = str_line.split(self.movie_title_flag)

					output_str = html_data_chart_array[0] + movie_title + html_data_chart_array[1]

					html_file_lines[i_line] = output_str


			#print("\n\n\n ouput data:\n")
			#print(output_str)


			with open(output_html_path, 'w+') as output_html_file:
			    output_html_file.writelines(html_file_lines)

			return 1

		except Exception as e:
			print(e)

			return 0


	def ProcessLineChartStatic(self, script_path, input_file_name, input_file_path, template_html_file_name, movie_title):

		
		input_html_template_path = os.path.join( script_path, self.html_templates_folder, template_html_file_name) 

		output_html_path = os.path.join( script_path, self.processed_charts_folder, input_file_name.split('/')[0].split('.csv')[0]+'__'+template_html_file_name.split('_')[0]+'__Done.html')


		with open(input_file_path, mode = 'r') as f:
			sum_lines = len(f.readlines())

		table = []
		#table_2 = []
		table_zoom1 = []
		table_zoom2 = []

		rank_max = 0;

		with open(input_file_path, mode = 'r') as input_file:

			csvFile = csv.reader(input_file)


			i_line = -1
			for line in csvFile:
				i_line = i_line + 1

				if i_line == 0:
					header = line.append(["day","mounth","year"])

				else:
					day = line[0].split('-')[0]
					mounth = line[0].split('-')[1]

					if len(list(mounth)) > 1:

						if list(mounth)[0] == '0':
							mounth = list(mounth)[1]

					year = line[0].split('-')[2]

					'''
					if i_line == (sum_lines-1):
						vir = ''
					else:
						vir = ','
					'''

					table.append('[new Date('+year+','+mounth+','+day+'), '+str(line[1:len(line)]).replace('[','').replace(']','')+']')
					#table_2.append('new Date('+year+','+mounth+','+day+')')

					# without Peers Total and Seeds Total
					table_zoom1.append('[new Date('+year+','+mounth+','+day+'), '+str(line[1:len(line)-2]).replace('[','').replace(']','')+']')

					# without Peers Total, Seeds Total, Complete by Tracker and Incomplete by Tracker
					table_zoom2.append('[new Date('+year+','+mounth+','+day+'), '+str(line[1]).replace('[','').replace(']','')+','+str(line[4:7]).replace('[','').replace(']','')+']')

					rank = line[1]
					if int(rank) > int(rank_max):
						rank_max = int(rank)

					


		'''
		# === Transform rows as list of lists (to Google Chart recognize)
		data_csv = pd.read_csv(input_file_path, sep=',', encoding = 'utf-8')

		df = pd.DataFrame(data_csv)

		df.loc[:,'day'] = df.loc[:,data_csv.columns[0]].split('-')[0]
		df.loc[:,'mounth'] = df.loc[:,data_csv.columns[0]].split('-')[1]
		df.loc[:,'year'] = df.loc[:,data_csv.columns[0]].split('-')[2]


		#title = "Paises de todas as conexoes ao torrent Moonfall (2022)"

		# Columns heads: string, number
		table = data_csv[[ "new Date("+df.loc[:,'day']+","+ df.loc[:,'mounth']+","+ df.loc[:,'year']+")", data_csv.columns[2], data_csv.columns[1], data_csv.columns[3], data_csv.columns[4], data_csv.columns[5], data_csv.columns[6], data_csv.columns[7], data_csv.columns[8]  ]]
		
		table2 = data_csv[ "new Date("+df.loc[:,'day']+","+ df.loc[:,'mounth']+","+ df.loc[:,'year']+")"]

		#countries['Country_occurences'] = countries['Country_occurences'].astype(str)

		d = table.values.tolist()
		#c = countries.columns.tolist()
		#d.insert(0,c)
		'''


		# === Edit the HTML file
		with open(input_html_template_path, 'r') as input_html_file:
		    html_file_lines = input_html_file.readlines()

		for i_line, str_line in enumerate(html_file_lines):

			'''
			if "NAME_A" in str_line:
				html_line = str_line.split("NAME_A")

				

				
					
				html_file_lines[i_line] = html_line[0] + table+ html_line[1]
			'''

			if "ZOOM1" in str_line:
				html_line = str_line.split("ZOOM1")

				output = html_line[0] +str(table_zoom1)+ html_line[1]

				output = output.replace('"','').replace("'",'')

				html_file_lines[i_line] = output

			elif "ZOOM2" in str_line:
				html_line = str_line.split("ZOOM2")

				output = html_line[0] +str(table_zoom2)+ html_line[1]

				output = output.replace('"','').replace("'",'')

				html_file_lines[i_line] = output

			elif str_line.endswith('data.addRows();\n'):
				
				html_line = str_line.split("(")

				output = html_line[0] +'(' +str(table)+ html_line[1]

				output = output.replace('"','').replace("'",'')

				html_file_lines[i_line] = output

			if self.movie_title_flag in str(str_line):
				html_data_chart_array = str_line.split(self.movie_title_flag)

				output_str = html_data_chart_array[0] + movie_title + html_data_chart_array[1]

				html_file_lines[i_line] = output_str
			'''
			if "ticks:" in str_line:
				html_line = str_line.split(":")

				output = html_line[0] +':' +str(table_2)

				output = output.replace("'",'')

				html_file_lines[i_line] = output
			'''

			if "maxValue" in str_line:
				html_line = str_line.split("maxValue:")

				rank_max = rank_max + 5

				output = html_line[0] + 'maxValue: '+str(rank_max) + html_line[1]

				output = output.replace("'",'')

				html_file_lines[i_line] = output

			
		#print("\n\n\n ouput data:\n")
		#print(output_str)


		with open(output_html_path, 'w+') as output_html_file:
		    output_html_file.writelines(html_file_lines)

		return 1



	def ProcessStackedBarChartStaticAll(self, script_path, input_file_name, input_file_path, template_html_file_name, movie_title):

	
		input_html_template_path = os.path.join( script_path, self.html_templates_folder, template_html_file_name) 

		output_html_path = os.path.join( script_path, self.processed_charts_folder, input_file_name.split('/')[0].split('.csv')[0]+'__'+template_html_file_name.split('_')[0]+'__Done.html')

		# === Transform rows as list of lists (to Google Chart recognize)
		data_csv = pd.read_csv(input_file_path, sep=',', encoding = 'utf-8')

		df = pd.DataFrame(data_csv)

		# get the first row of the file without the first column
		array_name_columns = list(data_csv.columns)
		array_name_columns[0] = 'Client App'
		array_name_columns.pop(-1)


		array_columns = list(data_csv.columns)
		array_columns.pop(-1)

		# Columns heads: string, number
		output_array = data_csv[array_columns]

		d = output_array.values.tolist()

		# === Edit the HTML file
		with open(input_html_template_path, 'r') as input_html_file:
		    html_file_lines = input_html_file.readlines()

		for i_line, str_line in enumerate(html_file_lines):
			if str_line.endswith('arrayToDataTable();\n'):

				html_data_chart_array = str_line.split('(',1)

				output_str = html_data_chart_array[0] + "(" + '['+str(array_name_columns)+','+str(d).replace('[[','[') + html_data_chart_array[1]

				html_file_lines[i_line] = output_str

			if self.movie_title_flag in str(str_line):
				html_data_chart_array = str_line.split(self.movie_title_flag)

				output_str = html_data_chart_array[0] + movie_title + html_data_chart_array[1]

				html_file_lines[i_line] = output_str


		with open(output_html_path, 'w+') as output_html_file:
		    output_html_file.writelines(html_file_lines)

		return 1

		

	




	def main(self):

		current_path = os.getcwd()

		files_to_process_array, files_to_process_folder_path = ChartsEditor.FilesToProcess(self, current_path, "csv")
		
		os.chdir(current_path)
		#print(files_to_process_array)

		files_to_process_path_array = []

		for i_file, file_to_process_name in enumerate(files_to_process_array):

			files_to_process_path_array.append(os.path.join( files_to_process_folder_path, files_to_process_array[i_file] ))

			print("\n== Start Chart Making for the file: \n    "+file_to_process_name)

			progres_p_f = float(((i_file+1) * 100)/len(files_to_process_array))

			movie_title = file_to_process_name.split('Output_-_')[1]

			movie_title = movie_title[:40] 

			# Static: Country vs number of IPs - Chart
			if file_to_process_name.endswith("Static_T_all_Country.csv"):

				# GeoChart
				template_html_file_name = 'GeoChart_Static_T_all_Country.html'
				result = ChartsEditor.ProcessGeoChartStaticAll(self, current_path, file_to_process_name, files_to_process_path_array[i_file], template_html_file_name, movie_title)

				# BarChart (Horizontal)
				template_html_file_name = 'BarChart_Static_T_all_Country.html'
				result = ChartsEditor.ProcessGeoChartStaticAll(self, current_path, file_to_process_name, files_to_process_path_array[i_file], template_html_file_name, movie_title)

				# PieChart
				template_html_file_name = 'PieChart_Static_T_all_Country.html'
				result = ChartsEditor.ProcessGeoChartStaticAll(self, current_path, file_to_process_name, files_to_process_path_array[i_file], template_html_file_name, movie_title)


			# Static: Organization (ISPs) vs number of IPs - Chart
			if file_to_process_name.endswith("Static_T_all_Organization.csv"):

				# BarChart (Horizontal)
				template_html_file_name = 'BarChart_Static_T_all_Organization.html'
				result = ChartsEditor.ProcessGeoChartStaticAll(self, current_path, file_to_process_name, files_to_process_path_array[i_file], template_html_file_name, movie_title)

				# PieChart
				template_html_file_name = 'PieChart_Static_T_all_Organization.html'
				result = ChartsEditor.ProcessGeoChartStaticAll(self, current_path, file_to_process_name, files_to_process_path_array[i_file], template_html_file_name, movie_title)

			# Static: Client App vs number of IPs - Chart
			if file_to_process_name.endswith("Static_T_all_client.csv"):

				# BarChart (Horizontal)
				template_html_file_name = 'BarChart_Static_T_all_client.html'
				result = ChartsEditor.ProcessGeoChartStaticAll(self, current_path, file_to_process_name, files_to_process_path_array[i_file], template_html_file_name, movie_title)

				# PieChart
				template_html_file_name = 'PieChart_Static_T_all_client.html'
				result = ChartsEditor.ProcessGeoChartStaticAll(self, current_path, file_to_process_name, files_to_process_path_array[i_file], template_html_file_name, movie_title)


			# Static: Popularity Vs other columns - Chart
			if file_to_process_name.endswith("Static_T_all_PopularityByDay.csv"):

				# LineChart (Dual-Y)
				template_html_file_name = 'LineChartTwoYAxis_Static_Days_Popularity.html'
				result = ChartsEditor.ProcessLineChartStatic(self, current_path, file_to_process_name, files_to_process_path_array[i_file], template_html_file_name, movie_title)

				# LineChart (Dual-Y) Zoomed 1x
				template_html_file_name = 'LineChartTwoYAxisZoom1_Static_Days_Popularity.html'
				result = ChartsEditor.ProcessLineChartStatic(self, current_path, file_to_process_name, files_to_process_path_array[i_file], template_html_file_name, movie_title)

				# LineChart (Dual-Y) Zoomed 2x
				template_html_file_name = 'LineChartTwoYAxisZoom2_Static_Days_Popularity.html'
				result = ChartsEditor.ProcessLineChartStatic(self, current_path, file_to_process_name, files_to_process_path_array[i_file], template_html_file_name, movie_title)

			# Static: Client App vs Countries vs number of IPs - Chart
			if file_to_process_name.endswith("Static_T_all_ClientCountries.csv"):

				# Stacked Bar Chart
				template_html_file_name = 'StackedBar_Static_T_all_client.html'
				result = ChartsEditor.ProcessStackedBarChartStaticAll(self, current_path, file_to_process_name, files_to_process_path_array[i_file], template_html_file_name, movie_title)

			# Static: Organization vs Countries vs number of IPs - Chart
			if file_to_process_name.endswith("Static_T_all_OrganizationCountries.csv"):

				# Stacked Bar Chart
				template_html_file_name = 'StackedBar_Static_T_all_organization.html'
				result = ChartsEditor.ProcessStackedBarChartStaticAll(self, current_path, file_to_process_name, files_to_process_path_array[i_file], template_html_file_name, movie_title)

				

				
			
			if result:
					print("\n Done! {:.2f}% ({:d}/{:d})\n   csv file:{:s}\n".format(progres_p_f, i_file+1, len(files_to_process_array), file_to_process_name ))
			else:
				sys.exit()

		
		return 1
		
		


if __name__ == "__main__":
	app = ChartsEditor()
	app.main()
