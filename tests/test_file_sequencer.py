import pytest
import os
import tempfile
from file_sequencer.file_sequencer import RevisionSequencer


@pytest.fixture
def temp_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def create_test_file(directory, filename, revision_id=None, revises_id=None):
    file_path = os.path.join(directory, filename)
    with open(file_path, "w") as f:
        f.write(f"revision_id = '{revision_id}'\n")
        if revises_id is not None:
            f.write(f"revises_id = '{revises_id}'\n")
        else:
            f.write("revises_id = None\n")
    return file_path


@pytest.fixture
def test_data(temp_directory):
    files = [
        {
            "new_filename": "1_rev1.py",
            "filename": "rev1.py",
            "revision_id": "rev1",
            "revises_id": None,
        },
        {
            "new_filename": "2_rev2.py",
            "filename": "rev2.py",
            "revision_id": "rev2",
            "revises_id": "rev1",
        },
        {
            "new_filename": "3_rev3.py",
            "filename": "rev3.py",
            "revision_id": "rev3",
            "revises_id": "rev2",
        },
        {
            "new_filename": "4_rev4.py",
            "filename": "rev4.py",
            "revision_id": "rev4",
            "revises_id": "rev2",
        },
        {
            "new_filename": "5_rev5.py",
            "filename": "rev5.py",
            "revision_id": "rev5",
            "revises_id": "rev4",
        },
    ]
    for file in files:
        create_test_file(
            temp_directory, file["filename"], file["revision_id"], file["revises_id"]
        )
    return temp_directory, files


def test_extract_revision_data(test_data):
    temp_directory, files = test_data
    sequencer = RevisionSequencer(temp_directory)
    for file in files:
        revision_id, revises_id = sequencer.extract_revision_data(
            os.path.join(temp_directory, file["filename"])
        )
        assert revision_id == file["revision_id"]
        assert revises_id == file["revises_id"]


def test_process_files(test_data):
    temp_directory, files = test_data
    sequencer = RevisionSequencer(temp_directory)
    files_data = list(sequencer.process_files())
    assert len(files_data) == len(files)
    for file_data, file in zip(files_data, files):
        assert file_data["filename"] == file["filename"]
        assert file_data["revision_id"] == file["revision_id"]
        assert file_data["revises_id"] == file["revises_id"]


def test_flatten_revision_tree(test_data):
    temp_directory, files = test_data
    sequencer = RevisionSequencer(temp_directory)
    files_data = list(sequencer.process_files())
    tree = sequencer.build_revision_tree(files_data)
    chain = sequencer.flatten_revision_tree(tree)
    assert len(chain) == len(files)
    for file_data, file in zip(chain, files):
        assert file_data["filename"] == file["filename"]
        assert file_data["revision_id"] == file["revision_id"]
        assert file_data["revises_id"] == file["revises_id"]


def test_rename_files_in_sequence(test_data):
    temp_directory, files = test_data
    sequencer = RevisionSequencer(temp_directory)
    files_data = list(sequencer.process_files())
    tree = sequencer.build_revision_tree(files_data)
    chain = sequencer.flatten_revision_tree(tree)
    sequencer.rename_files_in_sequence(chain)
    for index, file in enumerate(files, start=1):
        assert os.path.exists(os.path.join(temp_directory, file["new_filename"]))
