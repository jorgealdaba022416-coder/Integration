from abc import ABC, abstractmethod

class StorageAdapter(ABC):
    @abstractmethod
    def upload(self, file_path: str, destination_name: str) -> str:
        pass

    @abstractmethod
    def list_files(self) -> list:
        pass
