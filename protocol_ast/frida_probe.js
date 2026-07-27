/*
 * Probe-only Frida Gadget script — NO hooks.
 * Writes logs with mkdir + multiple fallbacks (Download always preferred).
 */
(function () {
  "use strict";

  var PKG = "com.lilithgame.hgame.gp";
  var NAME = "frida-unpin.log";
  var PATHS = [
    "/sdcard/Download/" + NAME,
    "/storage/emulated/0/Download/" + NAME,
    "/sdcard/Android/data/" + PKG + "/files/" + NAME,
    "/storage/emulated/0/Android/data/" + PKG + "/files/" + NAME,
  ];

  function mkdirp(path) {
    // best-effort via libc
    try {
      var mkdir = new NativeFunction(
        Module.findExportByName(null, "mkdir") || Module.findExportByName("libc.so", "mkdir"),
        "int",
        ["pointer", "int"]
      );
      var parts = path.split("/");
      var cur = "";
      for (var i = 0; i < parts.length; i++) {
        if (!parts[i]) continue;
        cur += "/" + parts[i];
        var p = Memory.allocUtf8String(cur);
        mkdir(p, 0x1ed); // 0755
      }
    } catch (_) {}
  }

  function log(msg) {
    var line = "[probe " + new Date().toISOString() + "] " + msg + "\n";
    try {
      console.log(line);
    } catch (_) {}
    // Ensure parent dirs for Android/data
    try {
      mkdirp("/sdcard/Android/data/" + PKG + "/files");
      mkdirp("/storage/emulated/0/Android/data/" + PKG + "/files");
    } catch (_) {}
    for (var i = 0; i < PATHS.length; i++) {
      try {
        var f = new File(PATHS[i], "a");
        f.write(line);
        f.flush();
        f.close();
      } catch (_) {}
    }
    // Java fallback (works even when Frida File fails on some paths)
    try {
      if (typeof Java !== "undefined" && Java.available) {
        Java.perform(function () {
          try {
            var FileCls = Java.use("java.io.File");
            var FOS = Java.use("java.io.FileOutputStream");
            var dir = FileCls.$new("/sdcard/Download");
            if (!dir.exists()) dir.mkdirs();
            var out = FOS.$new("/sdcard/Download/" + NAME, true);
            var bytes = Java.use("java.lang.String").$new(line).getBytes("UTF-8");
            out.write(bytes);
            out.flush();
            out.close();
          } catch (_) {}
        });
      }
    } catch (_) {}
  }

  log("ALIVE no-hooks");
  var n = 0;
  setInterval(function () {
    n += 1;
    log("heartbeat #" + n);
  }, 2000);
})();
