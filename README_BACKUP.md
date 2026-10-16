# Daily backup to Google Drive (free, no Google Cloud, no card)

1. In Google Drive create a **private** folder, e.g. "GH Backups". Copy the id from its link
   (`https://drive.google.com/drive/folders/<THIS-PART>`).
2. Go to https://script.google.com > New project. Replace the code with `apps_script/Code.gs`.
   Set `FOLDER_ID` and set `TOKEN` to a long random secret (e.g. 40 random characters).
3. Click **Deploy > New deployment > Web app**:
   - Execute as: **Me**
   - Who has access: **Anyone**   (the secret token protects it; the folder itself stays private)
   Authorize when asked, then copy the **Web app URL** (ends with `/exec`).
4. On Railway add the variable `GDRIVE_WEBAPP_TOKEN` = the same secret as in the script.
5. In the app: Settings > Daily Backup to Google Drive > paste the Web app URL, tick the switch,
   Save, then press **Upload a test backup now**.

If you edit the script later, use Deploy > Manage deployments > Edit > New version
(the URL stays the same).
