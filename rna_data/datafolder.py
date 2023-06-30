
from typing import Any

from .config import DATA_FOLDER
from .path_datafolder import PathDatafolder
from .config import DATA_FOLDER
from .datapoints import ListofDatapoints, write_list_of_datapoints_to_json
from .info_file import infoFileWriter
from .write_npy import write_dms_npy_from_json, write_structure_npy_from_json
import os
import numpy as np
from huggingface_hub import HfApi
from .config import HUGGINGFACE_TOKEN
from huggingface_hub import snapshot_download

GENERATE_NPY = False
PREDICT_STRUCTURE = False
PREDICT_DMS = False
ROUSKINLAB = 'rouskinlab/'




class CreateDatafolderTemplate(PathDatafolder):

    def __init__(self, path_in, path_out, name, source, predict_structure, predict_dms) -> None:
        super().__init__(name, path_out)
        self.path_in = path_in
        self.path_out = path_out
        self.datapoints = []
        self.api = HfApi(token=HUGGINGFACE_TOKEN)
        self.predict_structure = predict_structure
        self.predict_dms = predict_dms

        # Set name
        if name is None:
            name = path_in.replace('\\','/').split('/')[-1].split('.')[0]
        self.name = name

        # move path_in to source folder
        os.makedirs(self.get_source_folder(), exist_ok=True)
        os.system(f'cp -fr {path_in} {self.get_source_folder()}')

        # Write info file
        infoFileWriter(source=source, datafolder=self).write()


    def __repr__(self) -> str:
        return f"{self.__class__.__name__} @{self.get_main_folder()}"

    def create_repo(self, exist_ok=False, private=True):

        """Create a repo on huggingface.co.

        Parameters
        ----------

        exist_ok : bool, optional
            If True, the repo is created even if it already exists. Default is False.

        private : bool, optional
            If True, the repo is private. Default is True.

        Examples
        --------

        >>> datafolder = DataFolder.from_huggingface('for_testing')
        >>> datafolder.create_repo()

        """

        self.api.create_repo(
            repo_id=ROUSKINLAB+self.name,
            token=HUGGINGFACE_TOKEN,
            exist_ok=exist_ok,
            private=private,
            repo_type="dataset",
        )

    def upload_folder(self, revision = 'main', commit_message=None, commit_description=None, multi_commits=False, run_as_future=False, **kwargs):

        """Upload the datafolder to huggingface.co.

        Parameters
        ----------

        revision : str, optional
            The revision of the repo (i.e. the branch on the HuggingFace hub). Default is 'main'.

        commit_message : str, optional
            The commit message. Default is None.

        commit_description : str, optional
            The commit description. Default is None.

        multi_commits : bool, optional
            Useful for large files. If True, the upload is done in multiple commits. Default is False.

        run_as_future : bool, optional
            If True, the upload is run asynchonously. The state of the upload can be checked with the returned future. See sample code. Default is False.

        Examples
        --------

        >>> datafolder = DataFolder.from_huggingface('for_testing')
        >>> datafolder.upload_folder('main', 'pytest commit', 'A commit generated by pytest for the upload_folder method')
        >>> future = datafolder.upload_folder(run_as_future=True)
        >>> future.result() # wait for the upload to finish
        >>> future.done() # check if the upload is done
        True

        """


        future = self.api.upload_folder(
            repo_id=ROUSKINLAB+self.name,
            folder_path=self.get_main_folder(),
            repo_type="dataset",
            token=HUGGINGFACE_TOKEN,
            revision=revision,
            commit_message=commit_message,
            commit_description=commit_description,
            multi_commits=multi_commits,
            run_as_future=run_as_future,
            **kwargs
        )

        if run_as_future:
            return future

    def generate_npy(self):

        if self.predict_structure:
            write_structure_npy_from_json(self)

        if self.predict_dms:
            write_dms_npy_from_json(self)


class CreateDatafolderFromJSON(CreateDatafolderTemplate):

    def __init__(self, path_in, name, predict_structure, predict_dms, generate_npy) -> None:
        super().__init__(path_in, name)


