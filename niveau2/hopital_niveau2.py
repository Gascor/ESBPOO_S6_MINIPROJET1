from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional


class ErreurMetierHospitaliere(Exception):
    """Exception metier levee lorsque une regle hospitaliere est violee."""


class TypeActeMedical(str, Enum):
    CONSULTATION = "Consultation"
    SOIN = "Soin"
    INTERVENTION_CHIRURGICALE = "Intervention chirurgicale"


class StatutRendezVous(str, Enum):
    PLANIFIE = "Planifie"
    ANNULE = "Annule"
    REALISE = "Realise"


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
    rendez_vous: List["RendezVous"] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.dossier_medical is None:
            suffix = self.numero_securite_sociale[-6:]
            self.dossier_medical = DossierMedical(numero_dossier=f"DOS-{suffix}")

    def ajouter_rendez_vous(self, rdv: "RendezVous") -> None:
        self.rendez_vous.append(rdv)


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
    date_acte: datetime
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
        if any(not isinstance(personnel, (Chirurgien, Infirmier)) for personnel in self.personnels):
            raise ErreurMetierHospitaliere(
                "Une intervention ne peut impliquer que chirurgien(s) et infirmier(s)."
            )
        contient_chirurgien = any(isinstance(personnel, Chirurgien) for personnel in self.personnels)
        contient_infirmier = any(isinstance(personnel, Infirmier) for personnel in self.personnels)
        if not (contient_chirurgien and contient_infirmier):
            raise ErreurMetierHospitaliere(
                "Une intervention chirurgicale doit avoir au moins un chirurgien et un infirmier."
            )


@dataclass
class RendezVous:
    id_rendez_vous: str
    date_heure: datetime
    patient: Patient
    type_acte: TypeActeMedical
    personnels: List[PersonnelMedical]
    statut: StatutRendezVous = field(default=StatutRendezVous.PLANIFIE, init=False)

    def __post_init__(self) -> None:
        if not self.personnels:
            raise ErreurMetierHospitaliere(
                "Un rendez-vous doit etre affecte a au moins un personnel medical."
            )
        self.verifier_affectation_personnel()

    def verifier_affectation_personnel(self) -> None:
        if self.type_acte == TypeActeMedical.CONSULTATION:
            if len(self.personnels) != 1 or not isinstance(self.personnels[0], Medecin):
                raise ErreurMetierHospitaliere(
                    "Un rendez-vous de consultation doit etre affecte a un medecin."
                )
            return

        if self.type_acte == TypeActeMedical.SOIN:
            if len(self.personnels) != 1 or not isinstance(self.personnels[0], Infirmier):
                raise ErreurMetierHospitaliere(
                    "Un rendez-vous de soin doit etre affecte a un infirmier."
                )
            return

        if any(not isinstance(personnel, (Chirurgien, Infirmier)) for personnel in self.personnels):
            raise ErreurMetierHospitaliere(
                "Un rendez-vous d'intervention ne peut impliquer que chirurgien(s) et infirmier(s)."
            )
        contient_chirurgien = any(isinstance(personnel, Chirurgien) for personnel in self.personnels)
        contient_infirmier = any(isinstance(personnel, Infirmier) for personnel in self.personnels)
        if not (contient_chirurgien and contient_infirmier):
            raise ErreurMetierHospitaliere(
                "Un rendez-vous d'intervention doit avoir au moins un chirurgien et un infirmier."
            )

    def annuler_par_patient(self, date_demande: datetime) -> None:
        self._verifier_planifie()
        if self.date_heure - date_demande < timedelta(hours=24):
            raise ErreurMetierHospitaliere(
                "Annulation refusee: le patient doit annuler au moins 24h avant le rendez-vous."
            )
        self.statut = StatutRendezVous.ANNULE

    def annuler_par_personnel(self, personnel: PersonnelMedical) -> None:
        self._verifier_planifie()
        if personnel not in self.personnels:
            raise ErreurMetierHospitaliere(
                "Annulation refusee: ce personnel n'est pas affecte a ce rendez-vous."
            )
        self.statut = StatutRendezVous.ANNULE

    def modifier_date(self, nouvelle_date: datetime) -> None:
        self._verifier_planifie()
        self.date_heure = nouvelle_date

    def realiser(self) -> ActeMedical:
        self._verifier_planifie()
        acte = self._construire_acte()
        acte.realiser()
        self.statut = StatutRendezVous.REALISE
        return acte

    def _verifier_planifie(self) -> None:
        if self.statut != StatutRendezVous.PLANIFIE:
            raise ErreurMetierHospitaliere(
                "Operation impossible: le rendez-vous n'est plus a l'etat PLANIFIE."
            )

    def _construire_acte(self) -> ActeMedical:
        if self.type_acte == TypeActeMedical.CONSULTATION:
            return Consultation(self.date_heure, self.patient, list(self.personnels))
        if self.type_acte == TypeActeMedical.SOIN:
            return Soin(self.date_heure, self.patient, list(self.personnels))
        return InterventionChirurgicale(self.date_heure, self.patient, list(self.personnels))


