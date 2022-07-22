#!/usr/bin/env python3

import ipinfo
#from ipinfo.handler_utils import cache_key

import pprint
import asyncio
import aiohttp
import sys
import logging
from datetime import date, datetime
import pandas as pd
import re
import csv 
import os
import numpy as np
from collections import Counter
import glob

import ChartsEditor

#from rest_framework import serializers

#from incoming import datatypes, PayloadValidator
from decimal import *

#csv_files_path_array = ['/home/lm-vm/Desktop/Link to Projeto_Licenciatura/OuputFiles/Output_-_Moonfall.2022.1080p.AMZN.WEBRip.DDP5.1.x.csv',
#                    '/home/lm-vm/Desktop/Link to Projeto_Licenciatura/OuputFiles/Output_-_Spider-Man.No.Way.Home.2021.1080p.BluRay.csv']



#csv_files_path_array = ['/home/lm-vm/Desktop/Link to Projeto_Licenciatura/OuputFiles/Output_-_Spider-Man.No.Way.Home.2021.1080p.BluRay.csv']


class IP_Analyser:

    def __init__(self):

        self.csv_files_path_array = ['/home/lm-vm/Desktop/Link to Projeto_Licenciatura/OuputFiles/Output_-_Moonfall.2022.1080p.AMZN.WEBRip.DDP5.1.x.csv']

        # Folders Analyse IPs
        self.input_folder_name = 'Input_csv_AnalyseIPs'
        self.output_folder_name = 'Output_csv_AnalyseIPs'

        # Folder to splitted and unique csv
        self.temp_beforechart_folder_name = 'Temp_Files/IP_Analyser/BeforeChart'

        self.temp_csv_cleaner_folder_name = 'Temp_Files/IP_Analyser/Csv_Cleaner'

        # Folder with TMDB info csv files
        self.tmdb_info_folder_name = 'TMDB_csv_info'

        # API settings
        self.access_token = 'c0491fe72d2438'


    # Verify files in folder
    def FilesToProcess(self, script_path, folder_name, extension):
        
        files_to_process_folder_path = os.path.join(script_path, folder_name)

        #print(files_to_process_folder_path)

        os.chdir(files_to_process_folder_path)
        files_names_array = glob.glob('*.{}'.format(extension))

        return files_names_array, files_to_process_folder_path


    async def do_req(self, handler, ip):

        # Hide aiohttp warnings about closing the session
        logging.getLogger('asyncio').setLevel(logging.CRITICAL)

        details = await handler.getDetails(ip)

        return details



        

    # Clean the CSV files before analysis (BeforeChart)
    #   cleans NULL values from IP API scraping and incosistent type cell's values  
    def csv_cleaner(self, csv_path_input, script_path):
        
        with open(csv_path_input, 'r') as source_file:
                    
            csvFile = csv.reader(source_file)
            
            #all_rows = source_file.readlines()

            lines_to_delete = []

            all_rows_cleaned = []



            #header = all_rows[0]

            #all_rows_cleaned.append(header)
            #print(all_rows)
            i_line = -1
            
            for line in csvFile:
                i_line += 1
                columns_line_array = line

                stop =0


                if i_line == 0:
                    header = line

                    all_rows_cleaned.append(header)

                    continue

                
                for column in line:
                    if ('NULL'.lower() in str(column).lower()):
                            
                        # Remove line
                        #all_rows.pop(i_line)
                        lines_to_delete.append(i_line)
                        continue
                

                # Split line into columns to array
                #columns_line_array = line.split(',')

                #print(i_line)
                #print('\n Line: '+str(i_line)+': ' )
                #print(columns_line_array[0])
                

                if len(columns_line_array) != 22:
                    lines_to_delete.append(i_line)
                    continue

                #print(i_line)
                #print('\n Line: '+str(i_line)+': ' )
                #print(columns_line_array)

                # === progress column ===
                #   Converter para float
                if str(columns_line_array[3]) == '':
                    # Remove line
                    #all_rows.pop(i_line)
                    lines_to_delete.append(i_line)
                    continue

                try:
                    error = 0
                    progress_float = float(columns_line_array[3])
                except Exception as e:
                    error = 1
                
                if error:
                    # Remove line
                    #all_rows.pop(i_line)
                    lines_to_delete.append(i_line)
                    continue

                elif Decimal(progress_float) >= Decimal(100) and Decimal(progress_float) <= Decimal(0):
                    # Remove line
                    #all_rows.pop(i_line)
                    lines_to_delete.append(i_line)
                    continue

                # === date column ===
                if str(columns_line_array[4]) == '':
                    # Remove line
                    #all_rows.pop(i_line)
                    lines_to_delete.append(i_line)
                    continue

                try:
                    error = 0
                    date_splited_array = columns_line_array[4].split('-')
                except Exception as e:
                    error = 1
                
                if error:
                    # Remove line
                    #all_rows.pop(i_line)
                    lines_to_delete.append(i_line)
                    continue

                elif (len(date_splited_array) != 3) or (len(date_splited_array[-1]) != 4):
                    # Remove line
                    #all_rows.pop(i_line)
                    lines_to_delete.append(i_line)
                    continue

                # === hour column ===
                if str(columns_line_array[5]) == '':
                    # Remove line
                    #all_rows.pop(i_line)
                    lines_to_delete.append(i_line)
                    continue

                try:
                    error = 0
                    date_splited_array = columns_line_array[5].split(':')
                except Exception as e:
                    error = 1
                
                if error:
                    # Remove line
                    #all_rows.pop(i_line)
                    lines_to_delete.append(i_line)
                    continue

                elif len(date_splited_array) != 3:
                    # Remove line
                    #all_rows.pop(i_line)
                    lines_to_delete.append(i_line)
                    continue

                

                # === country_ISO, country columns
                if str(columns_line_array[13]) != '' or str(columns_line_array[14]) != '':
                    lines_to_delete.append(i_line)

                    #print(str(column_cell))
                    continue


                # === num_complete_by_tracker to list_peers_total columns ===
                for i_column in range(6,13):

                    column_cell = columns_line_array[i_column]

                    #print(column_cell)

                    try:
                        error = 0
                        date_splited_array = int(float(column_cell))
                    except Exception as e:
                        if i_line == 1:
                            print(e)
                        error = 1
                    
                    if error and str(column_cell) != '' and str(column_cell) != '-1':
                        # Remove line
                        #all_rows.pop(i_line)
                        lines_to_delete.append(i_line)

                        #print(str(column_cell))
                        stop = 1
                        break
                    
                    


                if stop:
                    continue

                all_rows_cleaned.append(line)


            # Supostamente elementos estao repetidos, n sei porque
            lines_to_delete = set(lines_to_delete)
            
            #print(all_rows_cleaned)

            print('    Number of lines - original file: '+str(i_line))
            print('    Number of lines - after cleaning: '+str(len(all_rows_cleaned)) ) 
            print('    Number of lines removed from the original file: '+str(len(lines_to_delete)) ) 
            print('    Lines removed from the original file:')
            print(lines_to_delete)
            
            #   Save file
        output_csv_path = os.path.join( self.temp_csv_cleaner_folder_name , csv_path_input.split('/')[-1])

        with open(output_csv_path, 'w') as output_file:
            writer = csv.writer(output_file)
            writer.writerows(all_rows_cleaned)
        '''
        output_csv_file = open(output_csv_path, 'w')
        output_csv_file.writelines(all_rows_cleaned)
        output_csv_file.close()
        '''
        
        
        return output_csv_path

    

    def TMDBInfo_Process(self, csv_name, script_path):

        files2process_array, files2process_folder_path = IP_Analyser.FilesToProcess(self, script_path, self.tmdb_info_folder_name, "csv")

        for i_file, file_name in enumerate(files2process_array):

            if  str(file_name.split('_')[-1].split('.csv')[0]) in str(csv_name):

                file_tmdb_process_path = os.path.join(files2process_folder_path, file_name)

                data_csv = pd.read_csv(file_tmdb_process_path, sep=',', encoding = 'utf-8')

                data_csv_date_array = data_csv[data_csv.columns[4]].astype(str).tolist()

                data_csv_rank_array = data_csv[data_csv.columns[5]].tolist()

                return data_csv_date_array, data_csv_rank_array


        print("  TMDB Files not found or problem with names!")

        sys.exit()

        

        







    def csv_splitter(self, csv_path_input, script_path):

        try:
            data_csv = pd.read_csv(csv_path_input, sep=',', encoding = 'utf-8')

        except FileNotFoundError:
            print("\nError! - File not found: \n  "+csv_file_path+"\n")

            sys.exit()

        # For splitting the file 
        data_torrent_n_complete = data_csv['num complete by tracker'].tolist()
        data_torrent_ip = data_csv['ip'].tolist()
        data_torrent_date = data_csv['date'].tolist()
        
        #print(data_torrent_n_complete)

        data_torrent_n_complete_nan = np.isnan(data_torrent_n_complete)


        tmdb_dates_array, tmdb_ranks_array = IP_Analyser.TMDBInfo_Process(self, csv_path_input.split('/')[-1], script_path)



        ip_temp_dict = {}

        unique_rows_array = []

        # array with lines to split the csv file with the days of the TMDB info file
        days_split_file_lines_array = []


        # === Find the rows index to split the file
        index_spliting_csv_array = []

        for i_row in range(len(data_torrent_ip)):

            # save the index to split the file
            if not data_torrent_n_complete_nan[i_row] :
                index_spliting_csv_array.append(i_row)

            ip = data_torrent_ip[i_row]

            # save lines index Unique T final/all array
            if not ip in ip_temp_dict.keys():
                ip_temp_dict[ip] = i_row
                unique_rows_array.append(i_row)

            

            # save lines index splitting by day
            if i_row == 0:
                try:
                    date_old = datetime.strptime(str(data_torrent_date[i_row]), "%d-%m-%Y")
                except ValueError:
                    print("Erro converting datetime, line: "+str(i_row))
                    sys.exit()

                days_split_file_lines_array.append(i_row)

            else:
                try:
                    date_new = datetime.strptime(str(data_torrent_date[i_row]), "%d-%m-%Y")
                except ValueError:
                    print("Erro converting datetime, line: "+str(i_row))
                    sys.exit()
                
                if (date_new > date_old) :
                    if (date_new != date_old):
                        #days_split_file_lines_array.append(i_row)

                        # Rapid solve error of date infection between files
                        days_split_file_lines_array.append(i_row+1)

                date_old = date_new


            #print("ARRAYYY: ")
            #print(days_split_file_lines_array)



        
        # === Split the file and Mkae unique file
        csv_path_splitted = csv_path_input.split('.csv')
        csv_path_splitted = csv_path_splitted[0].split('/')[-1]

        os.chdir(script_path)

        with open(csv_path_input, 'r') as source_file:

            #try:
                #source_file = open(csv_path_input, 'r')
                    
            all_rows = source_file.readlines()

            header = all_rows[0]

            # Remove the header from the rows list
            all_rows.pop(0)


            # === Make unique csv file with all different ips
            output_unique_csv_path = os.path.join( script_path, self.temp_beforechart_folder_name, csv_path_splitted+'_Unique_T_final_.csv')

            #output_unique_csv_path = script_path + self.temp_beforechart_folder_name + csv_path_splitted + '_Unique_T_final_.csv'

            output_file_unique = [header]
            for i_line in unique_rows_array:
                output_file_unique.append( all_rows[i_line] )

            #   Save file
            output_unique_csv_file = open(output_unique_csv_path, 'w+')
            output_unique_csv_file.writelines(output_file_unique)
            output_unique_csv_file.close()
            
            splitted_files_path_array = []

            splitted_files_tmdb_path_array = []

            # === Split teh csv file for each T
            for i_line in range( len(index_spliting_csv_array) ):

                if i_line == len(index_spliting_csv_array) -1:
                    line_splitt_start = index_spliting_csv_array[i_line]
                    line_splitt_end = len(all_rows)

                    #print(line_splitt_start)
                    #print(line_splitt_end)
                else:
                    line_splitt_start = index_spliting_csv_array[i_line]
                    line_splitt_end = index_spliting_csv_array[i_line+1]

                output_file = all_rows[line_splitt_start:line_splitt_end]

                output_file.insert(0, header)

                output_csv_path = os.path.join( script_path, self.temp_beforechart_folder_name, csv_path_splitted+'_Splitted_T_' + str(i_line) + '.csv')
                #output_csv_path = script_path + self.temp_beforechart_folder_name + csv_path_splitted + '_Splitted_T_' + str(i_line) + '.csv'
                #output_csv_path = csv_path_splitted[0] + '_Splitted_T_' + str(i_line) + '.csv'

                splitted_files_path_array.append(output_csv_path)

                output_csv_file = open(output_csv_path, 'w+')

                output_csv_file.writelines(output_file)
                output_csv_file.close()


            # === Split the csv file for each day in TMDB info file
            for i_line in range( len(days_split_file_lines_array)):

                if i_line == len(days_split_file_lines_array) -1:
                    line_splitt_start = days_split_file_lines_array[i_line]
                    line_splitt_end = len(all_rows)

                    #print(line_splitt_start)
                    #print(line_splitt_end)
                else:
                    line_splitt_start = days_split_file_lines_array[i_line]
                    line_splitt_end = days_split_file_lines_array[i_line+1]

                    #print(line_splitt_start)
                    #print(line_splitt_end)

                output_file = all_rows[line_splitt_start:line_splitt_end]

                output_file.insert(0, header)

                output_csv_path = os.path.join( script_path, self.temp_beforechart_folder_name, csv_path_splitted+'_Splitted_DayTMDB_' + str(i_line) + '.csv')
                #output_csv_path = script_path + self.temp_beforechart_folder_name + csv_path_splitted + '_Splitted_T_' + str(i_line) + '.csv'
                #output_csv_path = csv_path_splitted[0] + '_Splitted_T_' + str(i_line) + '.csv'

                splitted_files_tmdb_path_array.append(output_csv_path)

                output_csv_file = open(output_csv_path, 'w+')

                output_csv_file.writelines(output_file)
                output_csv_file.close()



                # Write new TMDB Columns
                data_csv_tmdb_changes = pd.read_csv(output_csv_path, sep=',', encoding = 'utf-8')
                df_tmdb_changes = pd.DataFrame(data_csv_tmdb_changes)



                data_changes_torrent_ip = data_csv_tmdb_changes['ip'].tolist()
                data_changes_torrent_date = data_csv_tmdb_changes['date'].tolist()

                day_num_complete_tracker = int(df_tmdb_changes[data_csv_tmdb_changes.columns[6]].mean())
                day_num_incomplete_tracker = int(df_tmdb_changes[data_csv_tmdb_changes.columns[7]].mean())
                day_num_complete_conn = int(df_tmdb_changes[data_csv_tmdb_changes.columns[8]].mean())
                day_num_seeds_conn = int(df_tmdb_changes[data_csv_tmdb_changes.columns[9]].mean())
                day_num_peers_conn = int(df_tmdb_changes[data_csv_tmdb_changes.columns[10]].mean())
                day_seeds_total = int(df_tmdb_changes[data_csv_tmdb_changes.columns[11]].mean())
                day_peers_total = int(df_tmdb_changes[data_csv_tmdb_changes.columns[12]].mean())

                df_tmdb_changes.loc[:, data_csv_tmdb_changes.columns[6]+' (day)'] = ''
                df_tmdb_changes.loc[0, data_csv_tmdb_changes.columns[6]+' (day)'] = day_num_complete_tracker

                df_tmdb_changes.loc[:, data_csv_tmdb_changes.columns[7]+' (day)'] = ''
                df_tmdb_changes.loc[0, data_csv_tmdb_changes.columns[7]+' (day)'] = day_num_incomplete_tracker

                df_tmdb_changes.loc[:, data_csv_tmdb_changes.columns[8]+' (day)'] = ''
                df_tmdb_changes.loc[0, data_csv_tmdb_changes.columns[8]+' (day)'] = day_num_complete_conn

                df_tmdb_changes.loc[:, data_csv_tmdb_changes.columns[9]+' (day)'] = ''
                df_tmdb_changes.loc[0, data_csv_tmdb_changes.columns[9]+' (day)'] = day_num_seeds_conn

                df_tmdb_changes.loc[:, data_csv_tmdb_changes.columns[10]+' (day)'] = ''
                df_tmdb_changes.loc[0, data_csv_tmdb_changes.columns[10]+' (day)'] = day_num_peers_conn

                df_tmdb_changes.loc[:, data_csv_tmdb_changes.columns[11]+' (day)'] = ''
                df_tmdb_changes.loc[0, data_csv_tmdb_changes.columns[11]+' (day)'] = day_seeds_total

                df_tmdb_changes.loc[:, data_csv_tmdb_changes.columns[12]+' (day)'] = ''
                df_tmdb_changes.loc[0, data_csv_tmdb_changes.columns[12]+' (day)'] = day_peers_total


                # Remove duplicated IPs
                temp_ip_tmdb_dict = {}
                rows_remove_tmdb_changes = []

                

                for i_cell, cell_ip in enumerate(data_changes_torrent_ip):

                     # save lines index Unique T final/all array
                    if cell_ip in temp_ip_tmdb_dict.keys():
                        rows_remove_tmdb_changes.append(i_cell)
                    else:
                        temp_ip_tmdb_dict[cell_ip] = i_row

                df_tmdb_changes = df_tmdb_changes.drop(index=rows_remove_tmdb_changes)

                '''
                # Date mode in files
                rows_remove_tmdb_changes = []
                date_mode = df_tmdb_changes.loc[:, 'date'].mode()

                for i_cell, cell_date in enumerate(df_tmdb_changes.loc[:, 'date'].List()):

                    # Remove possible error with dates infection between files
                    if str(cell_date) != str(date_mode):
                        rows_remove_tmdb_changes.append(i_cell)
                
                if len(rows_remove_tmdb_changes) > 1:
                    df_tmdb_changes = df_tmdb_changes.drop(index=rows_remove_tmdb_changes)


                '''
                df_tmdb_changes.to_csv( output_csv_path, mode='w', index=False, header=True )
                

            return splitted_files_path_array, output_unique_csv_path, splitted_files_tmdb_path_array

            #except Exception as e:
            #    print(e)

            #    sys.exit()


        

        


    def chartsData(self, splitted_paths, unique_path, splitted_paths_tmdb, script_path):
        
        #for i_path, path in enumerate(splitted_paths):

        
        data_csv = pd.read_csv(unique_path, sep=',', encoding = 'utf-8')


        n_table_chart = 6

        for i_table in range(n_table_chart):

            # ==== countries
            if i_table == 0:
                # name ouput file
                name_file = 'Country'

                # === Analyse countries
                data_torrent_countries = data_csv[name_file].astype(str).tolist()

                countries_set = list(set(data_torrent_countries))
                # Remove NaN values
                countries_set = [x for x in countries_set if x.lower() != 'nan']

                '''
                print("\n LIST SET:")
                print(countries_set)
                print("\n")
                '''
                countries_values_array = []

                counts = Counter(data_torrent_countries)
                '''
                print("\n COUNTS:")
                print(counts)
                print("\n")
                '''

                for i_country, country in enumerate(countries_set):
                    # Remove NaN values
                    if country.lower() != 'nan':
                        countries_values_array.append( counts[country] )


                df = pd.DataFrame({'Country': countries_set,
                                'Number of IPs': countries_values_array, 
                                })

                df = df.sort_values(by = df.columns[1], ascending=False)


            # ==== organizations (ISPs)
            if i_table == 1:

                # name ouput file
                name_file = 'Organization'

                # === Analyse countries
                data_torrent_org = data_csv[name_file].astype(str).tolist()

                org_set = list(set(data_torrent_org))
                # Remove NaN values
                org_set = [x for x in org_set if x.lower() != 'nan']

                countries_values_array = []

                counts = Counter(data_torrent_org)

                for i_country, org in enumerate(org_set):
                    # Remove NaN values
                    if org.lower() != 'nan':
                        countries_values_array.append( counts[org] )


                df = pd.DataFrame({'Organizations (ISPs)': org_set,
                                'Number of IPs': countries_values_array, 
                                })

                df = df.sort_values(by = df.columns[1], ascending=False)


            # ==== Client torrent program
            if i_table == 2:

                # name ouput file
                name_file = 'client'

                # === Analyse countries
                data_torrent_client = data_csv[name_file].astype(str).tolist()

                # Solve client names bugs
                for i_x, x in enumerate(data_torrent_client):

                    # Because appears to be two exact names
                    if x == 'µTorrent': 
                        data_torrent_client[i_x] = 'μTorrent'

                    if x == 'uTorrent': 
                        data_torrent_client[i_x] = 'μTorrent'

                    if x == 'Unknown': 
                        data_torrent_client[i_x] = '--Unknown_Unidentifiable--'

                    if x == '': 
                        data_torrent_client[i_x] = '--Unknown_Unidentifiable--'

                

                clients_set = list(set(data_torrent_client))
                # Remove NaN values
                clients_set = [x for x in clients_set if x.lower() != 'nan']

                '''
                print("\n LIST SET:")
                print(clients_set)
                print("\n")
                '''
                countries_values_array = []

                counts = Counter(data_torrent_client)
                '''
                print("\n COUNTS:")
                print(counts)
                print("\n")
                '''

                for i_country, country in enumerate(clients_set):
                    # Remove NaN values
                    if country.lower() != 'nan':
                        countries_values_array.append( counts[country] )


                df = pd.DataFrame({'Torrent Client App': clients_set,
                                'Number of IPs': countries_values_array, 
                                })

                df = df.sort_values(by = df.columns[1], ascending=False)


            # ==== Popularity (TMDB) vs Columns G to M
            if i_table == 3:

                # name ouput file
                name_file = 'PopularityByDay'

                date = []
                n_c_tracker = []
                n_i_tracker = []
                n_c_c = []
                n_s_c = []
                n_p_c = []
                s_t = []
                p_t = []

                for i_path, path in enumerate(splitted_paths_tmdb):

                    data_csv_tmdb = pd.read_csv(path, sep=',', encoding = 'utf-8')

                    df_tmdb_changes = pd.DataFrame(data_csv_tmdb)

                    date.append(df_tmdb_changes.loc[0, data_csv_tmdb.columns[4]])
                    n_c_tracker.append(df_tmdb_changes.loc[0, data_csv_tmdb.columns[22]])
                    n_i_tracker.append(df_tmdb_changes.loc[0, data_csv_tmdb.columns[23]])
                    n_c_c.append(df_tmdb_changes.loc[0, data_csv_tmdb.columns[24]])
                    n_s_c.append(df_tmdb_changes.loc[0, data_csv_tmdb.columns[25]])
                    n_p_c.append(df_tmdb_changes.loc[0, data_csv_tmdb.columns[26]])
                    s_t.append(df_tmdb_changes.loc[0, data_csv_tmdb.columns[27]])
                    p_t.append(df_tmdb_changes.loc[0, data_csv_tmdb.columns[28]])


                # read TMDB Info files
                tmdb_info_files_array,  tmdb_info_folder_path = IP_Analyser.FilesToProcess(self, script_path, os.path.join(script_path, self.tmdb_info_folder_name), "csv")

                for i_file, tmdb_info_name in enumerate( tmdb_info_files_array ):

                    if tmdb_info_name.split('.csv')[0].split('_')[-1] in splitted_paths_tmdb[0]:

                        #data_csv_date_array, data_csv_rank_array = TMDBInfo_Process(self, csv_name, script_path)


                        data_csv_tmdb_info = pd.read_csv( os.path.join(tmdb_info_folder_path, tmdb_info_name), sep=',', encoding = 'utf-8')

                        df_tmdb = pd.DataFrame(data_csv_tmdb_info)

                        dates_tmdb_info = data_csv_tmdb_info[ data_csv_tmdb_info.columns[4] ].tolist()
                        #rank_tmdb_info = data_csv_tmdb_info[ data_csv_tmdb_info.columns[5] ].tolist()

                        remove_lines_tmdb_info_dates = []

                        for i_cell, cell in enumerate(dates_tmdb_info):

                            if not str(cell) in date:
                                remove_lines_tmdb_info_dates.append(i_cell)

                                #rank_tmdb_info2 = rank_tmdb_info.pop(i_cell)

                        df_tmdb = df_tmdb.drop(index=remove_lines_tmdb_info_dates)

                        rank_tmdb_info = df_tmdb.loc[:,data_csv_tmdb_info.columns[5]]

                
                df = pd.DataFrame({'Date': date,
                                'Rank': rank_tmdb_info,
                                'N Complete by Tracker': n_c_tracker, 
                                'N Inomplete by Tracker': n_i_tracker, 
                                'N Complete Connected': n_c_c,
                                'N Seeds Connected': n_s_c,
                                'N Peers Connected': n_p_c,
                                'N Seeds Total': s_t,   
                                'N Peers Total': p_t, 
                                })

            # ==== Client vs Countries vs number of IPs
            if i_table == 4:

                name_file='ClientCountries'

                
                # === Analyse
                data_torrent_client = data_csv['client'].astype(str).tolist()
                data_torrent_countries = data_csv['Country'].astype(str).tolist()

                # Dict with Countrie's name keys and array values in order of clients_set
                aux_dict = {}

                # Count number of clients per country
                for i_x, x in enumerate(data_torrent_client):

                    if x.lower() == 'nan':
                        continue

                    # Because appears to be two exact names
                    if x == 'µTorrent': 
                        x = 'μTorrent'

                    if x == 'uTorrent': 
                        x = 'μTorrent'

                    if x == 'Unknown': 
                        x = '--Unknown_Unidentifiable--'

                    if x == '': 
                        x = '--Unknown_Unidentifiable--'


                    country = data_torrent_countries[i_x]
                    if country.lower() == 'nan':
                        continue


                    if not country in aux_dict.keys():
                        
                        array_aux_dict_values = []
                        for i_client, client in enumerate(clients_set):

                            #print("============== Comparar: "+client+" ; "+x)
                            if client == x:
                                array_aux_dict_values.append(1)


                            else:
                                array_aux_dict_values.append(0)
                    
                    else:
                        
                        array_aux_dict_values = aux_dict[country]
                        for i_client, client in enumerate(clients_set):
                            if client == x:
                                array_aux_dict_values[i_client] = array_aux_dict_values[i_client] + 1

                    
                    aux_dict[country] = array_aux_dict_values

                
                # Initialize arrays to export to pandas dataframe
                array_output_keys = []

                # Initialize arrays to export to pandas dataframe
                for i_client, client in enumerate(clients_set):
                    exec( 'array_output_client%s = []' % (str(i_client) ) )

                # Append arrays 
                for i_key, key in enumerate(aux_dict.keys()):

                    array_output_keys.append(key)

                    for i_client, client in enumerate(clients_set):
                        exec( 'array_output_client%s.append( aux_dict["%s"][%d] )' % (str(i_client), key, i_client) )


                # Insert into dataframe
                df = pd.DataFrame({'Countries': array_output_keys 
                                })

                # Insert into dataframe
                for i_client, client in enumerate(clients_set):
                        exec( 'df["%s"] = array_output_client%s' % (client, str(i_client)) )

                
                # Order by sum
                array_columns_name = list(df)
                array_columns_name.pop(0)

                #print(array_columns_name)
                df['Sum_of_row'] = df.loc[:,array_columns_name].sum(axis = 1)

                df = df.sort_values(by ='Sum_of_row', ascending=False)




            # ==== organizations (ISPs) vs Countries vs number of IPs
            if i_table == 5:

                name_file='OrganizationCountries'

                #==================================================================
                    # ==== organizations (ISPs)
                if i_table == 1:

                    # name ouput file
                    name_file = 'Organization'

                    # === Analyse countries
                    data_torrent_countries = data_csv[name_file].astype(str).tolist()

                    countries_set = list(set(data_torrent_countries))
                    # Remove NaN values
                    countries_set = [x for x in countries_set if x.lower() != 'nan']

                    '''
                    print("\n LIST SET:")
                    print(countries_set)
                    print("\n")
                    '''
                    countries_values_array = []

                    counts = Counter(data_torrent_countries)
                    '''
                    print("\n COUNTS:")
                    print(counts)
                    print("\n")
                    '''

                    for i_country, country in enumerate(countries_set):
                        # Remove NaN values
                        if country.lower() != 'nan':
                            countries_values_array.append( counts[country] )


                    df = pd.DataFrame({'Organizations (ISPs)': countries_set,
                                    'Number of IPs': countries_values_array, 
                                    })

                    df = df.sort_values(by = df.columns[1], ascending=False)


                #====================================================================

                
                # === Analyse
                data_torrent_org = data_csv['Organization'].astype(str).tolist()
                data_torrent_countries = data_csv['Country'].astype(str).tolist()

                # Dict with Countrie's name keys and array values in order of org_set
                aux_dict = {}

                # Count number of clients per country
                for i_x, x in enumerate(data_torrent_org):

                    if x.lower() == 'nan':
                        continue

                    country = data_torrent_countries[i_x]
                    if country.lower() == 'nan':
                        continue


                    if not country in aux_dict.keys():
                        
                        array_aux_dict_values = []
                        for i_org, org in enumerate(org_set):

                            if org == x:
                                array_aux_dict_values.append(1)
                            else:
                                array_aux_dict_values.append(0)
                    else:
                        
                        array_aux_dict_values = aux_dict[country]
                        for i_org, org in enumerate(org_set):
                            if org == x:
                                array_aux_dict_values[i_org] = array_aux_dict_values[i_org] + 1

                    
                    aux_dict[country] = array_aux_dict_values

                
                # Initialize arrays to export to pandas dataframe
                array_output_keys = []

                # Initialize arrays to export to pandas dataframe
                for i_org, org in enumerate(org_set):
                    exec( 'array_output_client%s = []' % (str(i_org) ) )

                # Append arrays 
                for i_key, key in enumerate(aux_dict.keys()):

                    array_output_keys.append(key)

                    for i_org, org in enumerate(org_set):
                        exec( 'array_output_client%s.append( aux_dict["%s"][%d] )' % (str(i_org), key, i_org) )


                # Insert into dataframe
                df_1 = pd.DataFrame({'Countries': array_output_keys 
                                })

                # Insert into dataframe
                array_new_columns = []
                dict_new_dataframe = {}
                for i_org, org in enumerate(org_set):
                    # Better execution time
                    exec( 'dict_new_dataframe["%s"] = array_output_client%s' % (org, str(i_org)) )

                df_2 = pd.DataFrame(dict_new_dataframe)
                df = pd.concat([df_1, df_2], axis = 1) 


                # Order by sum
                array_columns_name = list(df)
                array_columns_name.pop(0)

                #print(array_columns_name)
                df['Sum_of_row'] = df.loc[:,array_columns_name].sum(axis = 1)

                df = df.sort_values(by ='Sum_of_row', ascending=False)

                


            csv_path_splitted = unique_path.split('.csv')
            csv_path_splitted = csv_path_splitted[0].split('/')[-1]

            output_csv_path = os.path.join( script_path, ChartsEditor.ChartsEditor().input_folder_name, csv_path_splitted+'__Static_T_all_'+name_file+'.csv')

            #output_csv_path = script_path + csv_path_splitted[0] + '__Chart_Country.csv'


            df.to_csv(output_csv_path, mode='w', index=False, header=True)

        



    # Only for Linux systems
    def clearTerminal():
        os.system('tput reset')


    def main(self):

        # Ask 
        option = input("\nWhat do you want to do?\n  Analyse IPs (from API requests) = 1\n  Make the charts = 2\n  (1 or 2)? ")




        # Analyse IPs Geo
        if option == '1':

            keys_dict_example_array = ['Organization', 'time zone', 'Country', 'Latitude', 'Longitude', 'Region', 'City']


            fieldnames_output_csv = [
                'ip', 'client','version','progress %','date','hour','num complete by tracker',
                'num incomplete by tracker','num complete connected','num seeds connected',
                'num peers connected','list seeds total','list peers total',keys_dict_example_array[0],
                keys_dict_example_array[1], keys_dict_example_array[2], keys_dict_example_array[3],
                keys_dict_example_array[4], keys_dict_example_array[5], keys_dict_example_array[6]
                ]

            # api response vars, name of lists to panda csv
            api_fields = ['org','timezone','country_name','latitude','longitude','region','city']


            current_path = os.getcwd()

            files2process_array, files2process_folder_path = IP_Analyser.FilesToProcess(self, current_path, self.input_folder_name, "csv")
            
            os.chdir(current_path)


            session_start_time = datetime.now()


            api_handler = ipinfo.getHandlerAsync(self.access_token, request_options={'timeout': 10})


            files2process_path_array = []
            csv_export_file_path_array = []

            # Main loop
            for i_csv_file_path, file2process_name in enumerate(files2process_array):

                files2process_path_array.append(os.path.join( files2process_folder_path, file2process_name ))

                csv_file_path = files2process_path_array[i_csv_file_path]

                # Output files
                path_splited = file2process_name.split('.csv')
                csv_export_file_path_array.append(os.path.join( current_path, self.output_folder_name, path_splited[0] + '_Analysed.csv' ))

                # para comparar com os ips ja verificados, poupar querys
                temp_dict = {}

                # Inialize lists
                '''
                for i in range(len(api_fields)):
                    exec("%s_array = []" % ( api_fields[i] ))
                '''
                organization_array = []
                timezone_array = []
                country_array = []
                latitude_array = []
                longitude_array = []
                region_array = []
                city_array = []
                

                data_csv = pd.read_csv(csv_file_path, sep=',', encoding = 'utf-8')

                data_torrent_ip_array = data_csv[ fieldnames_output_csv[0] ].tolist()
                data_torrent_client_array = data_csv[ fieldnames_output_csv[1] ].tolist()
                data_torrent_version_array = data_csv[ fieldnames_output_csv[2] ].tolist()
                data_torrent_progress_array = data_csv[ fieldnames_output_csv[3] ].tolist()
                data_torrent_date_array = data_csv[ fieldnames_output_csv[4] ].tolist()
                data_torrent_hour_array = data_csv[ fieldnames_output_csv[5] ].tolist()
                data_torrent_ncumtracker_array = data_csv[fieldnames_output_csv[6]].tolist()
                '''
                data_torrent_nincumtracker_array = data_csv[fieldnames_output_csv[7]].tolist()
                data_torrent_ncumconn_array = data_csv[fieldnames_output_csv[8]].tolist()
                data_torrent_nseedsconn_array = data_csv[fieldnames_output_csv[9]].tolist()
                data_torrent_npeersconn_array = data_csv[fieldnames_output_csv[10]].tolist()
                data_torrent_nseedstot_array = data_csv[fieldnames_output_csv[11]].tolist()
                data_torrent_npeerstot_array = data_csv[fieldnames_output_csv[12]].tolist()
                '''

                remove_lines_array = []
          
                for i_ip, ip in enumerate(data_torrent_ip_array):

                    if data_torrent_ip_array[i_ip] == '' or data_torrent_progress_array[i_ip] == '' or data_torrent_date_array[i_ip] == '' or data_torrent_hour_array[i_ip] == '':

                        remove_lines_array.append(i_ip)

                        continue # skip

                    else:

                        if not ip in temp_dict.keys():

                            try:
                            
                                loop = asyncio.get_event_loop()

                                apiresponse = loop.run_until_complete(IP_Analyser.do_req(self, api_handler, ip))

                                #pprint.pprint(res.region)
                                '''
                                for i in range(len(api_fields)):
                                    eval('temp_dict["%s"][%d].append(apiresponse.%s)' % (ip, i, api_fields[i] ))

                                    exec('%s_array.append( temp_dict["%s"][%d] )' % ( api_fields[i], ip, i ), {'temp_dict': temp_dict})
                                '''

                                temp_dict[ip] = [
                                                apiresponse.org, 
                                                apiresponse.timezone, 
                                                apiresponse.country_name, 
                                                apiresponse.latitude, 
                                                apiresponse.longitude, 
                                                apiresponse.region,
                                                apiresponse.city 
                                                ]

                            except Exception as e:
                            
                                temp_dict[ip] = [
                                                'NULL', 
                                                'NULL', 
                                                'NULL', 
                                                'NULL', 
                                                'NULL', 
                                                'NULL',
                                                'NULL' 
                                                ]
                        
                        
                    organization_array.append( temp_dict[ip][0] )
                    timezone_array.append( temp_dict[ip][1] )
                    country_array.append( temp_dict[ip][2] )
                    latitude_array.append( temp_dict[ip][3] )
                    longitude_array.append( temp_dict[ip][4] )
                    region_array.append( temp_dict[ip][5] )
                    city_array.append( temp_dict[ip][6] )
                        

                    # Print
                    if i_ip % 10 == 0:

                        session_elapse_time = datetime.now() - session_start_time
                        session_elapse_time_witho_sec = str(session_elapse_time).split(".")[0]

                        progress = float(((i_ip+1) * 100)/len(data_torrent_ip_array))
                        progres_p_f = float(((i_csv_file_path+1) * 100)/len(files2process_array)) 
                        IP_Analyser.clearTerminal()

                        print("\nIP Scraping, Session, start at: {:s}, running time: {:s}  \n  Progress per File: {:.2f}% ({:d}/{:d}), Progress per IP: {:.2f}%"
                            .format( session_start_time.strftime("%d-%m-%Y/%H:%M:%S"), session_elapse_time_witho_sec, progres_p_f, i_csv_file_path+1,len(files2process_array), progress) )
                            

                '''
                df = pd.DataFrame({
                                keys_dict_example_array[0]: organization_array, 
                                keys_dict_example_array[1]: timezone_array , 
                                keys_dict_example_array[2]: country_array,
                                keys_dict_example_array[3]: latitude_array, 
                                keys_dict_example_array[4]: longitude_array ,
                                keys_dict_example_array[5]: region_array,
                                keys_dict_example_array[6]: city_array
                                })
                '''
                
                # Remove lines
                df = pd.DataFrame(data_csv)
                #   FutureWarning: In a future version of pandas all arguments of DataFrame.drop except for the argument 'labels' will be keyword-only.
                df.drop(remove_lines_array,0,inplace=True)

                # Save and export the processed info
                data_csv[ keys_dict_example_array[0] ] = organization_array
                data_csv[ keys_dict_example_array[1] ] = timezone_array
                data_csv[ keys_dict_example_array[2] ] = country_array
                data_csv[ keys_dict_example_array[3] ] = latitude_array
                data_csv[ keys_dict_example_array[4] ] = longitude_array
                data_csv[ keys_dict_example_array[5] ] = region_array
                data_csv[ keys_dict_example_array[6] ] = city_array

                data_csv.to_csv( csv_export_file_path_array[i_csv_file_path], mode='a', index=False, header=True )


                print("\nDone for the file! \n  {:s}\n".format( file2process_name ))
                session_elapse_time = datetime.now() - session_start_time
                session_elapse_time_witho_sec = str(session_elapse_time).split(".")[0]

                # Log file
                with open('LOG-IP_Analysis.log', 'a+') as log_file:
                    log_file.writelines(['\n\n',str(datetime.now()),'\nFile: '+str(file2process_name), '\n   Time to finish:'+str(session_elapse_time_witho_sec)+'\n'])




        elif option == '2':

            current_path = os.getcwd()

            files2process_array, files2process_folder_path = IP_Analyser.FilesToProcess(self, current_path, self.output_folder_name, "csv")
            
            os.chdir(current_path)

            files2process_path_array = []

            for i_csv_file_path, file2process_name in enumerate(files2process_array):
                os.chdir(current_path)

                files2process_path_array.append(os.path.join( files2process_folder_path, file2process_name ))

                #path_splited = csv_file_path.split('.csv')
                #csv_file_path = path_splited[0] + '_Analysed.csv'

                print("\n Start CSV cleaning\n   for the file:  {:s}\n".format( file2process_name ))
                cleaned_csv_path = IP_Analyser.csv_cleaner(self, files2process_path_array[i_csv_file_path], current_path)

                print("\n   CSV File cleaned!\n   for the file:  {:s}\n".format( file2process_name ))

                #sys.exit()
                    
                print("\n Start CSV spliting\n   for the file:  {:s}\n".format( file2process_name ))
                splitted_files_path_array, output_unique_csv_path, splitted_files_tmdb_path_array = IP_Analyser.csv_splitter(self, cleaned_csv_path, current_path)

                print("\n  Spliting file Done! \n   for the file:  {:s}\n".format( file2process_name ))

                print("\n Start preparation before make the charts\n   for the file:  {:s}\n".format( file2process_name ))
                IP_Analyser.chartsData(self, splitted_files_path_array, output_unique_csv_path, splitted_files_tmdb_path_array, current_path)

                print("\n   BeforeChart File Preparation Done! \n   for the file:  {:s}\n".format( file2process_name ))


            os.chdir(current_path)
            charts_maker = ChartsEditor.ChartsEditor().main()





        sys.exit()


if __name__ == "__main__":
    app = IP_Analyser()
    app.main()

