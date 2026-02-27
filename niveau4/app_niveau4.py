from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List

import sys
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from niveau3.hopital_niveau3 import (  # noqa: E402
    CentreHospitalier,
    Chirurgien,
    Departement,
    ErreurMetierHospitaliere,
    Infirmier,
    Medecin,
    Patient,
    PersonnelMedical,
    Region,
    ReseauHospitalier,
    TypeActeMedical,
    Ville,
)


class AppNiveau4(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Niveau 4 - Application hospitaliere Tkinter")
        self.geometry("1280x820")

        self.regions: Dict[str, Region] = {}
        self.departements: Dict[str, Departement] = {}
        self.villes: Dict[str, Ville] = {}
        self.centres: Dict[str, CentreHospitalier] = {}
        self.personnels: Dict[str, PersonnelMedical] = {}
        self.patients: Dict[str, Patient] = {}
        self.reseau = ReseauHospitalier(centres=[])

        self._build_ui()
        self._refresh_all()
        self._set_defaults()

    def _set_defaults(self) -> None:
        now_dt = datetime.now().strftime("%Y-%m-%d %H:%M")
        now_d = datetime.now().strftime("%Y-%m-%d")
        self.var_staff_birth.set("1980-01-01")
        self.var_staff_start.set(now_d)
        self.var_patient_birth.set("1990-01-01")
        self.var_transfer_date.set(now_dt)
        self.var_rdv_date.set(now_dt)
        self.var_rdv_edit_date.set(now_dt)
        self.var_rdv_cancel_date.set(now_dt)
        self.var_capacity_date.set(now_dt)

    def _parse_date(self, raw: str):
        return datetime.strptime(raw.strip(), "%Y-%m-%d").date()

    def _parse_datetime(self, raw: str):
        return datetime.strptime(raw.strip(), "%Y-%m-%d %H:%M")

    def _city_key(self, city: Ville) -> str:
        return f"{city.nom} ({city.code_postal})"

    def _execute(self, fn) -> None:
        try:
            fn()
        except (ErreurMetierHospitaliere, ValueError) as exc:
            messagebox.showerror("Erreur", str(exc))
        except Exception as exc:  # pragma: no cover
            messagebox.showerror("Erreur technique", str(exc))

    def _set_text(self, widget: ScrolledText, content: str) -> None:
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)
        widget.config(state="disabled")

    def _split_csv(self, value: str) -> List[str]:
        return [part.strip() for part in value.split(",") if part.strip()]

    def _refresh_all(self) -> None:
        region_names = sorted(self.regions.keys())
        dept_codes = sorted(self.departements.keys())
        city_keys = sorted(self.villes.keys())
        center_names = sorted(self.centres.keys())
        staff_emails = sorted(self.personnels.keys())
        patient_nss = sorted(self.patients.keys())
        rdv_ids = sorted(self.reseau.rendez_vous.keys())

        self.cmb_dept_region["values"] = region_names
        self.cmb_city_dept["values"] = dept_codes
        self.cmb_center_city["values"] = city_keys

        self.cmb_patient_city["values"] = city_keys
        self.cmb_patient_region["values"] = region_names
        self.cmb_patient_center["values"] = center_names
        self.cmb_transfer_patient["values"] = patient_nss
        self.cmb_transfer_center["values"] = center_names
        self.cmb_dossier_patient["values"] = patient_nss

        self.cmb_rdv_patient["values"] = patient_nss
        self.cmb_rdv_center["values"] = center_names
        self.cmb_rdv_type["values"] = [acte.name for acte in TypeActeMedical]
        self.cmb_rdv_ops_id["values"] = rdv_ids
        self.cmb_rdv_cancel_staff["values"] = staff_emails
        self.cmb_capacity_center["values"] = center_names
        self.cmb_capacity_type["values"] = [acte.name for acte in TypeActeMedical]

        self.cmb_staff_active_center["values"] = center_names
        self.cmb_staff_manage_email["values"] = staff_emails
        self.cmb_staff_manage_center["values"] = center_names

        self._set_text(self.txt_setup, self._setup_state_text())
        self._set_text(self.txt_staff, self._staff_state_text())
        self._set_text(self.txt_patients, self._patient_state_text())
        self._set_text(self.txt_rdv, self._rdv_state_text())

    def _setup_state_text(self) -> str:
        lines: List[str] = []
        lines.append("Regions:")
        if self.regions:
            lines.extend([f"- {name}" for name in sorted(self.regions)])
        else:
            lines.append("- aucune")
        lines.append("")
        lines.append("Departements:")
        if self.departements:
            for code in sorted(self.departements):
                reg = self._region_name_of_department(code)
                lines.append(f"- {code} (region={reg})")
        else:
            lines.append("- aucun")
        lines.append("")
        lines.append("Villes:")
        if self.villes:
            lines.extend([f"- {key}" for key in sorted(self.villes)])
        else:
            lines.append("- aucune")
        lines.append("")
        lines.append("Centres:")
        if self.centres:
            for name in sorted(self.centres):
                city = self.centres[name].ville
                lines.append(f"- {name} ({city.nom} {city.code_postal})")
        else:
            lines.append("- aucun")
        return "\n".join(lines)

    def _region_name_of_department(self, dept_code: str) -> str:
        dept = self.departements[dept_code]
        for region in self.regions.values():
            if dept in region.departements:
                return region.nom
        return "-"

    def _staff_state_text(self) -> str:
        if not self.personnels:
            return "Aucun personnel."
        lines: List[str] = []
        for email in sorted(self.personnels):
            p = self.personnels[email]
            centers = ", ".join(sorted(c.nom for c in p.centres_rattaches)) or "-"
            active = p.centre_disponible.nom if p.centre_disponible else "-"
            lines.append(
                f"{p.__class__.__name__} | {p.prenom} {p.nom} | {email} | centres=[{centers}] | actif={active}"
            )
        return "\n".join(lines)

    def _patient_state_text(self) -> str:
        if not self.patients:
            return "Aucun patient."
        lines: List[str] = []
        for nss in sorted(self.patients):
            p = self.patients[nss]
            lines.append(
                f"{p.prenom} {p.nom} | nss={nss} | region={p.region_residence.nom} | centre={p.centre_actuel.nom}"
            )
        return "\n".join(lines)

    def _rdv_state_text(self) -> str:
        if not self.reseau.rendez_vous:
            return "Aucun rendez-vous."
        lines: List[str] = []
        for rdv_id in sorted(self.reseau.rendez_vous):
            rdv = self.reseau.rendez_vous[rdv_id]
            staff = ", ".join([f"{p.prenom} {p.nom}" for p in rdv.personnels])
            lines.append(
                f"{rdv.id_rendez_vous} | {rdv.date_heure:%Y-%m-%d %H:%M} | {rdv.type_acte.name} | "
                f"patient={rdv.patient.numero_securite_sociale} | centre={rdv.centre.nom} | "
                f"statut={rdv.statut.name} | staff=[{staff}]"
            )
        return "\n".join(lines)

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_setup = ttk.Frame(notebook, padding=10)
        self.tab_staff = ttk.Frame(notebook, padding=10)
        self.tab_patients = ttk.Frame(notebook, padding=10)
        self.tab_rdv = ttk.Frame(notebook, padding=10)
        self.tab_dossier = ttk.Frame(notebook, padding=10)

        notebook.add(self.tab_setup, text="Setup")
        notebook.add(self.tab_staff, text="Personnels")
        notebook.add(self.tab_patients, text="Patients")
        notebook.add(self.tab_rdv, text="Rendez-vous")
        notebook.add(self.tab_dossier, text="Dossiers")

        self._build_tab_setup()
        self._build_tab_staff()
        self._build_tab_patients()
        self._build_tab_rdv()
        self._build_tab_dossier()

    def _build_tab_setup(self) -> None:
        frame = self.tab_setup
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(1, weight=1)

        self.var_region_name = tk.StringVar()
        self.var_dept_code = tk.StringVar()
        self.var_city_name = tk.StringVar()
        self.var_city_cp = tk.StringVar()
        self.var_center_name = tk.StringVar()

        region_box = ttk.LabelFrame(frame, text="Region")
        region_box.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        ttk.Label(region_box, text="Nom").grid(row=0, column=0, sticky="w")
        ttk.Entry(region_box, textvariable=self.var_region_name).grid(
            row=1, column=0, sticky="ew"
        )
        ttk.Button(region_box, text="Ajouter", command=self._on_add_region).grid(
            row=2, column=0, sticky="ew", pady=4
        )
        region_box.columnconfigure(0, weight=1)

        dept_box = ttk.LabelFrame(frame, text="Departement")
        dept_box.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ttk.Label(dept_box, text="Code").grid(row=0, column=0, sticky="w")
        ttk.Entry(dept_box, textvariable=self.var_dept_code).grid(
            row=1, column=0, sticky="ew"
        )
        ttk.Label(dept_box, text="Region").grid(row=2, column=0, sticky="w")
        self.cmb_dept_region = ttk.Combobox(dept_box, state="readonly")
        self.cmb_dept_region.grid(row=3, column=0, sticky="ew")
        ttk.Button(dept_box, text="Ajouter", command=self._on_add_department).grid(
            row=4, column=0, sticky="ew", pady=4
        )
        dept_box.columnconfigure(0, weight=1)

        city_box = ttk.LabelFrame(frame, text="Ville et centre")
        city_box.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        ttk.Label(city_box, text="Ville").grid(row=0, column=0, sticky="w")
        ttk.Entry(city_box, textvariable=self.var_city_name).grid(row=1, column=0, sticky="ew")
        ttk.Label(city_box, text="Code postal").grid(row=2, column=0, sticky="w")
        ttk.Entry(city_box, textvariable=self.var_city_cp).grid(row=3, column=0, sticky="ew")
        ttk.Label(city_box, text="Departement").grid(row=4, column=0, sticky="w")
        self.cmb_city_dept = ttk.Combobox(city_box, state="readonly")
        self.cmb_city_dept.grid(row=5, column=0, sticky="ew")
        ttk.Button(city_box, text="Ajouter ville", command=self._on_add_city).grid(
            row=6, column=0, sticky="ew", pady=4
        )
        ttk.Label(city_box, text="Centre").grid(row=7, column=0, sticky="w")
        ttk.Entry(city_box, textvariable=self.var_center_name).grid(
            row=8, column=0, sticky="ew"
        )
        ttk.Label(city_box, text="Ville du centre").grid(row=9, column=0, sticky="w")
        self.cmb_center_city = ttk.Combobox(city_box, state="readonly")
        self.cmb_center_city.grid(row=10, column=0, sticky="ew")
        ttk.Button(city_box, text="Ajouter centre", command=self._on_add_center).grid(
            row=11, column=0, sticky="ew", pady=4
        )
        city_box.columnconfigure(0, weight=1)

        self.txt_setup = ScrolledText(frame, wrap="word")
        self.txt_setup.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

    def _build_tab_staff(self) -> None:
        frame = self.tab_staff
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        self.var_staff_type = tk.StringVar(value="Medecin")
        self.var_staff_nom = tk.StringVar()
        self.var_staff_prenom = tk.StringVar()
        self.var_staff_birth = tk.StringVar()
        self.var_staff_phone = tk.StringVar()
        self.var_staff_email = tk.StringVar()
        self.var_staff_start = tk.StringVar()
        self.var_staff_contract = tk.StringVar(value="CDI")
        self.var_staff_centers = tk.StringVar()
        self.var_staff_active = tk.StringVar()

        add_box = ttk.LabelFrame(frame, text="Ajouter personnel")
        add_box.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        add_box.columnconfigure(1, weight=1)
        self._add_row(add_box, "Type", ttk.Combobox(add_box, textvariable=self.var_staff_type, state="readonly", values=["Medecin", "Infirmier", "Chirurgien"]), 0)
        self._add_row(add_box, "Nom", ttk.Entry(add_box, textvariable=self.var_staff_nom), 1)
        self._add_row(add_box, "Prenom", ttk.Entry(add_box, textvariable=self.var_staff_prenom), 2)
        self._add_row(add_box, "Date naissance", ttk.Entry(add_box, textvariable=self.var_staff_birth), 3)
        self._add_row(add_box, "Telephone", ttk.Entry(add_box, textvariable=self.var_staff_phone), 4)
        self._add_row(add_box, "Email", ttk.Entry(add_box, textvariable=self.var_staff_email), 5)
        self._add_row(add_box, "Date debut", ttk.Entry(add_box, textvariable=self.var_staff_start), 6)
        self._add_row(add_box, "Contrat", ttk.Entry(add_box, textvariable=self.var_staff_contract), 7)
        self._add_row(add_box, "Centres (CSV)", ttk.Entry(add_box, textvariable=self.var_staff_centers), 8)
        self.cmb_staff_active_center = ttk.Combobox(add_box, textvariable=self.var_staff_active, state="readonly")
        self._add_row(add_box, "Centre actif", self.cmb_staff_active_center, 9)
        ttk.Button(add_box, text="Ajouter personnel", command=self._on_add_staff).grid(
            row=10, column=0, columnspan=2, sticky="ew", pady=5
        )

        manage_box = ttk.LabelFrame(frame, text="Modifier disponibilite")
        manage_box.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        manage_box.columnconfigure(1, weight=1)
        self.var_manage_staff_email = tk.StringVar()
        self.var_manage_staff_center = tk.StringVar()
        self.cmb_staff_manage_email = ttk.Combobox(manage_box, textvariable=self.var_manage_staff_email, state="readonly")
        self.cmb_staff_manage_center = ttk.Combobox(manage_box, textvariable=self.var_manage_staff_center, state="readonly")
        self._add_row(manage_box, "Email personnel", self.cmb_staff_manage_email, 0)
        self._add_row(manage_box, "Nouveau centre actif", self.cmb_staff_manage_center, 1)
        ttk.Button(
            manage_box,
            text="Appliquer disponibilite",
            command=self._on_set_staff_availability,
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

        self.txt_staff = ScrolledText(frame, wrap="word")
        self.txt_staff.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

    def _build_tab_patients(self) -> None:
        frame = self.tab_patients
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        self.var_patient_nom = tk.StringVar()
        self.var_patient_prenom = tk.StringVar()
        self.var_patient_birth = tk.StringVar()
        self.var_patient_phone = tk.StringVar()
        self.var_patient_email = tk.StringVar()
        self.var_patient_nss = tk.StringVar()
        self.var_patient_mutuelle = tk.StringVar()
        self.var_patient_address = tk.StringVar()
        self.var_patient_city = tk.StringVar()
        self.var_patient_region = tk.StringVar()
        self.var_patient_center = tk.StringVar()

        left = ttk.LabelFrame(frame, text="Ajouter patient")
        left.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left.columnconfigure(1, weight=1)
        self._add_row(left, "Nom", ttk.Entry(left, textvariable=self.var_patient_nom), 0)
        self._add_row(left, "Prenom", ttk.Entry(left, textvariable=self.var_patient_prenom), 1)
        self._add_row(left, "Date naissance", ttk.Entry(left, textvariable=self.var_patient_birth), 2)
        self._add_row(left, "Telephone", ttk.Entry(left, textvariable=self.var_patient_phone), 3)
        self._add_row(left, "Email", ttk.Entry(left, textvariable=self.var_patient_email), 4)
        self._add_row(left, "NSS", ttk.Entry(left, textvariable=self.var_patient_nss), 5)
        self._add_row(left, "Mutuelle", ttk.Entry(left, textvariable=self.var_patient_mutuelle), 6)
        self._add_row(left, "Adresse", ttk.Entry(left, textvariable=self.var_patient_address), 7)
        self.cmb_patient_city = ttk.Combobox(left, textvariable=self.var_patient_city, state="readonly")
        self.cmb_patient_region = ttk.Combobox(left, textvariable=self.var_patient_region, state="readonly")
        self.cmb_patient_center = ttk.Combobox(left, textvariable=self.var_patient_center, state="readonly")
        self._add_row(left, "Ville", self.cmb_patient_city, 8)
        self._add_row(left, "Region", self.cmb_patient_region, 9)
        self._add_row(left, "Centre actuel", self.cmb_patient_center, 10)
        ttk.Button(left, text="Ajouter patient", command=self._on_add_patient).grid(
            row=11, column=0, columnspan=2, sticky="ew", pady=5
        )

        right = ttk.LabelFrame(frame, text="Transfert dossier")
        right.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right.columnconfigure(1, weight=1)
        self.var_transfer_patient = tk.StringVar()
        self.var_transfer_center = tk.StringVar()
        self.var_transfer_date = tk.StringVar()
        self.cmb_transfer_patient = ttk.Combobox(right, textvariable=self.var_transfer_patient, state="readonly")
        self.cmb_transfer_center = ttk.Combobox(right, textvariable=self.var_transfer_center, state="readonly")
        self._add_row(right, "Patient NSS", self.cmb_transfer_patient, 0)
        self._add_row(right, "Nouveau centre", self.cmb_transfer_center, 1)
        self._add_row(right, "Date transfert", ttk.Entry(right, textvariable=self.var_transfer_date), 2)
        ttk.Button(right, text="Transferer", command=self._on_transfer_patient).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=5
        )

        self.txt_patients = ScrolledText(frame, wrap="word")
        self.txt_patients.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

    def _build_tab_rdv(self) -> None:
        frame = self.tab_rdv
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        left = ttk.LabelFrame(frame, text="Creer rendez-vous")
        left.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left.columnconfigure(1, weight=1)

        self.var_rdv_id = tk.StringVar()
        self.var_rdv_date = tk.StringVar()
        self.var_rdv_patient = tk.StringVar()
        self.var_rdv_center = tk.StringVar()
        self.var_rdv_type = tk.StringVar(value=TypeActeMedical.CONSULTATION.name)
        self.var_rdv_staff_csv = tk.StringVar()

        self.cmb_rdv_patient = ttk.Combobox(left, textvariable=self.var_rdv_patient, state="readonly")
        self.cmb_rdv_center = ttk.Combobox(left, textvariable=self.var_rdv_center, state="readonly")
        self.cmb_rdv_type = ttk.Combobox(left, textvariable=self.var_rdv_type, state="readonly")
        self._add_row(left, "ID RDV", ttk.Entry(left, textvariable=self.var_rdv_id), 0)
        self._add_row(left, "Date RDV", ttk.Entry(left, textvariable=self.var_rdv_date), 1)
        self._add_row(left, "Patient NSS", self.cmb_rdv_patient, 2)
        self._add_row(left, "Centre", self.cmb_rdv_center, 3)
        self._add_row(left, "Type acte", self.cmb_rdv_type, 4)
        self._add_row(left, "Staff emails (CSV)", ttk.Entry(left, textvariable=self.var_rdv_staff_csv), 5)
        ttk.Button(left, text="Creer RDV", command=self._on_create_rdv).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=5
        )

        right = ttk.LabelFrame(frame, text="Operations RDV")
        right.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right.columnconfigure(1, weight=1)

        self.var_rdv_ops_id = tk.StringVar()
        self.var_rdv_edit_date = tk.StringVar()
        self.var_rdv_cancel_date = tk.StringVar()
        self.var_rdv_cancel_staff = tk.StringVar()
        self.var_capacity_date = tk.StringVar()
        self.var_capacity_center = tk.StringVar()
        self.var_capacity_type = tk.StringVar(value=TypeActeMedical.CONSULTATION.name)

        self.cmb_rdv_ops_id = ttk.Combobox(right, textvariable=self.var_rdv_ops_id, state="readonly")
        self.cmb_rdv_cancel_staff = ttk.Combobox(right, textvariable=self.var_rdv_cancel_staff, state="readonly")
        self.cmb_capacity_center = ttk.Combobox(right, textvariable=self.var_capacity_center, state="readonly")
        self.cmb_capacity_type = ttk.Combobox(right, textvariable=self.var_capacity_type, state="readonly")
        self._add_row(right, "RDV", self.cmb_rdv_ops_id, 0)
        self._add_row(right, "Nouvelle date", ttk.Entry(right, textvariable=self.var_rdv_edit_date), 1)
        ttk.Button(right, text="Modifier date", command=self._on_edit_rdv).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=2
        )
        self._add_row(right, "Date annulation patient", ttk.Entry(right, textvariable=self.var_rdv_cancel_date), 3)
        ttk.Button(right, text="Annuler par patient", command=self._on_cancel_rdv_patient).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=2
        )
        self._add_row(right, "Personnel annulateur", self.cmb_rdv_cancel_staff, 5)
        ttk.Button(right, text="Annuler par personnel", command=self._on_cancel_rdv_staff).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=2
        )
        ttk.Button(right, text="Realiser RDV", command=self._on_realize_rdv).grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=2
        )
        ttk.Separator(right, orient="horizontal").grid(row=8, column=0, columnspan=2, sticky="ew", pady=5)
        self._add_row(right, "Date capacite", ttk.Entry(right, textvariable=self.var_capacity_date), 9)
        self._add_row(right, "Centre capacite", self.cmb_capacity_center, 10)
        self._add_row(right, "Type capacite", self.cmb_capacity_type, 11)
        ttk.Button(right, text="Calculer capacite", command=self._on_compute_capacity).grid(
            row=12, column=0, columnspan=2, sticky="ew", pady=2
        )
        self.lbl_capacity = ttk.Label(right, text="Capacite: -")
        self.lbl_capacity.grid(row=13, column=0, columnspan=2, sticky="w")

        self.txt_rdv = ScrolledText(frame, wrap="word")
        self.txt_rdv.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

    def _build_tab_dossier(self) -> None:
        frame = self.tab_dossier
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        self.var_dossier_patient = tk.StringVar()
        ttk.Label(frame, text="Patient NSS").grid(row=0, column=0, sticky="w")
        self.cmb_dossier_patient = ttk.Combobox(
            frame, textvariable=self.var_dossier_patient, state="readonly"
        )
        self.cmb_dossier_patient.grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(frame, text="Afficher dossier", command=self._on_show_dossier).grid(
            row=0, column=2, sticky="ew"
        )

        self.txt_dossier = ScrolledText(frame, wrap="word")
        self.txt_dossier.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=6)

    def _add_row(self, parent: ttk.Frame, label: str, widget, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2)
        widget.grid(row=row, column=1, sticky="ew", pady=2)

    def _on_add_region(self) -> None:
        def action() -> None:
            name = self.var_region_name.get().strip()
            if not name:
                raise ValueError("Nom de region obligatoire.")
            if name in self.regions:
                raise ValueError("Region deja existante.")
            self.regions[name] = Region(nom=name)
            self.var_region_name.set("")
            self._refresh_all()

        self._execute(action)

    def _on_add_department(self) -> None:
        def action() -> None:
            code = self.var_dept_code.get().strip()
            region_name = self.cmb_dept_region.get().strip()
            if not code or not region_name:
                raise ValueError("Code departement et region obligatoires.")
            if code in self.departements:
                raise ValueError("Departement deja existant.")
            dept = Departement(code=code)
            self.departements[code] = dept
            self.regions[region_name].ajouter_departement(dept)
            self.var_dept_code.set("")
            self._refresh_all()

        self._execute(action)

    def _on_add_city(self) -> None:
        def action() -> None:
            name = self.var_city_name.get().strip()
            cp = self.var_city_cp.get().strip()
            dept_code = self.cmb_city_dept.get().strip()
            if not name or not cp or not dept_code:
                raise ValueError("Ville, code postal et departement obligatoires.")
            key = f"{name} ({cp})"
            if key in self.villes:
                raise ValueError("Ville deja existante.")
            city = Ville(nom=name, code_postal=cp)
            self.villes[key] = city
            self.departements[dept_code].ajouter_ville(city)
            self.var_city_name.set("")
            self.var_city_cp.set("")
            self._refresh_all()

        self._execute(action)

    def _on_add_center(self) -> None:
        def action() -> None:
            center_name = self.var_center_name.get().strip()
            city_key = self.cmb_center_city.get().strip()
            if not center_name or not city_key:
                raise ValueError("Nom de centre et ville obligatoires.")
            if center_name in self.centres:
                raise ValueError("Centre deja existant.")
            center = CentreHospitalier(nom=center_name, ville=self.villes[city_key])
            self.centres[center_name] = center
            self.reseau.centres.append(center)
            self.var_center_name.set("")
            self._refresh_all()

        self._execute(action)

    def _on_add_staff(self) -> None:
        def action() -> None:
            email = self.var_staff_email.get().strip()
            if not email:
                raise ValueError("Email du personnel obligatoire.")
            if email in self.personnels:
                raise ValueError("Personnel deja existant.")

            class_map = {"Medecin": Medecin, "Infirmier": Infirmier, "Chirurgien": Chirurgien}
            cls = class_map[self.var_staff_type.get().strip()]
            staff = cls(
                nom=self.var_staff_nom.get().strip(),
                prenom=self.var_staff_prenom.get().strip(),
                date_naissance=self._parse_date(self.var_staff_birth.get()),
                telephone=self.var_staff_phone.get().strip(),
                email=email,
                date_debut_fonction=self._parse_date(self.var_staff_start.get()),
                type_contrat=self.var_staff_contract.get().strip(),
            )

            center_names = self._split_csv(self.var_staff_centers.get())
            for center_name in center_names:
                if center_name not in self.centres:
                    raise ValueError(f"Centre inconnu: {center_name}")
                staff.rattacher_a_centre(self.centres[center_name])

            active_center = self.var_staff_active.get().strip()
            if active_center:
                staff.definir_disponibilite(self.centres[active_center])
            elif center_names:
                staff.definir_disponibilite(self.centres[center_names[0]])

            self.personnels[email] = staff
            self.var_staff_nom.set("")
            self.var_staff_prenom.set("")
            self.var_staff_email.set("")
            self.var_staff_phone.set("")
            self.var_staff_centers.set("")
            self._refresh_all()

        self._execute(action)

    def _on_set_staff_availability(self) -> None:
        def action() -> None:
            email = self.var_manage_staff_email.get().strip()
            center_name = self.var_manage_staff_center.get().strip()
            if not email or not center_name:
                raise ValueError("Selectionner personnel et centre.")
            self.personnels[email].definir_disponibilite(self.centres[center_name])
            self._refresh_all()

        self._execute(action)

    def _on_add_patient(self) -> None:
        def action() -> None:
            nss = self.var_patient_nss.get().strip()
            if not nss:
                raise ValueError("NSS obligatoire.")
            if nss in self.patients:
                raise ValueError("Patient deja existant.")

            city_key = self.var_patient_city.get().strip()
            region_name = self.var_patient_region.get().strip()
            center_name = self.var_patient_center.get().strip()
            if not city_key or not region_name or not center_name:
                raise ValueError("Ville, region et centre obligatoires.")

            patient = Patient(
                nom=self.var_patient_nom.get().strip(),
                prenom=self.var_patient_prenom.get().strip(),
                date_naissance=self._parse_date(self.var_patient_birth.get()),
                telephone=self.var_patient_phone.get().strip(),
                email=self.var_patient_email.get().strip(),
                numero_securite_sociale=nss,
                numero_mutuelle=self.var_patient_mutuelle.get().strip() or None,
                adresse_postale=self.var_patient_address.get().strip(),
                ville_residence=self.villes[city_key],
                region_residence=self.regions[region_name],
                centre_actuel=self.centres[center_name],
            )
            self.patients[nss] = patient
            self.var_patient_nom.set("")
            self.var_patient_prenom.set("")
            self.var_patient_nss.set("")
            self.var_patient_phone.set("")
            self.var_patient_email.set("")
            self.var_patient_address.set("")
            self.var_patient_mutuelle.set("")
            self._refresh_all()

        self._execute(action)

    def _on_transfer_patient(self) -> None:
        def action() -> None:
            nss = self.var_transfer_patient.get().strip()
            center_name = self.var_transfer_center.get().strip()
            transfer_dt = self._parse_datetime(self.var_transfer_date.get())
            if not nss or not center_name:
                raise ValueError("Patient et centre obligatoires.")
            self.reseau.transferer_patient(
                patient=self.patients[nss],
                nouveau_centre=self.centres[center_name],
                date_transfert=transfer_dt,
            )
            self._refresh_all()

        self._execute(action)

    def _on_create_rdv(self) -> None:
        def action() -> None:
            rdv_id = self.var_rdv_id.get().strip()
            date_rdv = self._parse_datetime(self.var_rdv_date.get())
            nss = self.var_rdv_patient.get().strip()
            center_name = self.var_rdv_center.get().strip()
            type_name = self.var_rdv_type.get().strip()
            staff_emails = self._split_csv(self.var_rdv_staff_csv.get())
            if not rdv_id or not nss or not center_name or not type_name:
                raise ValueError("ID, patient, centre et type obligatoires.")
            if not staff_emails:
                raise ValueError("Au moins un personnel requis.")
            if nss not in self.patients:
                raise ValueError(f"Patient inconnu: {nss}")
            if center_name not in self.centres:
                raise ValueError(f"Centre inconnu: {center_name}")
            unknown = [email for email in staff_emails if email not in self.personnels]
            if unknown:
                raise ValueError(f"Personnel inconnu: {', '.join(unknown)}")
            staffs = [self.personnels[email] for email in staff_emails]
            self.reseau.creer_rendez_vous(
                id_rdv=rdv_id,
                date_heure=date_rdv,
                patient=self.patients[nss],
                centre=self.centres[center_name],
                type_acte=TypeActeMedical[type_name],
                personnels=staffs,
            )
            self.var_rdv_id.set("")
            self._refresh_all()

        self._execute(action)

    def _on_edit_rdv(self) -> None:
        def action() -> None:
            rdv_id = self.var_rdv_ops_id.get().strip()
            new_dt = self._parse_datetime(self.var_rdv_edit_date.get())
            if not rdv_id:
                raise ValueError("Selectionner un RDV.")
            self.reseau.modifier_date_rendez_vous(rdv_id, new_dt)
            self._refresh_all()

        self._execute(action)

    def _on_cancel_rdv_patient(self) -> None:
        def action() -> None:
            rdv_id = self.var_rdv_ops_id.get().strip()
            cancel_dt = self._parse_datetime(self.var_rdv_cancel_date.get())
            if not rdv_id:
                raise ValueError("Selectionner un RDV.")
            self.reseau.annuler_par_patient(rdv_id, cancel_dt)
            self._refresh_all()

        self._execute(action)

    def _on_cancel_rdv_staff(self) -> None:
        def action() -> None:
            rdv_id = self.var_rdv_ops_id.get().strip()
            email = self.var_rdv_cancel_staff.get().strip()
            if not rdv_id or not email:
                raise ValueError("Selectionner RDV et personnel.")
            self.reseau.annuler_par_personnel(rdv_id, self.personnels[email])
            self._refresh_all()

        self._execute(action)

    def _on_realize_rdv(self) -> None:
        def action() -> None:
            rdv_id = self.var_rdv_ops_id.get().strip()
            if not rdv_id:
                raise ValueError("Selectionner un RDV.")
            acte = self.reseau.realiser_rendez_vous(rdv_id)
            messagebox.showinfo(
                "Succes", f"Acte {acte.__class__.__name__} realise pour {acte.patient.nom}."
            )
            self._refresh_all()

        self._execute(action)

    def _on_compute_capacity(self) -> None:
        def action() -> None:
            target_dt = self._parse_datetime(self.var_capacity_date.get())
            center_name = self.var_capacity_center.get().strip()
            type_name = self.var_capacity_type.get().strip()
            if not center_name or not type_name:
                raise ValueError("Selectionner centre et type.")
            cap = self.reseau.nombre_rendez_vous_disponibles(
                date_heure=target_dt,
                centre=self.centres[center_name],
                type_acte=TypeActeMedical[type_name],
            )
            self.lbl_capacity.config(text=f"Capacite: {cap}")

        self._execute(action)

    def _on_show_dossier(self) -> None:
        def action() -> None:
            nss = self.var_dossier_patient.get().strip()
            if not nss:
                raise ValueError("Selectionner un patient.")
            patient = self.patients[nss]
            dossier = patient.dossier_medical
            if dossier is None:
                raise ErreurMetierHospitaliere("Dossier introuvable.")

            lines: List[str] = []
            lines.append(f"Patient: {patient.prenom} {patient.nom} ({nss})")
            lines.append(f"Dossier: {dossier.numero_dossier}")
            lines.append(f"Centre reference: {dossier.centre_reference.nom}")
            lines.append("")
            lines.append("Actes:")
            if dossier.actes:
                for acte in dossier.actes:
                    personnels = ", ".join(
                        [f"{p.prenom} {p.nom}" for p in acte.personnels]
                    )
                    lines.append(
                        f"- {acte.date_acte:%Y-%m-%d %H:%M} | {acte.__class__.__name__} | "
                        f"centre={acte.centre.nom} | personnels={personnels}"
                    )
            else:
                lines.append("- Aucun")
            lines.append("")
            lines.append("Transferts:")
            if dossier.transferts:
                for t in dossier.transferts:
                    lines.append(
                        f"- {t.date_transfert:%Y-%m-%d %H:%M} | {t.ancien_centre.nom} -> {t.nouveau_centre.nom}"
                    )
            else:
                lines.append("- Aucun")

            self._set_text(self.txt_dossier, "\n".join(lines))

        self._execute(action)


def main() -> None:
    app = AppNiveau4()
    app.mainloop()


if __name__ == "__main__":
    main()
