/*
 * Probe-only Frida Gadget script — NO hooks.
 * If the game still dies with this, crash is anti-Frida / gadget load, not unpin.
 */
(function () {
  "use strict";
  var PATHS = [
    "/sdcard/Android/data/com.lilithgame.hgame.gp/files/frida-unpin.log",
    "/storage/emulated/0/Android/data/com.lilithgame.hgame.gp/files/frida-unpin.log",
    "/data/data/com.lilithgame.hgame.gp/files/frida-unpin.log",
    "/sdcard/Download/frida-unpin.log",
  ];
  function log(msg) {
    var line = "[probe] " + msg + "\n";
    try {
      console.log(line);
    } catch (_) {}
    for (var i = 0; i < PATHS.length; i++) {
      try {
        var f = new File(PATHS[i], "a");
        f.write(line);
        f.flush();
        f.close();
      } catch (_) {}
    }
  }
  // Write immediately — before any timer (proves script loaded).
  log("ALIVE no-hooks");
  var n = 0;
  setInterval(function () {
    n += 1;
    log("heartbeat #" + n);
  }, 2000);
})();
