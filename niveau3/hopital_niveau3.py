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
class Ville:
    nom: str
    code_postal: str


@dataclass
class Departement:
    code: str
    villes: List[Ville] = field(default_factory=list)

    def ajouter_ville(self, ville: Ville) -> None:
        if ville not in self.villes:
            self.villes.append(ville)

    def contient_ville(self, ville: Ville) -> bool:
        return ville in self.villes


@dataclass
class Region:
    nom: str
    departements: List[Departement] = field(default_factory=list)

    def ajouter_departement(self, departement: Departement) -> None:
        if departement not in self.departements:
            self.departements.append(departement)

    def contient_ville(self, ville: Ville) -> bool:
        return any(departement.contient_ville(ville) for departement in self.departements)


@dataclass
class Personne(ABC):
    nom: str
    prenom: str
    date_naissance: date


@dataclass
class CentreHospitalier:
    nom: str
    ville: Ville
    personnels: List["PersonnelMedical"] = field(default_factory=list)

    def ajouter_personnel(self, personnel: "PersonnelMedical") -> None:
        if personnel not in self.personnels:
            self.personnels.append(personnel)
        if self not in personnel.centres_rattaches:
            personnel.centres_rattaches.append(self)


@dataclass
class TransfertDossier:
    date_transfert: datetime
    ancien_centre: CentreHospitalier
    nouveau_centre: CentreHospitalier


@dataclass
class DossierMedical:
    numero_dossier: str
    centre_reference: CentreHospitalier
    actes: List["ActeMedical"] = field(default_factory=list)
    transferts: List[TransfertDossier] = field(default_factory=list)

    def ajouter_acte(self, acte: "ActeMedical") -> None:
        self.actes.append(acte)

    def enregistrer_transfert(
        self,
        ancien_centre: CentreHospitalier,
        nouveau_centre: CentreHospitalier,
        date_transfert: datetime,
    ) -> None:
        self.transferts.append(
            TransfertDossier(
                date_transfert=date_transfert,
                ancien_centre=ancien_centre,
                nouveau_centre=nouveau_centre,
            )
        )
        self.centre_reference = nouveau_centre

    def historique(self) -> List["ActeMedical"]:
        return list(self.actes)


@dataclass
class Patient(Personne):
    numero_securite_sociale: str
    adresse_postale: str
    telephone: str
    email: str
    ville_residence: Ville
    region_residence: Region
    centre_actuel: CentreHospitalier
    numero_mutuelle: Optional[str] = None
    dossier_medical: Optional[DossierMedical] = None
    rendez_vous: List["RendezVous"] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if not self.region_residence.contient_ville(self.ville_residence):
            raise ErreurMetierHospitaliere(
                "La ville de residence du patient doit appartenir a sa region."
            )
        if self.dossier_medical is None:
            suffix = self.numero_securite_sociale[-6:]
            self.dossier_medical = DossierMedical(
                numero_dossier=f"DOS-{suffix}",
                centre_reference=self.centre_actuel,
            )

    def ajouter_rendez_vous(self, rdv: "RendezVous") -> None:
        self.rendez_vous.append(rdv)

    def transferer_dossier(
        self, nouveau_centre: CentreHospitalier, date_transfert: datetime
    ) -> None:
        if nouveau_centre == self.centre_actuel:
            raise ErreurMetierHospitaliere(
                "Transfert inutile: le patient est deja dans ce centre."
            )
        if self.dossier_medical is None:
            raise ErreurMetierHospitaliere("Le patient ne possede pas de dossier medical.")
        ancien_centre = self.centre_actuel
        self.dossier_medical.enregistrer_transfert(
            ancien_centre=ancien_centre,
            nouveau_centre=nouveau_centre,
            date_transfert=date_transfert,
        )
        self.centre_actuel = nouveau_centre


