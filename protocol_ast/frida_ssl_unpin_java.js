/*
 * Minimal Frida Gadget unpin — OkHttp pin check bypass only.
 * Logging copied from frida_probe.js (File + Java FOS) — that path worked on-device.
 * Injector sets: var MODE = "java";
 */
(function () {
  "use strict";

  var MODE = "java";
  var PKG = "com.lilithgame.hgame.gp";
  var NAME = "frida-unpin.log";
  var PATHS = [
    "/sdcard/Download/" + NAME,
    "/storage/emulated/0/Download/" + NAME,
    "/sdcard/Android/data/" + PKG + "/files/" + NAME,
    "/storage/emulated/0/Android/data/" + PKG + "/files/" + NAME,
  ];
  // Long quiet window: prove heartbeats before touching OkHttp.
  var HOOK_DELAY_MS = 45000;

  function mkdirp(path) {
    try {
      var mkdir = new NativeFunction(
        Module.findExportByName(null, "mkdir") ||
          Module.findExportByName("libc.so", "mkdir"),
        "int",
        ["pointer", "int"]
      );
      var parts = path.split("/");
      var cur = "";
      for (var i = 0; i < parts.length; i++) {
        if (!parts[i]) continue;
        cur += "/" + parts[i];
        mkdir(Memory.allocUtf8String(cur), 0x1ed);
      }
    } catch (_) {}
  }

  function log(msg) {
    var line = "[ssl-unpin/" + MODE + " " + new Date().toISOString() + "] " + msg + "\n";
    try {
      console.log(line);
    } catch (_) {}
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
    // Same Java fallback that made probe logs visible in Download/
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

  function hookPinOnly() {
    if (typeof Java === "undefined" || !Java.available) {
      log("Java unavailable — pin hook skipped");
      return;
    }
    Java.perform(function () {
      var hooked = 0;
      try {
        var C = Java.use("okhttp3.CertificatePinner");
        C.check.overloads.forEach(function (ov) {
          try {
            ov.implementation = function () {
              return;
            };
            hooked++;
          } catch (e1) {
            log("pin overload fail: " + e1);
          }
        });
        log("CertificatePinner.check x" + hooked);
      } catch (e) {
        log("CertificatePinner missing/skip: " + e);
      }
      try {
        var C2 = Java.use("okhttp3.CertificatePinner");
        if (C2["check$okhttp"]) {
          C2["check$okhttp"].overloads.forEach(function (ov) {
            try {
              ov.implementation = function () {
                return;
              };
            } catch (_) {}
          });
          log("CertificatePinner.check$okhttp");
        }
      } catch (_) {}
      log("pin-only ready");
    });
  }

  log("boot MODE=" + MODE + " delay=" + HOOK_DELAY_MS + "ms pin-only");
  var hb = 0;
  setInterval(function () {
    hb += 1;
    log("heartbeat #" + hb);
  }, 2000);

  setTimeout(function () {
    log("installing pin hook…");
    try {
      hookPinOnly();
    } catch (e) {
      log("pin hook err: " + e);
    }
  }, HOOK_DELAY_MS);
})();
