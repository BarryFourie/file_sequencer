import importlib.util as importlib
import os
import logging
import sys
from typing import Generator, List, Dict, Any, Tuple
import logging

__author__ = "Barry Fourie"
__copyright__ = "Barry Fourie"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


class RevisionSequencer:
    def __init__(self, directory: str):
        self.directory = directory

    def extract_revision_data(self, file_path: str) -> Tuple[str, str]:
        """Extract revision_id and revised_id from a Python file by importing it. Assumed all files are valid Python files.
        Alternatively regex can be used to extract the data.

        Args:
            file_path (str): Path to the Python file.

        Raises:
            KeyError: If revision_id or revised_id is missing in the file.

        Returns:
            Tuple[str, str]: Tuple containing revision_id and revised
        """

        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.spec_from_file_location(module_name, file_path)
        module = importlib.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "revision_id") and hasattr(module, "revises_id"):
            revision_id = module.revision_id
            revises_id = module.revises_id
            return revision_id, revises_id
        else:
            error_message = "Missing revision_id or revised_id in {}".format(file_path)
            _logger.error(error_message, exc_info=False)
            raise KeyError(error_message)

    def process_files(self) -> Generator[Dict[str, Any], None, None]:
        """Process all Python files in the directory and extract revision data.
        Returns a generator of dictionaries containing filename, revision_id and revised_id.

        Raises:
            ValueError: If revision_id or revised_id is missing in a file.

        Yields:
            Dict[str, Any]: Dictionary containing filename, revision_id and revised_id.
        """

        for filename in os.listdir(self.directory):
            if filename.endswith(".py"):
                file_path = os.path.join(self.directory, filename)
                try:
                    revision_id, revises_id = self.extract_revision_data(file_path)
                    yield {
                        "filename": filename,
                        "revision_id": revision_id,
                        "revises_id": revises_id,
                    }
                except Exception as error:
                    warning_message = "Skipping file {} due to error {}".format(
                        filename, error
                    )
                    _logger.warning(warning_message)
                    raise ValueError(warning_message)

        if len(os.listdir(self.directory)) == 0:
            _logger.warning("No files found in the directory")
            raise ValueError("No files found in the directory")

    def build_revision_tree(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build an ordered tree structure where each file points to its revisions based on revises_id.
        The chain starts with the file that has no revises_id and follows each file's revision_id
        to include the next revised file, ensuring the order is preserved.

        Args:
            files_data (List[Dict[str, Any]]): List of dictionaries containing filename, revision_id, and revises_id.

        Returns:
            List[Dict[str, Any]]: A single ordered chain of files starting from the root.

        """

        files_dict = {
            file["revision_id"]: {**file, "revisions": []} for file in files_data
        }

        root = next(
            (file for file in files_dict.values() if file["revises_id"] is None), None
        )

        if root is None:
            _logger.error("No root file found in the directory")
            raise ValueError("No root file found in the directory")

        def add_revisions(file):

            revisions = [
                files_dict[child["revision_id"]]
                for child in files_data
                if child["revises_id"] == file["revision_id"]
            ]

            for revision in revisions:
                file["revisions"].append(revision)
                add_revisions(revision)

        add_revisions(root)

        return root

    def flatten_revision_tree(self, root: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Flatten the revision tree starting from the root into a single list of files, preserving
        the original file order. Each file in the list will be followed by its revisions, recursively.

        Args:
            root (Dict[str, Any]): The root file, typically the one with no `revises_id`,
                                    which contains its revisions under the "revisions" key.

        Returns:
            List[Dict[str, Any]]: A flattened list of files, starting from the root, followed by its revisions.
        """
        file_chain = []

        def traverse(file):
            # Add the current file to the flat list
            file_chain.append(file)

            sorted_revisions = sorted(
                file.get("revisions", []), key=lambda x: len(x.get("revisions", []))
            )

            for revision in sorted_revisions:
                traverse(revision)

        # Start traversal from the root
        traverse(root)

        return file_chain

    def rename_files_in_sequence(self, chain: List[Dict[str, Any]]) -> None:
        """Rename files in the directory based on the ordered chain.

        Args:
            chain (List[Dict[str, Any]]): Ordered chain of files.

        Raises:
            Exception: If an error is encountered when renaming files, all changes are rolled back.
        """

        try:
            renamed_files = []
            for index, file_data in enumerate(chain, start=1):
                original_path = os.path.join(self.directory, file_data["filename"])
                new_name = f"{index}_{file_data['filename']}"
                new_path = os.path.join(self.directory, new_name)
                os.rename(original_path, new_path)
                renamed_files.append((new_path, original_path))
                file_data["new_filename"] = new_name
                _logger.info(f"Renamed {file_data['filename']} to {new_name}")

        except Exception as error:
            _logger.error(
                "Error encountered when saving files: {}. Rolling back changes...".format(
                    error
                )
            )

            for new_path, original_path in reversed(renamed_files):
                os.rename(new_path, original_path)

            _logger.info("Rollback complete. All files reverted to original names.")


def main():
    if len(sys.argv) == 1:
        _logger.error("No directory provided")
        raise ValueError("No directory provided")
    sequencer = RevisionSequencer(sys.argv[1])
    files_data = list(sequencer.process_files())
    tree = sequencer.build_revision_tree(files_data)
    chain = sequencer.flatten_revision_tree(tree)
    sequencer.rename_files_in_sequence(chain)


if __name__ == "__main__":
    main()
