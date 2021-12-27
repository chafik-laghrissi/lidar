from georef import Georef
import glob
if __name__=='__main__':
    # paths for scanner data set
    paths=glob.glob('data/scanner_data/*.xyz')
    # create instance of Georef class
    instance=Georef('data/GPS&INS_data/export_dgps_event2.txt',paths)
    # Start processing (georeferencing) data 
    data=instance.georef()
    # Save data to test.scv path
    instance.save_georef_data('test.csv')
