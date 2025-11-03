Alternative sans WSL: build APK via GitHub Actions

Objectif

Construire l'APK Android de Minefut (pygame) dans le cloud avec GitHub Actions, sans installer WSL/SDK localement. L'APK sera disponible comme artefact téléchargeable.

Étapes

1) Assure-toi d'avoir ces fichiers dans le repo (déjà ajoutés ici):
	- `test apk/buildozer.spec` (pointe vers `..` et `main.py`, requirements `python3, pygame`).
	- `.github/workflows/android-build.yml` (workflow CI pour la build).

2) Pousse ce dossier sur GitHub (nouveau repo ou existant).

3) Lance le workflow:
	- Depuis GitHub: onglet "Actions" > "Build Android APK (Buildozer)" > "Run workflow".
	- Ou fais un push sur la branche: le workflow se déclenchera automatiquement si des fichiers suivis changent.

4) Récupère l'APK:
	- Ouvre l'exécution du workflow > "Artifacts" > télécharge `minefut-apk`.
	- L'APK de debug sera à l'intérieur (ex: `minefut-0.1.0-arm64-v8a-debug.apk`).

Notes

- Le workflow utilise Ubuntu, Java 17 et Buildozer pour télécharger automatiquement le SDK/NDK Android.
- Si tu veux inclure plus d'extensions d'assets, modifie `source.include_exts` dans `buildozer.spec`.
- Pour publier un .aab release signé, dis-le et on ajoutera l'étape de signature keystore.