@dataclass
class PersonnelMedical(Personne, ABC):
    date_debut_fonction: date
    type_contrat: str
    telephone: str
    email: str
    centres_rattaches: List[CentreHospitalier] = field(default_factory=list, init=False)
    centre_disponible: Optional[CentreHospitalier] = field(default=None, init=False)

    def rattacher_a_centre(self, centre: CentreHospitalier) -> None:
        if centre not in self.centres_rattaches:
            self.centres_rattaches.append(centre)
        if self not in centre.personnels:
            centre.personnels.append(self)

    def definir_disponibilite(self, centre: CentreHospitalier) -> None:
        if centre not in self.centres_rattaches:
            raise ErreurMetierHospitaliere(
                "Disponibilite refusee: le personnel n'est pas rattache a ce centre."
            )
        self.centre_disponible = centre

    def est_disponible_dans(self, centre: CentreHospitalier) -> bool:
        return self.centre_disponible == centre


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
    centre: CentreHospitalier
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
        if any(
            not isinstance(personnel, (Chirurgien, Infirmier))
            for personnel in self.personnels
        ):
            raise ErreurMetierHospitaliere(
                "Une intervention ne peut impliquer que chirurgien(s) et infirmier(s)."
            )
        contient_chirurgien = any(
            isinstance(personnel, Chirurgien) for personnel in self.personnels
        )
        contient_infirmier = any(
            isinstance(personnel, Infirmier) for personnel in self.personnels
        )
        if not (contient_chirurgien and contient_infirmier):
            raise ErreurMetierHospitaliere(
                "Une intervention chirurgicale doit avoir au moins un chirurgien et un infirmier."
            )


@dataclass
class RendezVous:
    id_rendez_vous: str
    date_heure: datetime
    patient: Patient
    centre: CentreHospitalier
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

        if any(
            not isinstance(personnel, (Chirurgien, Infirmier))
            for personnel in self.personnels
        ):
            raise ErreurMetierHospitaliere(
                "Un rendez-vous d'intervention ne peut impliquer que chirurgien(s) et infirmier(s)."
            )
        contient_chirurgien = any(
            isinstance(personnel, Chirurgien) for personnel in self.personnels
        )
        contient_infirmier = any(
            isinstance(personnel, Infirmier) for personnel in self.personnels
        )
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
            return Consultation(
                self.date_heure, self.patient, self.centre, list(self.personnels)
            )
        if self.type_acte == TypeActeMedical.SOIN:
            return Soin(self.date_heure, self.patient, self.centre, list(self.personnels))
        return InterventionChirurgicale(
            self.date_heure, self.patient, self.centre, list(self.personnels)
        )


