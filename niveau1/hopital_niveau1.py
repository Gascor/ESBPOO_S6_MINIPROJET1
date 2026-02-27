from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


class ErreurMetierHospitaliere(Exception):
    """Exception metier levee lorsque une regle hospitaliere est violee."""


@dataclass
class Personne(ABC):
    nom: str
    prenom: str
    date_naissance: date


@dataclass
class DossierMedical:
    numero_dossier: str
    actes: List["ActeMedical"] = field(default_factory=list)

    def ajouter_acte(self, acte: "ActeMedical") -> None:
        self.actes.append(acte)

    def historique(self) -> List["ActeMedical"]:
        return list(self.actes)


@dataclass
class Patient(Personne):
    numero_securite_sociale: str
    adresse_postale: str
    telephone: str
    email: str
    numero_mutuelle: Optional[str] = None
    dossier_medical: Optional[DossierMedical] = None

    def __post_init__(self) -> None:
        if self.dossier_medical is None:
            suffix = self.numero_securite_sociale[-6:]
            self.dossier_medical = DossierMedical(numero_dossier=f"DOS-{suffix}")


@dataclass
class PersonnelMedical(Personne, ABC):
    date_debut_fonction: date
    type_contrat: str
    telephone: str
    email: str


@dataclass
class Medecin(PersonnelMedical):
    pass


@dataclass
class Infirmier(PersonnelMedical):
    pass


@dataclass
class Chirurgien(PersonnelMedical):
    pass


@dataclass
class ActeMedical(ABC):
    date_acte: date
    patient: Patient
    personnels: List[PersonnelMedical]
    est_realise: bool = field(default=False, init=False)
    dossier: DossierMedical = field(init=False)

    def __post_init__(self) -> None:
        if not self.personnels:
            raise ErreurMetierHospitaliere(
                "Un acte medical doit etre affecte a au moins un personnel."
            )
        if self.patient.dossier_medical is None:
            raise ErreurMetierHospitaliere("Le patient doit posseder un dossier medical.")
        self.dossier = self.patient.dossier_medical

    def realiser(self) -> None:
        if self.est_realise:
            raise ErreurMetierHospitaliere("Cet acte medical a deja ete realise.")
        self.verifier_habilitation()
        self.dossier.ajouter_acte(self)
        self.est_realise = True

    @abstractmethod
    def verifier_habilitation(self) -> None:
        """Verifie que le ou les personnels sont habilites pour l'acte."""


@dataclass
class Consultation(ActeMedical):
    def verifier_habilitation(self) -> None:
        if len(self.personnels) != 1 or not isinstance(self.personnels[0], Medecin):
            raise ErreurMetierHospitaliere(
                "Une consultation doit etre realisee par un seul medecin."
            )


@dataclass
class Soin(ActeMedical):
    def verifier_habilitation(self) -> None:
        if len(self.personnels) != 1 or not isinstance(self.personnels[0], Infirmier):
            raise ErreurMetierHospitaliere(
                "Un soin doit etre realise par un seul infirmier."
            )


@dataclass
class InterventionChirurgicale(ActeMedical):
    def verifier_habilitation(self) -> None:
        if any(not isinstance(personnel, Chirurgien) for personnel in self.personnels):
            raise ErreurMetierHospitaliere(
                "Une intervention chirurgicale doit etre realisee par un ou plusieurs chirurgiens."
            )


def _demo() -> None:
    patient = Patient(
        nom="Durand",
        prenom="Alice",
        date_naissance=date(1998, 4, 12),
        numero_securite_sociale="2980412756012",
        numero_mutuelle="MUT-8842",
        adresse_postale="12 rue des Fleurs, 78000 Versailles",
        telephone="0601020304",
        email="alice.durand@example.com",
    )

    medecin = Medecin(
        nom="Martin",
        prenom="Paul",
        date_naissance=date(1980, 3, 1),
        date_debut_fonction=date(2020, 1, 10),
        type_contrat="CDI",
        telephone="0600000001",
        email="paul.martin@hopital.fr",
    )
    infirmier = Infirmier(
        nom="Petit",
        prenom="Lea",
        date_naissance=date(1990, 7, 5),
        date_debut_fonction=date(2021, 6, 1),
        type_contrat="CDI",
        telephone="0600000002",
        email="lea.petit@hopital.fr",
    )
    chirurgien = Chirurgien(
        nom="Bernard",
        prenom="Nora",
        date_naissance=date(1975, 11, 23),
        date_debut_fonction=date(2018, 9, 15),
        type_contrat="CDI",
        telephone="0600000003",
        email="nora.bernard@hopital.fr",
    )

    Consultation(date.today(), patient, [medecin]).realiser()
    Soin(date.today(), patient, [infirmier]).realiser()
    InterventionChirurgicale(date.today(), patient, [chirurgien]).realiser()

    try:
        Soin(date.today(), patient, [medecin]).realiser()
    except ErreurMetierHospitaliere as exc:
        print(f"Erreur metier attendue: {exc}")

    print(f"Numero dossier: {patient.dossier_medical.numero_dossier}")
    print(f"Nombre d'actes: {len(patient.dossier_medical.historique())}")


if __name__ == "__main__":
    _demo()
