/**
 * GH Invoicing - Drive backup receiver (free, no Google Cloud needed).
 * Saves the nightly backup ZIP sent by the app into YOUR private Drive folder.
 *
 * SETUP: see README_BACKUP.md
 */
const FOLDER_ID = '1twqkzUwm7eHpT8DSO9ESpMrM5baw01Jq';   // the part after /folders/ in the folder link
const TOKEN     = 'olakka123';  // must equal GDRIVE_WEBAPP_TOKEN on Railway

function doPost(e) {
  try {
    const d = JSON.parse(e.postData.contents);
    if (!d.token || d.token !== TOKEN) return out({ ok: false, error: 'Wrong token' });
    const folder = DriveApp.getFolderById(FOLDER_ID);

    if (d.action === 'ping') return out({ ok: true, folder: folder.getName() });

    if (d.action === 'upload') {
      if (!/^GH_FullBackup_[0-9_]+\.zip$/.test(d.name || '')) return out({ ok: false, error: 'Bad file name' });
      const blob = Utilities.newBlob(Utilities.base64Decode(d.data), 'application/zip', d.name);
      const file = folder.createFile(blob);
      const removed = prune(folder, parseInt(d.keep, 10) || 0);
      return out({ ok: true, name: file.getName(), size: file.getSize(), removed: removed });
    }
    return out({ ok: false, error: 'Unknown action' });
  } catch (err) {
    return out({ ok: false, error: String(err) });
  }
}

function prune(folder, keep) {
  if (keep < 1) return 0;
  const files = [];
  const it = folder.getFiles();
  while (it.hasNext()) {
    const f = it.next();
    if (/^GH_FullBackup_[0-9_]+\.zip$/.test(f.getName())) files.push(f);
  }
  files.sort(function (a, b) { return a.getName() < b.getName() ? 1 : -1; }); // newest first
  let n = 0;
  for (let i = keep; i < files.length; i++) { files[i].setTrashed(true); n++; }
  return n;
}

function out(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