@dataclass
class ReseauHospitalier:
    centres: List[CentreHospitalier]
    rendez_vous: Dict[str, RendezVous] = field(default_factory=dict)

    def actes_disponibles(self) -> List[TypeActeMedical]:
        return list(TypeActeMedical)

    def transferer_patient(
        self,
        patient: Patient,
        nouveau_centre: CentreHospitalier,
        date_transfert: datetime,
    ) -> None:
        self._verifier_centre_existant(nouveau_centre)
        patient.transferer_dossier(nouveau_centre, date_transfert)

    def creer_rendez_vous(
        self,
        id_rdv: str,
        date_heure: datetime,
        patient: Patient,
        centre: CentreHospitalier,
        type_acte: TypeActeMedical,
        personnels: List[PersonnelMedical],
    ) -> RendezVous:
        if id_rdv in self.rendez_vous:
            raise ErreurMetierHospitaliere(f"Le rendez-vous '{id_rdv}' existe deja.")

        self._verifier_centre_existant(centre)
        self._verifier_patient_region(patient, centre)
        self._verifier_personnels_affectables(centre, personnels)

        rdv = RendezVous(
            id_rendez_vous=id_rdv,
            date_heure=date_heure,
            patient=patient,
            centre=centre,
            type_acte=type_acte,
            personnels=personnels,
        )
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
        self,
        date_heure: datetime,
        centre: CentreHospitalier,
        type_acte: TypeActeMedical,
    ) -> int:
        self._verifier_centre_existant(centre)
        disponibles = self._personnels_disponibles_par_type(date_heure, centre)
        if type_acte == TypeActeMedical.CONSULTATION:
            return disponibles["medecin"]
        if type_acte == TypeActeMedical.SOIN:
            return disponibles["infirmier"]
        return min(disponibles["chirurgien"], disponibles["infirmier"])

    def _personnels_disponibles_par_type(
        self, date_heure: datetime, centre: CentreHospitalier
    ) -> Dict[str, int]:
        personnels_occupes_ids = {
            id(personnel)
            for rdv in self.rendez_vous.values()
            if rdv.statut == StatutRendezVous.PLANIFIE and rdv.date_heure == date_heure
            for personnel in rdv.personnels
        }
        candidats = [
            personnel
            for personnel in centre.personnels
            if personnel.est_disponible_dans(centre)
            and id(personnel) not in personnels_occupes_ids
        ]
        return {
            "medecin": sum(1 for personnel in candidats if isinstance(personnel, Medecin)),
            "infirmier": sum(
                1 for personnel in candidats if isinstance(personnel, Infirmier)
            ),
            "chirurgien": sum(
                1 for personnel in candidats if isinstance(personnel, Chirurgien)
            ),
        }

    def _verifier_centre_existant(self, centre: CentreHospitalier) -> None:
        if centre not in self.centres:
            raise ErreurMetierHospitaliere(
                f"Centre non gere par le reseau: {centre.nom}."
            )

    def _verifier_patient_region(
        self, patient: Patient, centre: CentreHospitalier
    ) -> None:
        if not patient.region_residence.contient_ville(centre.ville):
            raise ErreurMetierHospitaliere(
                "Rendez-vous refuse: ce centre n'appartient pas a la region du patient."
            )

    def _verifier_personnels_affectables(
        self, centre: CentreHospitalier, personnels: List[PersonnelMedical]
    ) -> None:
        for personnel in personnels:
            if personnel not in centre.personnels:
                raise ErreurMetierHospitaliere(
                    f"Personnel non rattache au centre {centre.nom}: {personnel.prenom} {personnel.nom}."
                )
            if not personnel.est_disponible_dans(centre):
                raise ErreurMetierHospitaliere(
                    f"Personnel indisponible dans le centre {centre.nom}: {personnel.prenom} {personnel.nom}."
                )

    def _obtenir_rendez_vous(self, id_rdv: str) -> RendezVous:
        if id_rdv not in self.rendez_vous:
            raise ErreurMetierHospitaliere(f"Rendez-vous '{id_rdv}' introuvable.")
        return self.rendez_vous[id_rdv]

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
    versailles = Ville("Versailles", "78000")
    mantes = Ville("Mantes-la-Jolie", "78200")
    rouen = Ville("Rouen", "76000")

    dep78 = Departement(code="78", villes=[versailles, mantes])
    dep76 = Departement(code="76", villes=[rouen])

    ile_de_france = Region(nom="Ile-de-France", departements=[dep78])
    normandie = Region(nom="Normandie", departements=[dep76])

    centre_versailles = CentreHospitalier(nom="CH Versailles", ville=versailles)
    centre_mantes = CentreHospitalier(nom="CH Mantes", ville=mantes)
    centre_rouen = CentreHospitalier(nom="CH Rouen", ville=rouen)

    medecin = Medecin(
        nom="Martin",
        prenom="Paul",
        date_naissance=date(1980, 3, 1),
        date_debut_fonction=date(2020, 1, 10),
        type_contrat="CDI",
        telephone="0600000001",
        email="paul.martin@hopital.fr",
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
    infirmier_versailles = Infirmier(
        nom="Petit",
        prenom="Lea",
        date_naissance=date(1990, 7, 5),
        date_debut_fonction=date(2021, 6, 1),
        type_contrat="CDI",
        telephone="0600000002",
        email="lea.petit@hopital.fr",
    )
    infirmier_mantes = Infirmier(
        nom="Morel",
        prenom="Iris",
        date_naissance=date(1992, 1, 17),
        date_debut_fonction=date(2022, 4, 3),
        type_contrat="CDI",
        telephone="0600000004",
        email="iris.morel@hopital.fr",
    )

    medecin.rattacher_a_centre(centre_versailles)
    medecin.rattacher_a_centre(centre_mantes)
    chirurgien.rattacher_a_centre(centre_versailles)
    chirurgien.rattacher_a_centre(centre_mantes)
    infirmier_versailles.rattacher_a_centre(centre_versailles)
    infirmier_mantes.rattacher_a_centre(centre_mantes)

    medecin.definir_disponibilite(centre_versailles)
    chirurgien.definir_disponibilite(centre_versailles)
    infirmier_versailles.definir_disponibilite(centre_versailles)
    infirmier_mantes.definir_disponibilite(centre_mantes)

    patient = Patient(
        nom="Durand",
        prenom="Alice",
        date_naissance=date(1998, 4, 12),
        numero_securite_sociale="2980412756012",
        numero_mutuelle="MUT-8842",
        adresse_postale="12 rue des Fleurs, 78000 Versailles",
        telephone="0601020304",
        email="alice.durand@example.com",
        ville_residence=versailles,
        region_residence=ile_de_france,
        centre_actuel=centre_versailles,
    )

    reseau = ReseauHospitalier(
        centres=[centre_versailles, centre_mantes, centre_rouen]
    )

    maintenant = datetime.now()
    creneau_consultation = maintenant + timedelta(days=3)
    creneau_intervention = maintenant + timedelta(days=6)

    reseau.creer_rendez_vous(
        id_rdv="RDV3-001",
        date_heure=creneau_consultation,
        patient=patient,
        centre=centre_versailles,
        type_acte=TypeActeMedical.CONSULTATION,
        personnels=[medecin],
    )
    reseau.realiser_rendez_vous("RDV3-001")

    try:
        reseau.creer_rendez_vous(
            id_rdv="RDV3-002",
            date_heure=maintenant + timedelta(days=4),
            patient=patient,
            centre=centre_rouen,
            type_acte=TypeActeMedical.CONSULTATION,
            personnels=[medecin],
        )
    except ErreurMetierHospitaliere as exc:
        print(f"Erreur attendue (centre hors region): {exc}")

    reseau.transferer_patient(
        patient=patient,
        nouveau_centre=centre_mantes,
        date_transfert=maintenant + timedelta(days=5),
    )

    medecin.definir_disponibilite(centre_mantes)
    chirurgien.definir_disponibilite(centre_mantes)

    try:
        reseau.creer_rendez_vous(
            id_rdv="RDV3-003",
            date_heure=maintenant + timedelta(days=7),
            patient=patient,
            centre=centre_versailles,
            type_acte=TypeActeMedical.CONSULTATION,
            personnels=[medecin],
        )
    except ErreurMetierHospitaliere as exc:
        print(f"Erreur attendue (personnel pas disponible dans ce centre): {exc}")

    reseau.creer_rendez_vous(
        id_rdv="RDV3-004",
        date_heure=creneau_intervention,
        patient=patient,
        centre=centre_mantes,
        type_acte=TypeActeMedical.INTERVENTION_CHIRURGICALE,
        personnels=[chirurgien, infirmier_mantes],
    )
    reseau.realiser_rendez_vous("RDV3-004")

    print(f"Region patient: {patient.region_residence.nom}")
    print(f"Centre actuel du patient: {patient.centre_actuel.nom}")
    print(f"Nombre de transferts de dossier: {len(patient.dossier_medical.transferts)}")
    print(f"Nombre d'actes dans le dossier: {len(patient.dossier_medical.historique())}")
    print(
        "Capacite consultation CH Mantes:",
        reseau.nombre_rendez_vous_disponibles(
            maintenant + timedelta(days=8),
            centre_mantes,
            TypeActeMedical.CONSULTATION,
        ),
    )
    print(f"Region test complementaire: {normandie.nom}")


if __name__ == "__main__":
    _demo()
