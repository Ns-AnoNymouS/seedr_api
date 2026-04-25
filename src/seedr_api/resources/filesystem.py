"""Filesystem resource — folders, files, and batch operations."""

from __future__ import annotations

import json
from typing import Any

from seedr_api.models.filesystem import (
    BatchResult,
    FileInfo,
    FolderContents,
    FolderInfo,
)
from seedr_api.resources._base import BaseResource


class FilesystemResource(BaseResource):
    """Provides methods for browsing and managing files and folders in Seedr."""

    # ------------------------------------------------------------------
    # Root folder
    # ------------------------------------------------------------------

    async def get_root(self) -> FolderInfo:
        """Return metadata for the root folder.

        Required scope: ``files.read``

        Returns
        -------
        FolderInfo
            Root folder details.
        """
        data: Any = await self._http.get("/fs/root")
        return FolderInfo.model_validate(data)

    async def list_root_contents(self) -> FolderContents:
        """List all contents (subfolders, files, active torrents) of the root folder.

        Required scope: ``files.read``

        Returns
        -------
        FolderContents
            Root folder contents.
        """
        data: Any = await self._http.get("/fs/root/contents")
        return FolderContents.model_validate(data)

    # ------------------------------------------------------------------
    # Folder operations
    # ------------------------------------------------------------------

    async def get_folder(self, folder_id: int) -> FolderInfo:
        """Return metadata for a specific folder.

        Required scope: ``files.read``

        Parameters
        ----------
        folder_id:
            The numeric ID of the folder.

        Returns
        -------
        FolderInfo
            Folder metadata.
        """
        data: Any = await self._http.get(f"/fs/folder/{folder_id}")
        return FolderInfo.model_validate(data)

    async def list_folder_contents(self, folder_id: int) -> FolderContents:
        """List all contents of a specific folder.

        Required scope: ``files.read``

        Parameters
        ----------
        folder_id:
            The numeric ID of the folder.

        Returns
        -------
        FolderContents
            Folder contents.
        """
        data: Any = await self._http.get(f"/fs/folder/{folder_id}/contents")
        return FolderContents.model_validate(data)

    async def create_folder(
        self, name: str, parent_id: int | None = None
    ) -> FolderInfo:
        """Create a new folder.

        Required scope: ``files.write``

        Parameters
        ----------
        name:
            Name of the new folder.
        parent_id:
            Parent folder ID. Defaults to the root folder.

        Returns
        -------
        FolderInfo
            Created folder metadata.
        """
        payload: dict[str, Any] = {"name": name}
        if parent_id is not None:
            payload["parent"] = parent_id
        data: Any = await self._http.post("/fs/folder", data=payload)
        return FolderInfo.model_validate(data)

    async def rename_folder(self, folder_id: int, new_name: str) -> FolderInfo:
        """Rename an empty folder.

        The Seedr public API does not support moving items via Bearer-token auth,
        so rename is only possible for empty folders: creates a replacement with
        the new name then deletes the original.

        Required scope: ``files.write``

        Parameters
        ----------
        folder_id:
            The numeric ID of the folder to rename.
        new_name:
            New display name for the folder.

        Returns
        -------
        FolderInfo
            The newly created folder (carries the new ID).

        Raises
        ------
        ValueError
            If the folder is non-empty (rename would lose its contents).
        """
        from seedr_api.exceptions import SeedrError

        folder = await self.get_folder(folder_id)
        parent_id = folder.parent if folder.parent and folder.parent != -1 else None

        contents = await self.list_folder_contents(folder_id)
        if contents.folders or contents.files:
            raise SeedrError(
                "Rename is only supported for empty folders via the Seedr OAuth API."
            )

        new_folder = await self.create_folder(new_name, parent_id=parent_id)
        await self.delete_folder(folder_id)
        return new_folder


    async def delete_folder(self, folder_id: int) -> None:
        """Delete a folder and all its contents.

        Required scope: ``files.write``

        Parameters
        ----------
        folder_id:
            The numeric ID of the folder to delete.
        """
        await self._http.delete(
            f"/fs/folder/{folder_id}",
            data={"delete_arr": json.dumps([{"id": folder_id, "type": "folder"}])},
        )

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    async def get_file(self, file_id: int) -> FileInfo:
        """Return metadata for a specific file.

        Required scope: ``files.read``

        Parameters
        ----------
        file_id:
            The numeric ID of the file.

        Returns
        -------
        FileInfo
            File metadata.
        """
        data: Any = await self._http.get(f"/fs/file/{file_id}")
        return FileInfo.model_validate(data)

    async def delete_file(self, file_id: int) -> None:
        """Delete a specific file.

        Required scope: ``files.write``

        Parameters
        ----------
        file_id:
            The numeric ID of the file to delete.
        """
        await self._http.delete(
            f"/fs/file/{file_id}",
            data={"delete_arr": json.dumps([{"id": file_id, "type": "file"}])},
        )

    # ------------------------------------------------------------------
    # Path lookup
    # ------------------------------------------------------------------

    async def get_by_path(self, path: str) -> FolderInfo | FileInfo:
        """Retrieve a file or folder by its absolute path within Seedr.

        Required scope: ``files.read``

        Parameters
        ----------
        path:
            Absolute path (e.g. ``"/My Folder/file.mkv"``).

        Returns
        -------
        FolderInfo | FileInfo
            The located resource.
        """
        data: Any = await self._http.get("/fs/path", params={"path": path})
        if "name" in data and "folders" not in data:
            return FileInfo.model_validate(data)
        return FolderInfo.model_validate(data)

    # ------------------------------------------------------------------
    # Batch operations
    # ------------------------------------------------------------------

    async def batch_copy(
        self,
        item_ids: list[int],
        destination_folder_id: int,
    ) -> BatchResult:
        """Copy multiple files/folders to a destination folder.

        Required scope: ``files.write``

        Parameters
        ----------
        item_ids:
            List of file or folder IDs to copy.
        destination_folder_id:
            Target folder ID.

        Returns
        -------
        BatchResult
            Success status and any errors.
        """
        data: Any = await self._http.post(
            "/fs/batch/copy",
            data={"ids": item_ids, "destination": destination_folder_id},
        )
        return BatchResult.model_validate(data)

    async def batch_move(
        self,
        item_ids: list[int],
        source_folder_id: int,
        destination_folder_id: int,
    ) -> BatchResult:
        """Move multiple files/folders to a destination folder.

        Required scope: ``files.write``

        Parameters
        ----------
        item_ids:
            List of file or folder IDs to move.
        source_folder_id:
            Current parent folder ID of the items.
        destination_folder_id:
            Target folder ID.

        Returns
        -------
        BatchResult
            Success status and any errors.
        """
        data: Any = await self._http.post(
            "/fs/batch/move",
            data={
                "copy_arr": json.dumps([]),
                "move_arr": json.dumps(item_ids),
                "from": source_folder_id,
                "to": destination_folder_id,
            },
        )
        return BatchResult.model_validate(data)

    async def batch_delete(self, item_ids: list[int]) -> BatchResult:
        """Delete multiple files, folders, or torrent tasks.

        Required scope: ``files.write``

        Parameters
        ----------
        item_ids:
            List of file/folder/task IDs to delete.

        Returns
        -------
        BatchResult
            Success status and any errors.
        """
        tagged = [{"id": i, "type": "folder"} for i in item_ids]
        data: Any = await self._http.post(
            "/fs/batch/delete",
            data={"delete_arr": json.dumps(tagged)},
        )
        return BatchResult.model_validate(data)
