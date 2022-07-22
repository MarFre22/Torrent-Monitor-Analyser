#!/usr/bin/env python3

from email import header
from operator import length_hint
from elasticsearch import Elasticsearch
from countryinfo import CountryInfo
import libtorrent as lt
import geoip2.database
from tabulate import tabulate
from datetime import date, datetime

import argparse
import time
import csv 
import sys
import os 
import uuid
from collections import deque
import pandas as pd

class torrent_monitor:

    handle_modifier_flag = 0


    def __init__(self, torrents_input, output, elastic, geo, time, save_folder, fast_resume_folder, add_batch_folder):
        self.torrents_input = torrents_input
        self.output = output
        self.elastic = elastic
        self.geo = geo
        self.time = time
        self.save_folder = save_folder
        self.fast_resume_folder = fast_resume_folder
        self.fast_resume_file_name = "fastResumeFile.csv"
        self.add_batch_folder = add_batch_folder
        self.add_batch_file_name = "addBatch.csv"
        self.fieldnames_temp_csv = ['ID','File Path .torrent','Download Folder Path', 'Output Folder Path', 'Start Time']
        self.fieldnames_output_csv = ['ip', 'client','version','progress %','date','hour','num complete by tracker','num incomplete by tracker','num complete connected','num seeds connected','num peers connected','list seeds total','list peers total','countryISO','country']
        self.session_start_time = ''

        settings = {
            'user_agent': '',
            'listen_interfaces': '0.0.0.0:6881',
            'download_rate_limit': 10000,
            'upload_rate_limit': 0,
            'connections_limit': 50000,
            'max_peerlist_size': 50000,
            'active_limit': 2000,
            'active_seeds': 50000,
            'alert_mask': lt.alert.category_t.all_categories,
            'outgoing_interfaces': '',
            'announce_to_all_tiers': True,
            'announce_to_all_trackers': True,
            'auto_manage_interval': 5,
            'auto_scrape_interval': 0,
            'auto_scrape_min_interval': 0,
            'max_failcount': 1,
            'aio_threads': 8,
            'checking_mem_usage': 2048,
        }

        # Definir sessão Libtorrent com as settings acima
        self.ses = lt.session(settings)

        self.session_start_time = datetime.now()


    def size_converter(self, size):
        if size < 10**6:
            mb = size / 10**3
            return "{:.2f}KB".format(mb)
        elif size > 10**6 and size < 10**9:
            mb = size / 10 ** 6
            return "{:.2f}MB".format(mb)
        elif size > 10 ** 9:
            mb = size / 10 ** 9
            return "{:.2f}GB".format(mb)

    '''
    def save_elasticsearch_es(self, index, data):
        es = Elasticsearch(hosts="localhost:9200")

        es.indices.create(
            index=index,
            ignore=400  # ignore 400 already exists code
        )
        id_case = str(datetime.strptime(data['date'], "%Y-%m-%d")) + \
            '-'+data['ip']
        es.update(index=index, id=id_case, body={'doc':data,'doc_as_upsert':True})
    '''
    
    def pause_session(session, handles_array):
        for handle in handles_array:
            if not handle.is_valid() or not handle.has_metadata():
                continue
            data = lt.bencode(handle.write_resume_data())
            filename = os.path.join(
                handle.get_torrent_info().name() + '.fastresume')
            with open(filename, 'wb') as fresume:
                fresume.write(data)
    
    
    def torrentState(self, handle_status):
        switch = {
            1: "Checking existing files",
            2: "Downloading metadata",
            3: "Downloading",
            4: "Finished",
            5: "Seeding",
            6: "Disk storage allocated",
            7: "Checking resume data"
        }
        return switch.get(handle_status,"?")
    
    def addTorrent(self, op, handles_array, fast_resume_dict, array_first_torrent, batch_temp_dict):
        # op = 0; add torrents on program's start
        # op = 1; add torrents into the main while loop

        global handle_modifier_flag

        if op == 0:
            handles_array = []

        if len(array_first_torrent) == 0:
            
            if op == 0:
                for torrentID in fast_resume_dict:
                    
                    dot_torrent_file = fast_resume_dict[torrentID][0]
                    save_folder = fast_resume_dict[torrentID][1]
                    
                    '''
                    # Link magnet ou ficheiro .torrent
                    if torrent.startswith('magnet:'):
                        atp = lt.add_torrent_params()
                        atp = lt.parse_magnet_uri(torrent)
                        atp.save_path = '.'
                        h = self.ses.add_torrent(atp)
                    ''' 
                        
                    
                    info = lt.torrent_info(dot_torrent_file)
                    h = self.ses.add_torrent({'ti': info, 'save_path': save_folder})
                    
                    handles_array.append(h)
                    
                    print_messange = "\nFastResume torrent added: "+torrentID
                    print_messange2 = print_messange[:45]
                    print(print_messange2+"...")

            elif op == 0 or op == 1:
                for i in range(len(batch_temp_dict)):
                    info = lt.torrent_info(batch_temp_dict[i][0])
                    h = self.ses.add_torrent({'ti': info, 'save_path': batch_temp_dict[i][1]})
                    
                    handles_array.append(h)
                
                    fast_resume_dict, torrentID = torrent_monitor.handles2Dict(self, 1, handles_array, fast_resume_dict, batch_temp_dict[i])

                    print_messange = "\nBatch torrent added: "+torrentID
                    print_messange2 = print_messange[:45]
                    print(print_messange2+"...")
          
        else:
            info = lt.torrent_info(array_first_torrent[0])
            h = self.ses.add_torrent({'ti': info, 'save_path': array_first_torrent[1]})
                
            handles_array.append(h)
            
            fast_resume_dict, torrentID = torrent_monitor.handles2Dict(self, 0, handles_array, fast_resume_dict, array_first_torrent)
            
            for torrentID in fast_resume_dict:
                print_messange = "\nAdding first torrent: "+torrentID
                print_messange2 = print_messange[:45]
                print(print_messange2+"...")
            
        
        handle_modifier_flag = 1

        return handles_array, fast_resume_dict


    
    def handles2Dict(self, op, handles_array, dict, values_array):
        # op = 0: all handles
        # op = 1: only the last handle
        
        if op:
            handle_hash = torrent_monitor.handleHash(self, handles_array[-1])
            
            if handle_hash not in dict:
                dict[handle_hash] = values_array

        else:
            for handle in handles_array:
                
                handle_hash = torrent_monitor.handleHash(self, handle)
                
                if handle_hash not in dict:
                    dict[handle_hash] = values_array
                
        return dict, handle_hash
            

    def handleHash(self, handle):
         
        handle_stat = handle.status()
            
        handle_hash = uuid.uuid5(uuid.NAMESPACE_DNS, handle_stat.name)

        handle_hash_str = handle_hash.urn

        handle_hash_str = handle_hash_str[9:]
            
        return handle_hash_str
    
    
    def fastResumeInit(self):
        
        fast_resume_path_file = os.path.join(self.fast_resume_folder, self.fast_resume_file_name)
        fast_resume_dict = {}
        
        
        # Create Fast Resume File and header
        if not os.path.exists(fast_resume_path_file):
            f_resume = open(fast_resume_path_file, 'a+')
            writer = csv.DictWriter(f_resume, fieldnames=self.fieldnames_temp_csv)
            writer.writeheader()
            
            f_resume.close()
        
        # Read Fast Resume File to dict
        else:

            data_csv = pd.read_csv(fast_resume_path_file)

            data_torrentID = data_csv['ID'].tolist()
            data_filePath = data_csv['File Path .torrent'].tolist()
            data_downPath = data_csv['Download Folder Path'].tolist()
            data_outPath = data_csv['Output Folder Path'].tolist()

            for i_line in range(len(data_torrentID)):
                fast_resume_dict[data_torrentID[i_line]] = [ data_filePath[i_line], data_downPath[i_line], data_outPath[i_line] ]

                    
        return fast_resume_dict, fast_resume_path_file


    def fastResumeAdd(self, dict, file_path):
         
        if os.path.exists(file_path):

            data_csv = pd.read_csv(file_path)

            data_torrentID = data_csv['ID'].tolist()

            f_resume = open(file_path, 'a+')

            
            writer = csv.DictWriter(f_resume, fieldnames=self.fieldnames_temp_csv)

            for torrentID in dict:

                if not torrentID in data_torrentID:

                    writer.writerow({'ID': torrentID,'File Path .torrent': dict[torrentID][0], 'Download Folder Path': dict[torrentID][1],  
                                'Output Folder Path': dict[torrentID][2] })
                            

            f_resume.close()


    def addBatch(self, op):
        # op = 0: analyse add_batch file
        # op = 1: clean add_batch file

        add_batch_path_file = os.path.join(self.add_batch_folder, self.add_batch_file_name)

        batch_temp_dict = {}

        if not os.path.exists(add_batch_path_file) or op == 1:
            f_add_batch = open(add_batch_path_file, 'w')
            writer = csv.DictWriter(f_add_batch, fieldnames=self.fieldnames_temp_csv)
            writer.writeheader()
            
            f_add_batch.close()

        else:
            data_csv = pd.read_csv(add_batch_path_file)

            data_filePath = data_csv['File Path .torrent'].tolist()
            data_downPath = data_csv['Download Folder Path'].tolist()
            data_outPath = data_csv['Output Folder Path'].tolist()

            for i_line in range(len(data_filePath)):
                batch_temp_dict[i_line] = [ data_filePath[i_line], data_downPath[i_line], data_outPath[i_line] ]

        return batch_temp_dict


    # Only for Linux systems
    def clearTerminal():
        os.system('tput reset')
            

    def main(self):
        
        global handle_modifier_flag

        # Verify Fast Resume file
        fast_resume_dict, fast_resume_path_file = torrent_monitor.fastResumeInit(self)
        
        array_first_torrent = []
        
        if not fast_resume_dict:    # fast_resume_dict is empty
            
            # Ask to input the first torrent
            print("\n=== There isn't any torrent, add thre first one :)\n")
            
            #dot_torrent_file_input = input(".torrent file path:\n")
            dot_torrent_file_input = '/home/lm-vm/Documentos/Github-Projects/Torrent-Analysis-LECProject/Murcao-TorrentMonitor/Moonfall.2022.1080p.WEBRip.x264-RARBG-[rarbg.to].torrent'
            #dot_torrent_file_input = dot_torrent_file_input.replace("'", "")
            
            #download_folder_input = input("download folder path:\n")
            download_folder_input = '/home/lm-vm/Documentos/Projeto_Licenciatura/DownloadedFiles'
            #download_folder_input = download_folder_input.replace("'", "")
            
            #output_folder_input = input("analysis folder path\n")
            output_folder_input = '/home/lm-vm/Documentos/Projeto_Licenciatura/OuputFiles'
            #output_folder_input = output_folder_input.replace("'", "")
            
            array_first_torrent = [dot_torrent_file_input, download_folder_input, output_folder_input]


        batch_temp_dict = torrent_monitor.addBatch(self, 0)


        # Adicionar torrent inicial ou adicionar torrentes do fast_resume
        handles_array, fast_resume_dict = torrent_monitor.addTorrent(self, 0, [], fast_resume_dict, array_first_torrent, batch_temp_dict)
        
        
        
        table_header = ['Name', 'Progress %', 'Downloaded', 'Down Rate', 'Up Rate',
                        'State','Peers Instant', 'Saving Peers']

        files_csv_array = []
        
        try:
        
            while True:
                table_torrents_info_array = []


                batch_temp_dict = torrent_monitor.addBatch(self, 0)

                n_handles_array = len(handles_array)

                if batch_temp_dict:
                    handles_array, fast_resume_dict = torrent_monitor.addTorrent(self, 1, handles_array, fast_resume_dict, array_first_torrent, batch_temp_dict)

                    if n_handles_array < len(handles_array):
                        batch_temp_dict = torrent_monitor.addBatch(self, 1)


                if handle_modifier_flag :
                    torrent_monitor.fastResumeAdd(self, fast_resume_dict, fast_resume_path_file)

                    handle_modifier_flag = 0

                before_file_exists = 1
                    
                for i in range(len(handles_array)):
                    
                    
                    handle_stat = handles_array[i].status()
                    torrent_name = handle_stat.name
                    
                    file_csv_name = "Output_-_"+torrent_name[:40]
                    file_csv_path = self.output+file_csv_name + '.csv'
                        

                    if os.path.exists(file_csv_path):
                        before_file_exists = 1
                    else:
                        before_file_exists = 0
                    
                        
                    f = open(file_csv_path, 'a+')
                    files_csv_array.append(f)
                    
                    # Criacao e Cabecalho do ficheiro csv
                    writer = csv.DictWriter(files_csv_array[i], fieldnames=self.fieldnames_output_csv)


                    if before_file_exists == 0:
                        writer.writeheader()
                    
                    f.close()
                    
                    
                    
                    peers = handles_array[i].get_peer_info()
                    
                    
                    
                    
                    # name, progress, downloaded size, download rate, upload rate, state, n peers instantaneo, saving peers in csv
                    stat_info_array = [handle_stat.name[:40], float(handle_stat.progress * 100), 
                                       torrent_monitor.size_converter(self, handle_stat.total_download), 
                                       torrent_monitor.size_converter(self, handle_stat.download_rate), torrent_monitor.size_converter(self, handle_stat.upload_rate), 
                                       self.torrentState(handle_stat.state), handle_stat.num_peers, len(peers)]
            
                    table_torrents_info_array.append(stat_info_array)
                    
                    table = tabulate(table_torrents_info_array, headers=table_header, 
                                    showindex="always", tablefmt="fancy_grid",
                                    missingval="?")
                    

                    
                    
                    current_time = datetime.now()
                    
                    ip_to_write_array = []
                    client_to_write_array = []
                    version_to_write_array = []
                    progress_to_write_array = []
                    date_to_write_array = []
                    hour_to_write_array = []
                    countryISO_to_write_array = []
                    country_to_write_array = []
                    num_complete_array = []
                    num_incomplete_array = []
                    num_seeds_array = []
                    num_peers_array = []
                    list_seeds_array = []
                    list_peers_array = []
                    num_complete_connected_array = []

                    num_complete_connected = 0

                    if peers:
                        for p in peers:
                            ip, port  = p.ip
                            
                            # retirar o IP local do registo
                            #if ip == '127.0.0.1':
                            #    continue

                            country = ''
                            countryISO = ''
                            
                            '''
                            if self.geo:
                                try:
                                    response = reader.country(ip)
                                    country = response.country.name
                                    countryISO = response.country.iso_code
                                except Exception as e:
                                    print(e)
                            '''
                            
                            client = ''
                            version = ''
                            
                            try: 
                                client = p.client.decode("utf-8")

                                if client:
                                    if '/' in client :
                                        metadata = client.split('/')
                                    elif ' ' in client :
                                        metadata = client.split(' ')
                                        
                                    if len(metadata) > 1:
                                        
                                        if 'Unknown' in metadata[0]:
                                            client = 'Unknown'
                                            version = ''
                                            
                                        else:
                                            client = metadata[0]
                                            version = str(metadata[1])

                                    else:
                                        client = metadata
                            except Exception as e:
                                print(e)
                            

                            '''
                            peerDict = {'ip': ip, 'client': client, 'version': version, 
                                'date': current_time.strftime("%Y-%m-%d"), 'countryISO': countryISO,'country': country}
                            
                            
                            if self.elastic:
                                self.save_elasticsearch_es('mulan', peerDict)
                            '''
                            
                           

                            progress_peer = float(p.progress) * 100
                            progress_peer_rounded = round(progress_peer, 2)

                            if progress_peer_rounded == 100.0:
                                num_complete_connected = num_complete_connected + 1

                            # Save peers info
                            ip_to_write_array.append(ip)
                            client_to_write_array.append(client)
                            version_to_write_array.append(version)
                            progress_to_write_array.append(progress_peer_rounded)
                            date_to_write_array.append(current_time.strftime("%d-%m-%Y"))
                            hour_to_write_array.append(current_time.strftime("%H:%M:%S"))
                            num_complete_array.append('')
                            num_incomplete_array.append('')
                            num_complete_connected_array.append('')
                            num_seeds_array.append('')
                            num_peers_array.append('')
                            list_seeds_array.append('')
                            list_peers_array.append('')
                            countryISO_to_write_array.append(countryISO)
                            country_to_write_array.append(country)


                        # more info: https://libtorrent.org/reference-Torrent_Status.html#torrent_status
                        num_complete_array[0] = handle_stat.num_complete
                        num_incomplete_array[0] = handle_stat.num_incomplete
                        num_seeds_array[0] = handle_stat.num_seeds
                        num_peers_array[0] = len(peers)
                        list_seeds_array[0] = handle_stat.list_seeds
                        list_peers_array[0] = handle_stat.list_peers
                        num_complete_connected_array[0] = num_complete_connected

                        

                        # Append to the .csv output analysis files 
                        df = pd.DataFrame({'ip': ip_to_write_array,
                                    'client': client_to_write_array, 
                                    'version': version_to_write_array , 
                                    'progress %': progress_to_write_array,
                                    'date': date_to_write_array, 
                                    'hour': hour_to_write_array ,
                                    'num complete by tracker': num_complete_array,
                                    'num incomplete by tracker': num_incomplete_array,
                                    'num complete connected': num_complete_connected_array,
                                    'num seeds connected': num_seeds_array,
                                    'num peers connected':  num_peers_array,
                                    'list seeds total': list_seeds_array,
                                    'list peers total': list_peers_array,
                                    'countryISO': country_to_write_array,
                                    'country': country_to_write_array})

                        df.to_csv(file_csv_path, mode='a', index=False, header=False)


                # Print Time session
                session_elapse_time = datetime.now() - self.session_start_time
                session_elapse_time_witho_sec = str(session_elapse_time).split(".")[0]

                print("\nMonitoring Session, start at: {:s}, running time: {:s}  \n".format( self.session_start_time.strftime("%d-%m-%Y/%H:%M:%S"), session_elapse_time_witho_sec) )

                # Print table
                print(table)
                

                print("\n= Close Program with [Ctrl+C]")
                
                # Sleep
                time.sleep(int(self.time))
                sys.stdout.flush()

                # Clear terminal
                torrent_monitor.clearTerminal()
                
                    
                
        except KeyboardInterrupt:
                print("\nProgram Exiting...")

                print("\nCleaning up...")
                #if self.output:
                for f in files_csv_array:
                    f.close()
                
                for handle in handles_array :

                    # more info: https://libtorrent.org/reference-Torrent_Handle.html
                    handle.flush_cache()

                    lt.session.remove_torrent(self.ses, handle)
                

                sys.exit()
                '''
                if self.geo:
                    reader.close()
                '''  
        
        #finally:
                
        
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    #parser.add_argument('-t', "--torrent", help="Torrent file or magnet", required=True)
    parser.add_argument('torrents_input', nargs="*")
    parser.add_argument("-g", "--geo", help="Enable IP geolocation", default=False, action='store_true')  
    parser.add_argument("-o", "--output", help="Output path", default='/home/lm-vm/Documentos/Projeto_Licenciatura/OuputFiles/')     
    parser.add_argument("-ek", "--elastic", help="Enable elastic saving", default=False, action='store_true') 
    parser.add_argument("-T", "--time", help="Sleeping time between downloading peers", default=30)
    parser.add_argument("-s", "--save_folder", help="Path for saving downloaded torrent content", default='/home/lm-vm/Documentos/Projeto_Licenciatura/DownloadedFiles/')  
    parser.add_argument("-fr", "--fast_resume_folder", help="Path for saving fast resume files", default='/home/lm-vm/Documentos/Projeto_Licenciatura/FastResumeFiles/')  
    parser.add_argument("-ab", "--add_batch_folder", help="Path for addBatch file", default='/home/lm-vm/Documentos/Projeto_Licenciatura/AddBatch/')       
    args = parser.parse_args()

    if not (args.elastic or args.output):
        parser.error('You need to speficy a log output or enable elastic saving option')
    else:
        t = torrent_monitor(args.torrents_input, args.output, args.elastic, args.geo, args.time, args.save_folder, args.fast_resume_folder, args.add_batch_folder)
        t.main()
