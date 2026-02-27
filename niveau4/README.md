# Niveau 4 - Interface Tkinter

Cette interface permet de piloter le modele du niveau 3 avec une application desktop simple.

## Lancer l'application

Depuis la racine du projet :

```bash
py -3 niveau4/app_niveau4.py
```

## Onglets

- `Setup` : creation des regions, departements, villes et centres.
- `Personnels` : creation des medecins/infirmiers/chirurgiens, rattachement multi-centres, disponibilite active.
- `Patients` : creation patient + transfert de dossier.
- `Rendez-vous` : creation, modification, annulation (patient/personnel), realisation d'acte, calcul de capacite.
- `Dossiers` : consultation historique des actes et transferts.

## Formats attendus

- Date : `YYYY-MM-DD`
- Date/heure : `YYYY-MM-DD HH:MM`
- Listes CSV (centres, emails) : `valeur1,valeur2,valeur3`

## Notes

- Les regles metier du niveau 3 sont appliquees par le modele (`niveau3/hopital_niveau3.py`).
- Toutes les donnees sont en memoire (pas de base de donnees).
