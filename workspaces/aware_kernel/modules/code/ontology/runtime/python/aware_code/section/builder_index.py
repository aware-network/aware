from uuid import UUID

# Kernel Graph Ontology
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_storage.blob_store import BlobStore

# Code
from aware_code.node.node import CodeNode


class CodeSectionBuilderIndex:
    """
    Index for storing and retrieving code sections by their type and identity hash.
    """

    def __init__(self):
        """
        Initialize the index with dictionaries:
        - _by_hash: Maps (code_section_type, identity_hash) to CodeSection
        - _by_ref: Maps (code_section_type, reference_string) to CodeSection
        - _by_qualname: Maps (code_id, code_section_type, qualname) to CodeSection
        - _by_id: Maps section_id to CodeSection
        - _code_to_path: Maps code_id to file path for fast lookups
        - _code_section_to_node: Maps code_section_id to code_node mapping
        - _blob_store: BlobStore for storing and retrieving blobs
        """
        self._by_hash: dict[tuple[CodeSectionType, str], CodeSection] = {}
        self._by_ref: dict[tuple[CodeSectionType, str], CodeSection] = {}
        self._by_qualname: dict[tuple[UUID, CodeSectionType, str], CodeSection] = {}
        self._by_id: dict[UUID, CodeSection] = {}
        self._code_to_path: dict[UUID, str] = {}  # code_id -> file_path mapping
        self._code_section_to_node: dict[UUID, CodeNode[object]] = {}  # code_section_id -> code_node mapping
        self._blob_store: BlobStore | None = None

    def add(self, code_section: CodeSection):
        """
        Add a code section to the index.

        Args:
            code_section: The CodeSection to add
        """
        hash_key = (code_section.type, code_section.identity_hash)
        existing = self._by_hash.get(hash_key)
        if existing and existing.id != code_section.id:
            raise ValueError("Identity collision ...")

        self._by_hash[hash_key] = code_section
        self._by_qualname[(code_section.code_id, code_section.type, code_section.qualname)] = code_section
        self._by_id[code_section.id] = code_section

    def add_reference(
        self,
        code_section_type: CodeSectionType,
        reference: str,
        code_section: CodeSection,
    ):
        """
        Add a reference to a code section.

        Args:
            code_section_type: The type of code section
            reference: The reference string to add
            code_section: The CodeSection to add the reference to
        """
        key = (code_section_type, reference)
        existing = self._by_ref.get(key)
        if existing and existing.id != code_section.id:
            raise ValueError(f"Reference collision: {key} maps to {existing.id} and {code_section.id}")
        self._by_ref[key] = code_section

    def add_section_node(self, code_section_id: UUID, code_node: CodeNode[object]):
        """
        Add a code section node to the index.

        Args:
            code_section_id: The ID of the CodeSection to add the node to
            code_node: The CodeNode representing the section
        """
        existing = self._code_section_to_node.get(code_section_id)
        if existing is not None:
            # Idempotent behavior for multi-pass builders:
            # - If the same section is encountered again with the same byte range, treat as a no-op.
            # - If the byte range differs, raise because our identity mapping became ambiguous.
            if existing.byte_start == code_node.byte_start and existing.byte_end == code_node.byte_end:
                return
            existing_text = existing.node_text()
            new_text = code_node.node_text()
            message = (
                "Code section node already exists for section ID "
                + f"{code_section_id} with a different byte range: "
                + f"existing={existing.byte_start}:{existing.byte_end}, "
                + f"text={existing_text} "
                + f"new={code_node.byte_start}:{code_node.byte_end}, text={new_text}"
            )
            raise ValueError(message)
        self._code_section_to_node[code_section_id] = code_node

    def set_code_path_mapping(self, code_id: UUID, file_path: str):
        """
        Set the file path mapping for a code object.

        Args:
            code_id: The ID of the code object
            file_path: The relative file path
        """
        self._code_to_path[code_id] = file_path

    def clean(self):
        self._by_hash.clear()
        self._by_ref.clear()
        self._by_qualname.clear()
        self._by_id.clear()
        self._code_to_path.clear()
        self._code_section_to_node.clear()
        self._blob_store = None

    def get_by_hash(self, code_section_type: CodeSectionType, identity_hash: str) -> CodeSection | None:
        """
        Get a code section by its type and identity hash.

        Args:
            code_section_type: The type of code section
            identity_hash: The identity hash of the code section

        Returns:
            The CodeSection if found, otherwise None
        """
        return self._by_hash.get((code_section_type, identity_hash))

    def get_by_ref(self, code_section_type: CodeSectionType, reference: str) -> CodeSection | None:
        """
        Get a code section by its type and reference string.

        Args:
            code_section_type: The type of code section
            reference: The reference string to search for

        Returns:
            The CodeSection if found, otherwise None
        """
        return self._by_ref.get((code_section_type, reference))

    def get_by_id(self, section_id: UUID) -> CodeSection | None:
        """
        Get a code section by its ID.

        Args:
            section_id: The ID of the code section

        Returns:
            The CodeSection if found, otherwise None
        """
        return self._by_id.get(section_id)

    def get_by_qualname(self, code_id: UUID, code_section_type: CodeSectionType, qualname: str) -> CodeSection | None:
        """
        Get a code section by its qualname.
        """
        return self._by_qualname.get((code_id, code_section_type, qualname))

    def get_code_path(self, section_id: UUID) -> str | None:
        """
        Get the relative file path for a section by its ID.

        This is used by the behavioral rendering stage to quickly find
        which file a section belongs to without expensive lookups.

        Args:
            section_id: The ID of the code section

        Returns:
            The relative file path, or None if section not found
        """
        section = self.get_by_id(section_id)
        if not section:
            return None
        if not section.code_id:
            return None

        # Use the code_id to file_path mapping for fast lookup
        return self._code_to_path.get(section.code_id)

    def get_section_node(self, section_id: UUID) -> CodeNode[object] | None:
        """
        Get the code node for a code section by its ID.
        """
        return self._code_section_to_node.get(section_id)

    def get_sections(self, code_section_type: CodeSectionType) -> list[CodeSection]:
        """
        Get all code sections of a specific type.
        """
        return [section for section in self._by_hash.values() if section.type == code_section_type]

    def get_all_sections(self) -> list[CodeSection]:
        """
        Get all code sections in the index.

        Returns:
            List of all CodeSection objects
        """
        return list(self._by_id.values())

    def clear_blob_store(self):
        """
        Clear the blob store for the index.
        """
        self._blob_store = None

    def get_blob_store(self) -> BlobStore | None:
        """
        Get the blob store for the index.
        """
        return self._blob_store

    def set_blob_store(self, blob_store: BlobStore):
        """
        Set the blob store for the index.
        """
        self._blob_store = blob_store
