/*
 * Minimal Java SSL unpin for Lilith — OkHttp CertificatePinner ONLY.
 * No TrustManagerImpl, no SSLContext.init, no Interceptor, no registerClass.
 * Designed so the script itself stays small (anti-tamper scans strings).
 *
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
  ];
  // Stay quiet through Lilith splash + SDK; only then touch OkHttp.
  var HOOK_DELAY_MS = 25000;

  function mkdirp(path) {
    try {
      var mkdir = new NativeFunction(
        Module.findExportByName("libc.so", "mkdir") ||
          Module.findExportByName(null, "mkdir"),
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

  function logLibc(line) {
    try {
      var openPtr =
        Module.findExportByName("libc.so", "open") ||
        Module.findExportByName(null, "open");
      var writePtr =
        Module.findExportByName("libc.so", "write") ||
        Module.findExportByName(null, "write");
      var closePtr =
        Module.findExportByName("libc.so", "close") ||
        Module.findExportByName(null, "close");
      if (!openPtr || !writePtr || !closePtr) return;
      var openFn = new NativeFunction(openPtr, "int", ["pointer", "int", "int"]);
      var writeFn = new NativeFunction(writePtr, "int", ["int", "pointer", "int"]);
      var closeFn = new NativeFunction(closePtr, "int", ["int"]);
      // O_WRONLY|O_CREAT|O_APPEND = 1|64|1024
      var flags = 1 | 64 | 1024;
      var buf = Memory.allocUtf8String(line);
      var n = line.length;
      for (var i = 0; i < PATHS.length; i++) {
        try {
          var fd = openFn(Memory.allocUtf8String(PATHS[i]), flags, 0x1b6);
          if (fd < 0) continue;
          writeFn(fd, buf, n);
          closeFn(fd);
        } catch (_) {}
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
    } catch (_) {}
    logLibc(line);
    for (var i = 0; i < PATHS.length; i++) {
      try {
        var f = new File(PATHS[i], "a");
        f.write(line);
        f.flush();
        f.close();
      } catch (_) {}
    }
  }

  function hookPinOnly() {
    if (typeof Java === "undefined" || !Java.available) {
      log("Java unavailable — pin hook skipped");
      return;
    }
    Java.perform(function () {
      try {
        var C = Java.use("okhttp3.CertificatePinner");
        var n = 0;
        C.check.overloads.forEach(function (ov) {
          ov.implementation = function () {
            return;
          };
          n++;
        });
        log("CertificatePinner.check x" + n);
      } catch (e) {
        log("CertificatePinner missing/skip: " + e);
      }
      try {
        var C2 = Java.use("okhttp3.CertificatePinner");
        if (C2["check$okhttp"]) {
          C2["check$okhttp"].overloads.forEach(function (ov) {
            ov.implementation = function () {
              return;
            };
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
