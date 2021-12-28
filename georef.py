import numpy as np
import pandas as pd
import os
from threading import Thread
from glob import glob
import shutil
import multiprocessing


class Georef:
    """
    Georef class aim to georeference lidar data
    Start by creating an instance example:
    georef_instance=Georef(gps_path='data/GPS&INS_data/export_dgps_event2.txt',scanner_paths=['scanner1','scanner2'])
    Start gearefrencing data:
    georef_instance.georef()
    this method returns the result of processing
    then you can save data as csv
    georef_instance.save_georef_data(path='test.csv')
    """
    bras_levier = np.array([0.14, 0.249, -0.076])
    rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    scanner_data = []
    PROFILES_NUMBER = 538

    def __init__(self, gps_path: str, scanner_paths: list):
        self.gps_data = self.read_gps_file(gps_path)
        for path in scanner_paths:
            self.read_scanner_file(path)

    def clean_data(self, data):
        df = pd.DataFrame(data,
                          columns=[
                              'Profile', 'Index', 'X', 'Y', 'Z', 'Alpha',
                              'Beta', 'Gama'
                          ])
        df['Profile'] = df['Profile'].astype(int)
        df['Index'] = df['Index'].astype(int)
        df.drop(['Alpha', 'Beta', 'Gama'], axis=1, inplace=True)
        df.sort_values(by='Profile', inplace=True)
        return df

    def read_gps_file(self, path: str):
        self.gps_data = np.loadtxt(path, skiprows=1)
        return np.loadtxt(path, skiprows=1)

    def read_scanner_file(self, path: str):
        data = np.loadtxt(path)
        data = self.clean_data(data)
        self.scanner_data.append(data)
        return data

    def scanner_to_gps(self, coords):
        return self.bras_levier + self.rotation.dot(coords)

    def rot(self, angles):
        x_rot = np.deg2rad(angles[0])
        y_rot = np.deg2rad(angles[1])
        z_rot = np.deg2rad(angles[2])
        m11 = np.cos(y_rot) * np.cos(z_rot)
        m12 = np.sin(x_rot) * np.sin(y_rot) * np.cos(z_rot) + np.cos(
            x_rot) * np.sin(z_rot)
        m13 = -np.cos(x_rot) * np.sin(y_rot) * np.cos(z_rot) + np.sin(
            x_rot) * np.sin(z_rot)
        m21 = -np.cos(y_rot) * np.sin(z_rot)
        m22 = -np.sin(x_rot) * np.sin(y_rot) * np.sin(z_rot) + np.cos(
            x_rot) * np.cos(z_rot)
        m23 = np.cos(x_rot) * np.sin(y_rot) * np.sin(z_rot) + np.sin(
            x_rot) * np.cos(z_rot)
        m31 = np.sin(y_rot)
        m32 = -np.sin(x_rot) * np.cos(y_rot)
        m33 = np.cos(x_rot) * np.cos(y_rot)
        return np.array([[m11, m12, m13], [m21, m22, m23], [m31, m32, m33]])

    def gps_to_carto(self, coords, index):
        transition = self.gps_data[index][1:4]
        rotation = self.rot(self.gps_data[index][7:10])
        return transition + rotation.dot(coords)

    def georef(self):
        gps_index = 0
        georef_data = []
        print('Start processing data')
        for i, data in enumerate(self.scanner_data):
            current_profile = 0
            for coords in data.to_numpy():
                if coords[0] == current_profile:
                    pos1 = self.scanner_to_gps(coords[2:6])
                    georef_data.append(self.gps_to_carto(pos1, gps_index))
                else:
                    gps_index += 1
                    current_profile += 1
            print(f'working on data {int((i+1)/len(self.scanner_data)*100)}%')
        print('processing completed')
        self.georef_data = np.array(georef_data)
        return georef_data

    def save_georef_data(self, path: str):
        """
        Saving georeferenced data as cv
        this function take one param: path
        the path where u want to save the file
        exemple: 'data/test.csv'
        """
        try:
            pd.DataFrame(self.georef_data, columns=['X', 'Y',
                                                    'Z']).to_csv(path,
                                                                 index=False)
        except Exception as ex:
            print(ex)

    @classmethod
    def georef_by_file(cls, gps_path: str, scanner_paths: list, path):
        georef = cls(gps_path, scanner_paths)
        gps_indexes = list(range(len(georef.scanner_data)))
        gps_indexes = [x * georef.PROFILES_NUMBER for x in gps_indexes]
        threads = []
        os.mkdir('tmp')

        def process(georef, index, gps_index):
            data = georef.scanner_data[index]
            current_profile = 0
            georef_data = []
            for coords in data.to_numpy():
                if coords[0] == current_profile:
                    pos1 = georef.scanner_to_gps(coords[2:6])
                    georef_data.append(georef.gps_to_carto(pos1, gps_index))
                else:
                    gps_index += 1
                    current_profile += 1
            pd.DataFrame(georef_data, columns=['X', 'Y',
                                               'Z']).to_csv(f'tmp/{index}.csv',
                                                            index=False)
            print(f'file {index+1} processed.')

        for index, gps_index in enumerate(gps_indexes):
            t = multiprocessing.Process(target=process,
                                        args=(georef, index, gps_index))
            threads.append(t)
        print('start processing')
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
        files = glob('tmp/*.csv')
        df = pd.DataFrame(columns=['X', 'Y', 'Z'])
        for file in files:
            df = df.append(pd.read_csv(file))
        df.to_csv(path, index=False)
        print('Cleaning...')
        shutil.rmtree('tmp')
        print('Process was completed.')
