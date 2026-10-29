"""Write ontology and registry references (HERD) for the terms in an NWB file."""
from hdmf.common import DynamicTable
from pynwb import NWBFile
from pynwb.resources import HERD


def add_external_resources(nwbfile: NWBFile, terms: dict) -> None:
    """Write the terms in nadel_2026_external_resources.yaml into the file as HERD references."""
    herd = nwbfile.external_resources
    is_new_herd = herd is None
    if is_new_herd:
        herd = HERD()
    elif nwbfile.get_read_io() is not None:
        return  # references already stored on disk cannot be extended

    def annotate(container, kind, value, attribute=None):
        found = (terms.get(kind) or {}).get(value) or []
        key = value
        for term in found if isinstance(found, list) else [found]:
            herd.add_ref(
                container=container, attribute=attribute, key=key, entity_id=term["id"], entity_uri=term["uri"]
            )
            if isinstance(key, str):
                # Several terms for one value share one key; a second string key would duplicate the references.
                key = herd.get_key(key_name=value)
                key = key[-1] if isinstance(key, list) else key

    # Scalar fields of the file and the subject
    if nwbfile.institution:
        annotate(nwbfile, "institution", nwbfile.institution, attribute="institution")
    for experimenter in nwbfile.experimenter or []:
        annotate(nwbfile, "experimenter", experimenter, attribute="experimenter")
    if nwbfile.subject is not None:
        for field in ("species", "strain"):
            if getattr(nwbfile.subject, field, None):
                annotate(nwbfile.subject, field, getattr(nwbfile.subject, field), attribute=field)

    # Every anatomical `location` (table columns and scalar attributes)
    for neurodata_object in nwbfile.all_children():
        if isinstance(neurodata_object, DynamicTable) and "location" in neurodata_object.colnames:
            column = neurodata_object["location"]
            for value in dict.fromkeys(column.data):
                annotate(column, "brain_regions", value)
        elif isinstance(getattr(neurodata_object, "location", None), str):
            annotate(neurodata_object, "brain_regions", neurodata_object.location, attribute="location")

    if is_new_herd and len(herd.keys) > 0:
        nwbfile.external_resources = herd