class CreateDatafolderFromDreemOutput(CreateDatafolderTemplate):

    """Create a datafolder from a dreem output file.

    Parameters
    ----------

    path_in : str
        path_in to the dreem output file.

    name : str, optional
        Name of the datafolder. If None, the name is the name of the file or folder.

    predict_structure : bool, optional
        If True, the structure of the RNA is predicted. Default is True.

    generate_npy : bool, optional
        If True, the npy files are generated. Default is True.


    Examples
    --------

    >>> datafolder = DataFolder.from_dreem_output(path_in='data/input_files_for_testing/dreem_output.json', generate_npy=True)
    >>> datafolder.name
    'dreem_output'
    >>> print(datafolder)
    CreateDatafolderFromDreemOutput @data/datafolders/dreem_output
    >>> os.path.isfile(datafolder.get_json())
    True
    """

    def __init__(self, path_in, path_out, name, predict_structure, generate_npy) -> None:
        super().__init__(path_in, path_out, name, source = 'dreem_output', predict_structure = predict_structure, predict_dms = False)

        write_list_of_datapoints_to_json(
            path = self.get_json(),
            datapoints = ListofDatapoints.from_dreem_output(path_in, predict_structure = predict_structure)
        )

        if generate_npy:
            self.generate_npy()


class CreateDatafolderFromFasta(CreateDatafolderTemplate):

    """ Create a datafolder from a fasta file.

    Parameters
    ----------

    path_in : str
        path_in to the dreem output file.

    name : str, optional
        Name of the datafolder. If None, the name is the name of the file or folder.

    predict_structure : bool, optional
        If True, the structure of the RNA is predicted. Default is True.

    predict_dms : bool, optional
        If True, the dms of the RNA is predicted. Default is True.

    generate_npy : bool, optional
        If True, the npy files are generated. Default is True.


    Examples
    --------

    >>> datafolder = DataFolder.from_fasta(path_in='data/input_files_for_testing/sequences.fasta', generate_npy=True)
    >>> datafolder.name
    'sequences'
    >>> print(datafolder)
    CreateDatafolderFromFasta @data/datafolders/sequences
    >>> os.path.isfile(datafolder.get_json())
    True
    """

    def __init__(self, path_in, path_out, name, predict_structure, predict_dms, generate_npy) -> None:
        super().__init__(path_in, path_out, name, source = 'fasta', predict_structure = predict_structure, predict_dms = predict_dms)

        write_list_of_datapoints_to_json(
            path = self.get_json(),
            datapoints = ListofDatapoints.from_fasta(path_in, predict_structure = predict_structure, predict_dms = predict_dms)
        )

        if generate_npy:
            self.generate_npy()


class CreateDatafolderFromCTfolder(CreateDatafolderTemplate):

    """ Create a datafolder from a folder of ct files.

    Parameters
    ----------

    path_in : str
        path_in to the dreem output file.

    name : str, optional
        Name of the datafolder. If None, the name is the name of the file or folder.

    predict_dms : bool, optional
        If True, the dms of the RNA is predicted. Default is True.

    generate_npy : bool, optional
        If True, the npy files are generated. Default is True.


    Examples
    --------

    >>> datafolder = DataFolder.from_ct_folder(path_in='data/input_files_for_testing/ct_files', generate_npy=True)
    >>> datafolder.name
    'ct_files'
    >>> print(datafolder)
    CreateDatafolderFromCTfolder @data/datafolders/ct_files
    >>> os.path.isfile(datafolder.get_json())
    True
    """

    def __init__(self, path_in, path_out, name, predict_dms, generate_npy) -> None:
        super().__init__(path_in, path_out, name, source = 'ct', predict_structure = False, predict_dms = predict_dms)

        ct_files = [os.path.join(path_in, f) for f in os.listdir(path_in) if f.endswith('.ct')]
        write_list_of_datapoints_to_json(
            path = self.get_json(),
            datapoints = ListofDatapoints.from_ct(ct_files, predict_dms = predict_dms)
        )

        if generate_npy:
            self.generate_npy()


