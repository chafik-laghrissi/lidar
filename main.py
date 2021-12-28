from georef import Georef
import glob
import os

if __name__=='__main__':
    # paths for scanner data set
    paths=glob.glob('data/scanner_data/*.xyz')
    
    Georef.georef_by_file('data/GPS&INS_data/export_dgps_event2.txt',paths,path='test.csv')
