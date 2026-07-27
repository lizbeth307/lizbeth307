/*
 * Probe-only Frida Gadget script — NO hooks.
 * If the game still dies with this, crash is anti-Frida / gadget load, not unpin.
 */
(function () {
  "use strict";
  var LOG = "/sdcard/Download/frida-unpin.log";
  function log(msg) {
    var line = "[probe] " + msg;
    try {
      console.log(line);
    } catch (_) {}
    try {
      var f = new File(LOG, "a");
      f.write(line + "\n");
      f.flush();
      f.close();
    } catch (_) {}
  }
  log("alive pid probescript — no hooks");
  var n = 0;
  setInterval(function () {
    n += 1;
    log("heartbeat #" + n);
  }, 2000);
})();
