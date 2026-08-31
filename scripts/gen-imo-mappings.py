#!/usr/bin/env python3
"""Generates mappings/msw/v1/*.yaml (IMO Compendium wire-conformance mapping
tables) from a single source of truth. Run: python3 scripts/gen-imo-mappings.py
Deterministic output; do not hand-edit the generated YAMLs."""
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "mappings", "msw", "v1")

IDENT7 = [
    ("vesselName", "string", None, True, "Ship/Name", None),
    ("vesselImoNumber", "string", r"^[0-9]{7}$", True, "Ship/IMONumber",
     "Declaration/Consignment/TransportMeans/Identification"),
    ("callSign", "string", None, False, "Ship/CallSign", None),
    ("flagCode", "string", r"^[A-Z]{2}$", True, "Ship/FlagState",
     "Declaration/Consignment/TransportMeans/RegistrationNationality"),
    ("masterName", "string", None, True, "Ship/MasterName", None),
]

def ship_identity(msg):
    return [(p, t, pat, m, f"{msg}/{ip}", w) for (p, t, pat, m, ip, w) in IDENT7]

FORMS = {
    "FAL1": {
        "imoMessage": "IMOCompendium/GeneralDeclaration",
        "fields": ship_identity("IMOCompendium/GeneralDeclaration") + [
            ("registryPort", "string", None, False, "IMOCompendium/GeneralDeclaration/Ship/RegistryPort", None),
            ("registryDate", "string", r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", False, "IMOCompendium/GeneralDeclaration/Ship/RegistryDate", None),
            ("registryNumber", "string", None, False, "IMOCompendium/GeneralDeclaration/Ship/RegistryNumber", None),
            ("agentName", "string", None, True, "IMOCompendium/GeneralDeclaration/Agent/Name", None),
            ("agentContact", "string", None, False, "IMOCompendium/GeneralDeclaration/Agent/Contact", None),
            ("grossTonnage", "number", None, True, "IMOCompendium/GeneralDeclaration/Ship/GrossTonnage", None),
            ("netTonnage", "number", None, False, "IMOCompendium/GeneralDeclaration/Ship/NetTonnage", None),
            ("positionInPort", "string", None, False, "IMOCompendium/GeneralDeclaration/Voyage/BerthPosition", None),
            ("purposeOfCall", "string", None, True, "IMOCompendium/GeneralDeclaration/Voyage/PurposeOfCall", None),
            ("arrivalDateTime", "datetime", None, True, "IMOCompendium/GeneralDeclaration/Voyage/ArrivalDateTime", None),
            ("departureDateTime", "datetime", None, False, "IMOCompendium/GeneralDeclaration/Voyage/DepartureDateTime", None),
            ("lastPortCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", True, "IMOCompendium/GeneralDeclaration/Voyage/LastPortOfCall", "Declaration/Consignment/AdditionalInformation/Location/Identification"),
            ("nextPortCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", False, "IMOCompendium/GeneralDeclaration/Voyage/NextPortOfCall", None),
            ("cargoDescription", "string", None, False, "IMOCompendium/GeneralDeclaration/Cargo/BriefDescription", None),
        ],
        "extensions": [("portCallId", "Anchor to the port-interoperability boundary port-call record; platform-internal correlation, no IMO element.")],
    },
    "FAL2": {
        "imoMessage": "IMOCompendium/CargoDeclaration",
        "fields": ship_identity("IMOCompendium/CargoDeclaration") + [
            ("portOfLoadingCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", True, "IMOCompendium/CargoDeclaration/Voyage/PortOfLoading", "Declaration/Consignment/LoadingLocation/Identification"),
            ("portOfDischargeCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", True, "IMOCompendium/CargoDeclaration/Voyage/PortOfDischarge", "Declaration/Consignment/UnloadingLocation/Identification"),
            ("cargoItems", "array", None, True, "IMOCompendium/CargoDeclaration/Cargo/ConsignmentItem", "Declaration/Consignment/GoodsItem", [
                ("marksAndNumbers", "string", None, False, "MarksAndNumbers", None),
                ("packageCount", "integer", None, True, "NumberOfPackages", None),
                ("packageKind", "string", None, True, "KindOfPackages", None),
                ("goodsDescription", "string", None, True, "DescriptionOfGoods", None),
                ("grossWeightKg", "number", None, False, "GrossWeightKg", None),
                ("measurementM3", "number", None, False, "MeasurementCubicMetres", None),
            ]),
        ],
        "extensions": [("portCallId", "Anchor to the port-interoperability boundary port-call record; platform-internal correlation, no IMO element.")],
    },
    "FAL3": {
        "imoMessage": "IMOCompendium/ShipsStoresDeclaration",
        "fields": ship_identity("IMOCompendium/ShipsStoresDeclaration") + [
            ("portCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", True, "IMOCompendium/ShipsStoresDeclaration/Voyage/PortOfArrival", None),
            ("arrivalDateTime", "datetime", None, True, "IMOCompendium/ShipsStoresDeclaration/Voyage/ArrivalDateTime", None),
            ("personsOnBoardCount", "integer", None, False, "IMOCompendium/ShipsStoresDeclaration/Voyage/PersonsOnBoard", None),
            ("periodOfStay", "string", None, False, "IMOCompendium/ShipsStoresDeclaration/Voyage/PeriodOfStay", None),
            ("storesItems", "array", None, True, "IMOCompendium/ShipsStoresDeclaration/Stores/Article", "Declaration/GoodsItem", [
                ("articleName", "string", None, True, "ArticleName", None),
                ("quantity", "number", None, True, "Quantity", None),
                ("quantityUnit", "string", None, True, "QuantityUnit", None),
                ("locationOnBoard", "string", None, False, "PlaceOfStorageOnBoard", None),
            ]),
        ],
        "extensions": [("portCallId", "Anchor to the port-interoperability boundary port-call record; platform-internal correlation, no IMO element.")],
    },
    "FAL4": {
        "imoMessage": "IMOCompendium/CrewsEffectsDeclaration",
        "fields": ship_identity("IMOCompendium/CrewsEffectsDeclaration") + [
            ("portCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", True, "IMOCompendium/CrewsEffectsDeclaration/Voyage/PortOfArrival", None),
            ("arrivalDateTime", "datetime", None, True, "IMOCompendium/CrewsEffectsDeclaration/Voyage/ArrivalDateTime", None),
            ("crewEffects", "array", None, True, "IMOCompendium/CrewsEffectsDeclaration/CrewEffects/Item", "Declaration/GoodsItem", [
                ("familyName", "string", None, True, "CrewMember/FamilyName", None),
                ("givenNames", "string", None, True, "CrewMember/GivenNames", None),
                ("rankOrRating", "string", None, True, "CrewMember/RankOrRating", None),
                ("effectsDescription", "string", None, True, "EffectsInExcessOfAllowance/Description", None),
                ("quantity", "number", None, True, "EffectsInExcessOfAllowance/Quantity", None),
                ("dutiableIndicator", "boolean", None, False, "EffectsInExcessOfAllowance/DutiableIndicator", None),
            ]),
        ],
        "extensions": [("portCallId", "Anchor to the port-interoperability boundary port-call record; platform-internal correlation, no IMO element.")],
    },
    "FAL5": {
        "imoMessage": "IMOCompendium/CrewList",
        "fields": ship_identity("IMOCompendium/CrewList") + [
            ("portCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", True, "IMOCompendium/CrewList/Voyage/PortOfArrival", None),
            ("arrivalDateTime", "datetime", None, True, "IMOCompendium/CrewList/Voyage/ArrivalDateTime", None),
            ("crew", "array", None, True, "IMOCompendium/CrewList/Crew/CrewMember", "Declaration/Consignment/TransportContractDocument", [
                ("familyName", "string", None, True, "FamilyName", None),
                ("givenNames", "string", None, True, "GivenNames", None),
                ("nationalityCode", "string", r"^[A-Z]{2}$", True, "Nationality", None),
                ("rankOrRating", "string", None, True, "RankOrRating", None),
                ("dateOfBirth", "string", r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", True, "DateOfBirth", None),
                ("placeOfBirth", "string", None, False, "PlaceOfBirth", None),
                ("identityDocumentType", "string", None, True, "IdentityDocument/Type", None),
                ("identityDocumentNumber", "string", None, True, "IdentityDocument/Number", None),
                ("identityDocumentExpiry", "string", r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", False, "IdentityDocument/ExpiryDate", None),
                ("portOfEmbarkationCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", False, "Embarkation/Port", None),
                ("dateOfEmbarkation", "string", r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", False, "Embarkation/Date", None),
            ]),
        ],
        "extensions": [("portCallId", "Anchor to the port-interoperability boundary port-call record; platform-internal correlation, no IMO element.")],
    },
    "FAL6": {
        "imoMessage": "IMOCompendium/PassengerList",
        "fields": ship_identity("IMOCompendium/PassengerList") + [
            ("portCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", True, "IMOCompendium/PassengerList/Voyage/PortOfArrival", None),
            ("arrivalDateTime", "datetime", None, True, "IMOCompendium/PassengerList/Voyage/ArrivalDateTime", None),
            ("passengers", "array", None, True, "IMOCompendium/PassengerList/Passenger/Item", None, [
                ("familyName", "string", None, True, "FamilyName", None),
                ("givenNames", "string", None, True, "GivenNames", None),
                ("nationalityCode", "string", r"^[A-Z]{2}$", True, "Nationality", None),
                ("dateOfBirth", "string", r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", True, "DateOfBirth", None),
                ("placeOfBirth", "string", None, False, "PlaceOfBirth", None),
                ("identityDocumentType", "string", None, True, "IdentityDocument/Type", None),
                ("identityDocumentNumber", "string", None, True, "IdentityDocument/Number", None),
                ("portOfEmbarkationCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", True, "Embarkation/Port", None),
                ("portOfDisembarkationCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", True, "Disembarkation/Port", None),
                ("transitIndicator", "boolean", None, False, "TransitPassengerIndicator", None),
            ]),
        ],
        "extensions": [("portCallId", "Anchor to the port-interoperability boundary port-call record; platform-internal correlation, no IMO element.")],
    },
    "FAL7": {
        "imoMessage": "IMOCompendium/DangerousGoodsManifest",
        "fields": ship_identity("IMOCompendium/DangerousGoodsManifest") + [
            ("portOfLoadingCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", True, "IMOCompendium/DangerousGoodsManifest/Voyage/PortOfLoading", None),
            ("portOfDischargeCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", True, "IMOCompendium/DangerousGoodsManifest/Voyage/PortOfDischarge", None),
            ("dangerousGoodsItems", "array", None, True, "IMOCompendium/DangerousGoodsManifest/DangerousGoods/Item", "Declaration/Consignment/GoodsItem", [
                ("unNumber", "string", r"^[0-9]{4}$", True, "UNDGNumber", None),
                ("properShippingName", "string", None, True, "ProperShippingName", None),
                ("hazardClass", "string", None, True, "IMDGClass", None),
                ("packingGroup", "string", None, False, "PackingGroup", None),
                ("subsidiaryRisks", "string", None, False, "SubsidiaryRisks", None),
                ("marinePollutantIndicator", "boolean", None, True, "MarinePollutantIndicator", None),
                ("flashpointCelsius", "number", None, False, "FlashpointCelsius", None),
                ("packageCount", "integer", None, True, "NumberAndKindOfPackages/Count", None),
                ("packageKind", "string", None, True, "NumberAndKindOfPackages/Kind", None),
                ("quantity", "number", None, False, "MassOrVolume/Quantity", None),
                ("stowagePosition", "string", None, False, "StowagePositionOnBoard", None),
            ]),
        ],
        "extensions": [("portCallId", "Anchor to the port-interoperability boundary port-call record; platform-internal correlation, no IMO element.")],
    },
    "MDOH": {
        "imoMessage": "IMOCompendium/MaritimeDeclarationOfHealth",
        "fields": [
            ("vesselName", "string", None, True, "IMOCompendium/MaritimeDeclarationOfHealth/Ship/Name", None),
            ("vesselImoNumber", "string", r"^[0-9]{7}$", True, "IMOCompendium/MaritimeDeclarationOfHealth/Ship/IMONumber", None),
            ("flagCode", "string", r"^[A-Z]{2}$", True, "IMOCompendium/MaritimeDeclarationOfHealth/Ship/FlagState", None),
            ("masterName", "string", None, True, "IMOCompendium/MaritimeDeclarationOfHealth/Ship/MasterName", None),
            ("portCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", True, "IMOCompendium/MaritimeDeclarationOfHealth/Voyage/PortOfArrival", None),
            ("arrivalDateTime", "datetime", None, True, "IMOCompendium/MaritimeDeclarationOfHealth/Voyage/ArrivalDateTime", None),
            ("lastPortCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", True, "IMOCompendium/MaritimeDeclarationOfHealth/Voyage/LastPortOfCall", None),
            ("crewCount", "integer", None, True, "IMOCompendium/MaritimeDeclarationOfHealth/Health/CrewCount", None),
            ("passengerCount", "integer", None, True, "IMOCompendium/MaritimeDeclarationOfHealth/Health/PassengerCount", None),
            ("deathOnBoardIndicator", "boolean", None, True, "IMOCompendium/MaritimeDeclarationOfHealth/Health/DeathOnBoardIndicator", None),
            ("diseaseOnBoardIndicator", "boolean", None, True, "IMOCompendium/MaritimeDeclarationOfHealth/Health/DiseaseOnBoardIndicator", None),
            ("sanitaryMeasuresAppliedIndicator", "boolean", None, True, "IMOCompendium/MaritimeDeclarationOfHealth/Health/SanitaryMeasuresAppliedIndicator", None),
            ("sanitaryControlCertificateType", "string", None, True, "IMOCompendium/MaritimeDeclarationOfHealth/Health/ShipSanitationControlCertificate/Type", None),
            ("sanitaryControlCertificateExpiry", "string", r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", False, "IMOCompendium/MaritimeDeclarationOfHealth/Health/ShipSanitationControlCertificate/ExpiryDate", None),
            ("visitedAffectedAreaIndicator", "boolean", None, True, "IMOCompendium/MaritimeDeclarationOfHealth/Health/VisitedAffectedAreaIndicator", None),
            ("portsOfCallLast30Days", "array", None, True, "IMOCompendium/MaritimeDeclarationOfHealth/Voyage/PortsOfCallLastThirtyDays/Item", None, [
                ("portCode", "string", r"^[A-Z]{2}[A-Z0-9]{3}$", True, "Port", None),
                ("departureDate", "string", r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", False, "DepartureDate", None),
            ]),
        ],
        "extensions": [
            ("portCallId", "Anchor to the port-interoperability boundary port-call record; platform-internal correlation, no IMO element."),
            ("submittedByAgentReference", "Tokenized platform reference of the submitting shipping agent; platform-internal provenance, no IMO element."),
        ],
    },
}

HEADER = """# GENERATED by scripts/gen-imo-mappings.py — do not hand-edit.
# IMO Compendium Reference Model mapping table (normative companion of
# docs/imo-wco-conformance.md). imoPath paths follow the Compendium Reference
# Model structure per FAL.5/Circ.45; wcoPath is populated only where a WCO
# Data Model element is established for the concept, else null (honest "no
# established cross-reference").
"""


def emit_field(f, indent):
    pad = " " * indent
    if len(f) == 6:
        platform, ftype, pattern, mandatory, imo, wco = f
        items = None
    else:
        platform, ftype, pattern, mandatory, imo, wco, items = f
    lines = [f"{pad}- platform: {platform}", f"{pad}  type: {ftype}"]
    if pattern:
        lines.append(f"{pad}  pattern: '{pattern}'")
    lines.append(f"{pad}  mandatory: {'true' if mandatory else 'false'}")
    lines.append(f"{pad}  imoPath: {imo}")
    lines.append(f"{pad}  wcoPath: {wco if wco else 'null'}")
    if items is not None:
        lines.append(f"{pad}  repeating: true")
        lines.append(f"{pad}  itemFields:")
        for it in items:
            lines.extend(emit_field(it, indent + 4))
    return lines


def main():
    os.makedirs(OUT, exist_ok=True)
    summary = []
    for form, spec in FORMS.items():
        lines = [HEADER.rstrip(), "", 'mappingVersion: "1.0"', f"form: {form}",
                 f"imoMessage: {spec['imoMessage']}",
                 'reference: "IMO Compendium Reference Model, FAL.5/Circ.45 Annex"',
                 "fields:"]
        mapped = 0
        for f in spec["fields"]:
            lines.extend(emit_field(f, 2))
            mapped += 1
            if len(f) == 7:
                mapped += len(f[6])
        ext_names = [e[0] for e in spec["extensions"]]
        lines.append("extensionFields:")
        for name in ext_names:
            lines.append(f"  - {name}")
        path = os.path.join(OUT, f"{form.lower()}.yaml")
        with open(path, "w") as fh:
            fh.write("\n".join(lines) + "\n")
        summary.append((form, mapped, len(ext_names)))

    reg = [HEADER.rstrip(), "", 'registryVersion: "1.0"',
           "# Platform-only fields honestly registered as extensions (no IMO",
           "# Compendium element). Export places them under",
           "# extensions.blueeconomy.<FORM>.<field>; unregistered extensions",
           "# reject the export (fail closed).", "extensions:"]
    for form, spec in FORMS.items():
        for name, why in spec["extensions"]:
            reg.append(f"  - form: {form}")
            reg.append(f"    field: {name}")
            reg.append(f"    reason: \"{why}\"")
    with open(os.path.join(OUT, "extension-registry.yaml"), "w") as fh:
        fh.write("\n".join(reg) + "\n")

    total_m = sum(s[1] for s in summary)
    total_e = sum(s[2] for s in summary)
    for form, m, e in summary:
        print(f"{form}: mapped={m} extensions={e} total={m+e}")
    print(f"ALL: mapped={total_m} extensions={total_e} total={total_m+total_e}")


if __name__ == "__main__":
    main()
