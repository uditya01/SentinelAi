"""
ember_feature_extractor.py

Extracts machine learning features from a single
EMBER JSON record.

Used ONLY during model training.

Author: Sentinel AI
"""

from typing import Dict, Any


class EmberFeatureExtractor:
    """
    Converts one EMBER JSON sample into
    a structured feature dictionary.
    """

    def extract(self, sample: Dict[str, Any]) -> Dict[str, float]:

        features = {}

        # ==================================================
        # LABEL
        # ==================================================

        features["label"] = sample.get("label", -1)

        # ==================================================
        # GENERAL
        # ==================================================

        general = sample.get("general", {})

        features["size"] = general.get("size", 0)
        features["vsize"] = general.get("vsize", 0)
        features["imports_count"] = general.get("imports", 0)
        features["exports_count"] = general.get("exports", 0)
        features["symbols"] = general.get("symbols", 0)
        features["has_tls"] = general.get("has_tls", 0)
        features["has_resources"] = general.get("has_resources", 0)
        features["has_signature"] = general.get("has_signature", 0)
        features["has_relocations"] = general.get("has_relocations", 0)
        features["has_debug"] = general.get("has_debug", 0)

        # ==================================================
        # HISTOGRAM
        # ==================================================

        histogram = sample.get("histogram", [])

        for i, value in enumerate(histogram):
            features[f"histogram_{i}"] = value

        # ==================================================
        # BYTE ENTROPY
        # ==================================================

        byteentropy = sample.get("byteentropy", [])

        for i, value in enumerate(byteentropy):
            features[f"byteentropy_{i}"] = value

        # ==================================================
        # STRINGS
        # ==================================================

        strings = sample.get("strings", {})

        features["numstrings"] = strings.get("numstrings", 0)
        features["avg_string_length"] = strings.get("avlength", 0.0)
        features["string_entropy"] = strings.get("entropy", 0.0)
        features["num_paths"] = strings.get("paths", 0)
        features["num_urls"] = strings.get("urls", 0)
        features["num_registry"] = strings.get("registry", 0)
        features["printable_chars"] = strings.get("printables", 0)
        features["mz_count"] = strings.get("MZ", 0)

        # ==================================================
        # IMPORTS
        # ==================================================

        imports = sample.get("imports", {})

        features["dll_count"] = len(imports)

        api_count = 0

        for dll in imports.values():
            api_count += len(dll)

        features["api_count"] = api_count

        # ==================================================
        # SECTIONS
        # ==================================================

        section = sample.get("section", {})

        sections = section.get("sections", [])

        features["section_count"] = len(sections)

        entropy_sum = 0.0
        raw_size_sum = 0

        for sec in sections:
            entropy_sum += sec.get("entropy", 0.0)
            raw_size_sum += sec.get("size", 0)

        if len(sections):

            features["avg_section_entropy"] = (
                entropy_sum / len(sections)
            )

        else:

            features["avg_section_entropy"] = 0.0

        features["total_section_size"] = raw_size_sum

        # ==================================================
        # EXPORTS
        # ==================================================

        exports = sample.get("exports", [])

        features["export_function_count"] = len(exports)

        # ==================================================
        # DATA DIRECTORIES
        # ==================================================

        directories = sample.get("datadirectories", [])

        features["data_directory_count"] = len(directories)

        total_directory_size = 0

        for item in directories:
            total_directory_size += item.get("size", 0)

        features["total_directory_size"] = total_directory_size

        # ==================================================
        # HEADER
        # ==================================================

        header = sample.get("header", {})

        coff = header.get("coff", {})
        optional = header.get("optional", {})

        features["timestamp"] = coff.get("timestamp", 0)
        features["major_linker"] = optional.get(
            "major_linker_version",
            0
        )
        features["minor_linker"] = optional.get(
            "minor_linker_version",
            0
        )
        features["sizeof_code"] = optional.get(
            "sizeof_code",
            0
        )
        features["sizeof_headers"] = optional.get(
            "sizeof_headers",
            0
        )

        return features