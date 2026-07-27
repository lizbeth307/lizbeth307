/*
 * SSL unpin for Frida Gadget — staged & crash-safe (Lilith / AFK Arena).
 *
 * Modes (baked at inject: var MODE = "…"):
 *   probe  — use frida_probe.js instead
 *   java   — soft Java only (NO SSLContext.init / NO registerClass)
 *   native — java + safe BoringSSL (hook callback retval, never NativeCallback swap)
 *
 * Lilith dies if we replace TrustManagers via SSLContext.init+registerClass
 * during splash. Soft path: CertificatePinner + TrustManagerImpl.verifyChain
 * after a long delay, with heartbeats so logs show when it dies.
 */
(function () {
  "use strict";

  // Injector may rewrite this line: var MODE = "java"|"native";
  var MODE = "java";
  var PKG = "com.lilithgame.hgame.gp";
  var NAME = "frida-unpin.log";
  var LOG_PATHS = [
    "/sdcard/Download/" + NAME,
    "/storage/emulated/0/Download/" + NAME,
    "/sdcard/Android/data/" + PKG + "/files/" + NAME,
    "/storage/emulated/0/Android/data/" + PKG + "/files/" + NAME,
  ];
  // Splash + Lilith SDK often settle by ~8–12s; 2.5s was too early.
  var HOOK_DELAY_MS = 12000;
  var inJava = false;

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
    for (var i = 0; i < LOG_PATHS.length; i++) {
      try {
        var f = new File(LOG_PATHS[i], "a");
        f.write(line);
        f.flush();
        f.close();
      } catch (_) {}
    }
    // Never nest Java.perform while already inside Java.perform — that can crash.
    if (inJava) return;
    try {
      if (typeof Java !== "undefined" && Java.available) {
        Java.perform(function () {
          try {
            var FOS = Java.use("java.io.FileOutputStream");
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

  function safe(fn, label) {
    try {
      fn();
    } catch (e) {
      log((label || "err") + ": " + e);
    }
  }

  function hookJavaSoft() {
    if (typeof Java === "undefined" || !Java.available) {
      log("Java unavailable");
      return;
    }
    Java.perform(function () {
      inJava = true;
      try {
        log("Java soft hooks…");

        // --- OkHttp pin bypass (common for app-global / vip / psp) ---
        safe(function () {
          try {
            var C = Java.use("okhttp3.CertificatePinner");
            C.check.overloads.forEach(function (ov) {
              ov.implementation = function () {
                return;
              };
            });
            log("okhttp3.CertificatePinner.check");
          } catch (e) {
            log("CertificatePinner skip: " + e);
          }
          try {
            var C2 = Java.use("okhttp3.CertificatePinner");
            if (C2["check$okhttp"]) {
              C2["check$okhttp"].overloads.forEach(function (ov) {
                ov.implementation = function () {
                  return;
                };
              });
              log("okhttp3.CertificatePinner.check$okhttp");
            }
          } catch (_) {}
        }, "okhttp");

        // --- Conscrypt TrustManagerImpl (no SSLContext.init / no registerClass) ---
        safe(function () {
          var TMI = Java.use("com.android.org.conscrypt.TrustManagerImpl");
          if (TMI.verifyChain) {
            TMI.verifyChain.implementation = function (
              untrustedChain,
              trustAnchorChain,
              host,
              clientAuth,
              ocspData,
              tlsSctData
            ) {
              return untrustedChain;
            };
            log("TrustManagerImpl.verifyChain");
          }
          if (TMI.checkTrustedRecursive) {
            var ArrayList = Java.use("java.util.ArrayList");
            TMI.checkTrustedRecursive.implementation = function () {
              return ArrayList.$new();
            };
            log("TrustManagerImpl.checkTrustedRecursive");
          }
        }, "TrustManagerImpl");

        // --- Android network-security config pins ---
        safe(function () {
          var N = Java.use(
            "android.security.net.config.NetworkSecurityTrustManager"
          );
          if (N.checkPins) {
            N.checkPins.implementation = function () {};
            log("NetworkSecurityTrustManager.checkPins");
          }
        }, "NSTM");

        // --- Hostname verifier: accept all WITHOUT replacing SSLContext ---
        safe(function () {
          var HUV = Java.use("javax.net.ssl.HttpsURLConnection");
          var Allow = Java.use("javax.net.ssl.HostnameVerifier");
          // Hook instance setters only — do not invent a new class if possible.
          // Use a tiny registerClass ONLY if needed; Lilith crashed on SSLContext.init,
          // not necessarily on HV alone. Prefer hooking verify() on known verifiers.
          try {
            var OkHV = Java.use("okhttp3.internal.tls.OkHostnameVerifier");
            if (OkHV.verify) {
              OkHV.verify.overloads.forEach(function (ov) {
                ov.implementation = function () {
                  return true;
                };
              });
              log("OkHostnameVerifier.verify→true");
            }
          } catch (_) {}
          // noop dangerous setDefaultHostnameVerifier(null) patterns — skip
          void HUV;
          void Allow;
        }, "hostname");

        log("Java soft hooks done");
      } finally {
        inJava = false;
      }
    });
  }

  var hookedCb = {};

  function hookCustomVerifyExport(moduleName, exportName) {
    var addr;
    try {
      addr = moduleName
        ? Module.findExportByName(moduleName, exportName)
        : Module.findExportByName(null, exportName);
    } catch (_) {
      return;
    }
    if (!addr) return;
    var key = (moduleName || "*") + "!" + exportName;
    if (hookedCb[key]) return;
    hookedCb[key] = true;
    try {
      Interceptor.attach(addr, {
        onEnter: function (args) {
          var cb = args[2];
          if (cb.isNull()) return;
          var ck = cb.toString();
          if (hookedCb[ck]) return;
          hookedCb[ck] = true;
          try {
            Interceptor.attach(cb, {
              onLeave: function (retval) {
                try {
                  retval.replace(0);
                } catch (_) {}
              },
            });
            log("hooked verify cb via " + key);
          } catch (e) {
            log("cb hook fail " + key + ": " + e);
          }
        },
      });
      log("watching " + key);
    } catch (e) {
      log("watch fail " + key + ": " + e);
    }
  }

  function hookNativeSafe() {
    log("native hooks (safe BoringSSL pattern)…");
    ["libssl.so", "libboringssl.so", "libsscronet.so", null].forEach(function (m) {
      hookCustomVerifyExport(m, "SSL_CTX_set_custom_verify");
      hookCustomVerifyExport(m, "SSL_set_custom_verify");
    });

    safe(function () {
      var a = Module.findExportByName(null, "SSL_CTX_set_verify");
      if (!a || hookedCb.ssl_ctx_set_verify) return;
      hookedCb.ssl_ctx_set_verify = true;
      Interceptor.attach(a, {
        onEnter: function (args) {
          try {
            args[1] = ptr(0);
          } catch (_) {}
        },
      });
      log("SSL_CTX_set_verify mode=0");
    }, "SSL_CTX_set_verify");

    safe(function () {
      var a = Module.findExportByName(null, "SSL_get_verify_result");
      if (!a || hookedCb.ssl_get_verify_result) return;
      hookedCb.ssl_get_verify_result = true;
      Interceptor.attach(a, {
        onLeave: function (retval) {
          try {
            retval.replace(0);
          } catch (_) {}
        },
      });
      log("SSL_get_verify_result → 0");
    }, "SSL_get_verify_result");
  }

  log("boot MODE=" + MODE + " delay=" + HOOK_DELAY_MS + "ms");
  var hb = 0;
  setInterval(function () {
    hb += 1;
    log("heartbeat #" + hb);
  }, 2000);

  setTimeout(function () {
    if (MODE === "probe") {
      log("probe mode — no hooks");
      return;
    }
    log("installing hooks now…");
    // Pin-only lives in frida_ssl_unpin_java.js; this file always does soft Java.
    safe(hookJavaSoft, "java-tm");
    if (MODE === "native" || MODE === "full") {
      safe(hookNativeSafe, "native");
    } else {
      log("skip native (MODE=" + MODE + ")");
    }
    log("ready");
  }, HOOK_DELAY_MS);
})();