@dataclass
class GestionRendezVous:
    personnels_hopital: List[PersonnelMedical]
    rendez_vous: Dict[str, RendezVous] = field(default_factory=dict)

    def actes_disponibles(self) -> List[TypeActeMedical]:
        return list(TypeActeMedical)

    def creer_rendez_vous(
        self,
        id_rdv: str,
        date_heure: datetime,
        patient: Patient,
        type_acte: TypeActeMedical,
        personnels: List[PersonnelMedical],
    ) -> RendezVous:
        if id_rdv in self.rendez_vous:
            raise ErreurMetierHospitaliere(f"Le rendez-vous '{id_rdv}' existe deja.")

        self._verifier_personnels_connus(personnels)
        rdv = RendezVous(id_rdv, date_heure, patient, type_acte, personnels)
        self._verifier_conflits(
            patient=rdv.patient,
            type_acte=rdv.type_acte,
            personnels=rdv.personnels,
            date_heure=rdv.date_heure,
        )

        self.rendez_vous[id_rdv] = rdv
        patient.ajouter_rendez_vous(rdv)
        return rdv

    def annuler_par_patient(self, id_rdv: str, date_demande: datetime) -> None:
        self._obtenir_rendez_vous(id_rdv).annuler_par_patient(date_demande)

    def annuler_par_personnel(self, id_rdv: str, personnel: PersonnelMedical) -> None:
        self._obtenir_rendez_vous(id_rdv).annuler_par_personnel(personnel)

    def modifier_date_rendez_vous(self, id_rdv: str, nouvelle_date: datetime) -> None:
        rdv = self._obtenir_rendez_vous(id_rdv)
        rdv._verifier_planifie()
        self._verifier_conflits(
            patient=rdv.patient,
            type_acte=rdv.type_acte,
            personnels=rdv.personnels,
            date_heure=nouvelle_date,
            exclure_id=id_rdv,
        )
        rdv.modifier_date(nouvelle_date)

    def realiser_rendez_vous(self, id_rdv: str) -> ActeMedical:
        return self._obtenir_rendez_vous(id_rdv).realiser()

    def nombre_rendez_vous_disponibles(
        self, date_heure: datetime, type_acte: TypeActeMedical
    ) -> int:
        disponibles = self.personnels_disponibles_par_type(date_heure)
        if type_acte == TypeActeMedical.CONSULTATION:
            return disponibles["medecin"]
        if type_acte == TypeActeMedical.SOIN:
            return disponibles["infirmier"]
        return min(disponibles["chirurgien"], disponibles["infirmier"])

    def personnels_disponibles_par_type(self, date_heure: datetime) -> Dict[str, int]:
        personnels_occupes_ids = {
            id(personnel)
            for rdv in self.rendez_vous.values()
            if rdv.statut == StatutRendezVous.PLANIFIE and rdv.date_heure == date_heure
            for personnel in rdv.personnels
        }
        personnels_disponibles = [
            personnel
            for personnel in self.personnels_hopital
            if id(personnel) not in personnels_occupes_ids
        ]

        return {
            "medecin": sum(
                1 for personnel in personnels_disponibles if isinstance(personnel, Medecin)
            ),
            "infirmier": sum(
                1 for personnel in personnels_disponibles if isinstance(personnel, Infirmier)
            ),
            "chirurgien": sum(
                1 for personnel in personnels_disponibles if isinstance(personnel, Chirurgien)
            ),
        }

    def _obtenir_rendez_vous(self, id_rdv: str) -> RendezVous:
        if id_rdv not in self.rendez_vous:
            raise ErreurMetierHospitaliere(f"Rendez-vous '{id_rdv}' introuvable.")
        return self.rendez_vous[id_rdv]

    def _verifier_personnels_connus(self, personnels: List[PersonnelMedical]) -> None:
        for personnel in personnels:
            if personnel not in self.personnels_hopital:
                raise ErreurMetierHospitaliere(
                    f"Personnel non gere par l'hopital: {personnel.prenom} {personnel.nom}."
                )

    def _verifier_conflits(
        self,
        patient: Patient,
        type_acte: TypeActeMedical,
        personnels: List[PersonnelMedical],
        date_heure: datetime,
        exclure_id: Optional[str] = None,
    ) -> None:
        for rdv in self.rendez_vous.values():
            if exclure_id is not None and rdv.id_rendez_vous == exclure_id:
                continue
            if rdv.statut != StatutRendezVous.PLANIFIE or rdv.date_heure != date_heure:
                continue

            if rdv.patient == patient and rdv.type_acte != type_acte:
                raise ErreurMetierHospitaliere(
                    "Conflit planning: le patient a deja un rendez-vous d'un autre type sur ce creneau."
                )

            if any(personnel in rdv.personnels for personnel in personnels):
                raise ErreurMetierHospitaliere(
                    "Conflit planning: un personnel medical est deja occupe sur ce creneau."
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

    gestion = GestionRendezVous(personnels_hopital=[medecin, infirmier, chirurgien])
    maintenant = datetime.now()

    creneau_consultation = maintenant + timedelta(days=3)
    creneau_soin = maintenant + timedelta(days=4)
    creneau_intervention = maintenant + timedelta(days=5)

    gestion.creer_rendez_vous(
        id_rdv="RDV-001",
        date_heure=creneau_consultation,
        patient=patient,
        type_acte=TypeActeMedical.CONSULTATION,
        personnels=[medecin],
    )

    gestion.creer_rendez_vous(
        id_rdv="RDV-002",
        date_heure=creneau_soin,
        patient=patient,
        type_acte=TypeActeMedical.SOIN,
        personnels=[infirmier],
    )

    gestion.creer_rendez_vous(
        id_rdv="RDV-003",
        date_heure=creneau_intervention,
        patient=patient,
        type_acte=TypeActeMedical.INTERVENTION_CHIRURGICALE,
        personnels=[chirurgien, infirmier],
    )

    try:
        gestion.creer_rendez_vous(
            id_rdv="RDV-004",
            date_heure=creneau_consultation,
            patient=patient,
            type_acte=TypeActeMedical.SOIN,
            personnels=[infirmier],
        )
    except ErreurMetierHospitaliere as exc:
        print(f"Erreur attendue (conflit patient): {exc}")

    try:
        gestion.annuler_par_patient(
            id_rdv="RDV-001",
            date_demande=creneau_consultation - timedelta(hours=12),
        )
    except ErreurMetierHospitaliere as exc:
        print(f"Erreur attendue (annulation < 24h): {exc}")

    gestion.modifier_date_rendez_vous("RDV-002", creneau_soin + timedelta(hours=2))
    gestion.annuler_par_personnel("RDV-002", infirmier)

    gestion.realiser_rendez_vous("RDV-001")
    gestion.realiser_rendez_vous("RDV-003")

    print("Actes disponibles:", [acte.value for acte in gestion.actes_disponibles()])
    print(
        "Capacite restante creneau consultation:",
        gestion.nombre_rendez_vous_disponibles(
            creneau_consultation, TypeActeMedical.CONSULTATION
        ),
    )
    print("Nombre d'actes dans le dossier:", len(patient.dossier_medical.historique()))

    try:
        gestion.creer_rendez_vous(
            id_rdv="RDV-005",
            date_heure=maintenant + timedelta(days=6),
            patient=patient,
            type_acte=TypeActeMedical.INTERVENTION_CHIRURGICALE,
            personnels=[chirurgien],
        )
    except ErreurMetierHospitaliere as exc:
        print(f"Erreur attendue (intervention incomplete): {exc}")


if __name__ == "__main__":
    _demo()
