// Apps Script trigger for contest status sync.
// Install: Extensions → Apps Script → paste this → run installOnEditTrigger once.

var CONTEST_API_URL = 'https://YOUR_SERVER/api/contest/update_status';

function onEditTrigger(e) {
  var sheet = e.source.getActiveSheet();
  if (sheet.getName() !== 'НАСТРОЙКИ') return;

  var range = e.range;
  // Column B = status column (1-indexed = 2)
  if (range.getColumn() !== 2) return;
  // Skip header row
  if (range.getRow() === 1) return;

  var code = sheet.getRange(range.getRow(), 1).getValue().toString().trim().toUpperCase();
  var status = range.getValue().toString().trim().toLowerCase();

  if (!code || (status !== 'active' && status !== 'inactive')) return;

  var options = {
    method: 'post',
    contentType: 'application/x-www-form-urlencoded',
    payload: 'code=' + encodeURIComponent(code) + '&status=' + encodeURIComponent(status),
    muteHttpExceptions: true
  };

  try {
    var response = UrlFetchApp.fetch(CONTEST_API_URL, options);
    Logger.log('update_status response: ' + response.getContentText());
  } catch (err) {
    Logger.log('update_status error: ' + err.toString());
  }
}

function installOnEditTrigger() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  ScriptApp.newTrigger('onEditTrigger')
    .forSpreadsheet(ss)
    .onEdit()
    .create();
  Logger.log('Trigger installed');
}