class LoadDatafolderFromHF(PathDatafolder):
    """Load a datafolder from HuggingFace.

    Parameters
    ----------

    name : str
        Name of the datafolder.

    path_out : str
        Path to the folder where the datafolder is saved.

    revision : str, optional
        Revision of the datafolder. Default is 'main'.


    Examples
    --------

    >>> datafolder = LoadDatafolderFromHF(name='for_testing', path_out='data/datafolders')
    >>> datafolder.name
    'for_testing'
    """

    def __init__(self, name, path_out, revision='main') -> None:
        super().__init__(name, path_out)

        # Download the datafolder #TODO : check if the datafolder is already downloaded
        snapshot_download(
            repo_id = ROUSKINLAB+self.name,
            repo_type='dataset',
            local_dir=self.get_main_folder(),
            revision=revision,
            token=HUGGINGFACE_TOKEN,
            )

        assert os.path.isdir(self.get_main_folder()), f'No folder found in {self.get_main_folder()}'
        assert os.path.isfile(self.get_json()), f'No json file found in {self.get_main_folder()}'



class DataFolder:
    """Create a datafolder from a fasta file, a json file or a folder of ct files.

    Parameters
    ----------

    path_in : str
        path_in to the fasta file, the json file or the folder of ct files.

    path_out : str
        path_out to the folder where the datafolder is created.

    name : str, optional
        Name of the datafolder. If None, the name is the name of the file or folder.

    predict_structure : bool, optional
        If True, the structure is predicted. Default is True.

    predict_dms : bool, optional
        If True, the dms is predicted. Default is True.


    Example
    -------

    >>> datafolder = DataFolder.from_fasta('data/input_files_for_testing/sequences.fasta')
    >>> datafolder = DataFolder.from_dreem_output('data/input_files_for_testing/dreem_output.json')
    >>> datafolder = DataFolder.from_ct_folder('data/input_files_for_testing/ct_files')
    >>> datafolder = DataFolder.from_huggingface('for_testing')
    """

    def __init__(cls) -> None:
        pass

    @classmethod
    def from_fasta(cls, path_in, path_out=DATA_FOLDER, name = None, predict_structure = PREDICT_STRUCTURE, predict_dms = PREDICT_DMS, generate_npy = GENERATE_NPY)->CreateDatafolderFromFasta:
        """Create a datafolder from a fasta file. See CreateDatafolderFromFasta for more details."""
        return CreateDatafolderFromFasta(path_in, path_out, name, predict_structure, predict_dms, generate_npy)

    @classmethod
    def from_dreem_output(cls, path_in, path_out=DATA_FOLDER, name = None, predict_structure = PREDICT_STRUCTURE, generate_npy = GENERATE_NPY)->CreateDatafolderFromDreemOutput:
        """Create a datafolder from a dreem output file. See CreateDatafolderFromDreemOutput for more details."""
        return CreateDatafolderFromDreemOutput(path_in, path_out, name, predict_structure, generate_npy)

   # def from_json(path_in, path_out=DATA_FOLDER, name = None, generate_npy = GENERATE_NPY):
   #     return CreateDatafolderFromJSON(path_in, path_out, name, generate_npy)

    @classmethod
    def from_ct_folder(cls, path_in, path_out=DATA_FOLDER, name = None, predict_dms = PREDICT_DMS, generate_npy = GENERATE_NPY)->CreateDatafolderFromCTfolder:
        """Create a datafolder from a folder of ct files. See CreateDatafolderFromCTfolder for more details."""
        return CreateDatafolderFromCTfolder(path_in, path_out, name, predict_dms, generate_npy)

    @classmethod
    def from_huggingface(cls, name, path_out=DATA_FOLDER)->LoadDatafolderFromHF:
        """Load a datafolder from HuggingFace. See LoadDatafolderFromHF for more details."""
        return LoadDatafolderFromHF(name, path_out)
