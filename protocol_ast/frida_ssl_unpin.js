/*
 * SSL unpin for Frida Gadget — staged & crash-safe.
 *
 * Modes (via global FRIDA_UNPIN_MODE baked at inject time, default "java"):
 *   probe  — no hooks (use frida_probe.js instead)
 *   java   — Java TrustManager / OkHttp only (default; safest for Lilith splash)
 *   native — java + safe BoringSSL (hook callback retval, never NativeCallback swap)
 *
 * Why games die at ~4–8s: replacing SSL_CTX_set_custom_verify's callback with a
 * Frida NativeCallback of the wrong ABI → SIGSEGV on first TLS handshake.
 * Correct pattern: Interceptor.attach(existingCallback) + retval.replace(0).
 */
(function () {
  "use strict";

  var LOG_PATH = "/sdcard/Download/frida-unpin.log";
  // Injector may rewrite this line: var MODE = "java"|"native";
  var MODE = "java";

  function log(msg) {
    var line = "[ssl-unpin/" + MODE + "] " + msg;
    try {
      console.log(line);
    } catch (_) {}
    try {
      var f = new File(LOG_PATH, "a");
      f.write(line + "\n");
      f.flush();
      f.close();
    } catch (_) {}
  }

  function safe(fn, label) {
    try {
      fn();
    } catch (e) {
      log((label || "err") + ": " + e);
    }
  }

  function hookJava() {
    if (typeof Java === "undefined" || !Java.available) {
      log("Java unavailable");
      return;
    }
    Java.perform(function () {
      log("Java hooks…");

      safe(function () {
        var ArrayList = Java.use("java.util.ArrayList");
        var TrustManagerImpl = Java.use(
          "com.android.org.conscrypt.TrustManagerImpl"
        );
        if (TrustManagerImpl.checkTrustedRecursive) {
          TrustManagerImpl.checkTrustedRecursive.implementation = function () {
            return ArrayList.$new();
          };
          log("TrustManagerImpl.checkTrustedRecursive");
        }
      }, "TrustManagerImpl");

      safe(function () {
        var X509TrustManager = Java.use("javax.net.ssl.X509TrustManager");
        var SSLContext = Java.use("javax.net.ssl.SSLContext");
        // Unique class name per process start to avoid re-register crashes
        var clsName = "com.signal.EmptyTM" + Date.now();
        var TrustManagers = Java.registerClass({
          name: clsName,
          implements: [X509TrustManager],
          methods: {
            checkClientTrusted: function () {},
            checkServerTrusted: function () {},
            getAcceptedIssuers: function () {
              return [];
            },
          },
        });
        var tm = TrustManagers.$new();
        SSLContext.init.overload(
          "[Ljavax.net.ssl.KeyManager;",
          "[Ljavax.net.ssl.TrustManager;",
          "java.security.SecureRandom"
        ).implementation = function (km, _tm, sr) {
          this.init(km, [tm], sr);
        };
        log("SSLContext.init");
      }, "SSLContext");

      safe(function () {
        var C = Java.use("okhttp3.CertificatePinner");
        C.check.overloads.forEach(function (ov) {
          ov.implementation = function () {};
        });
        log("okhttp3.CertificatePinner");
      }, "CertificatePinner");

      safe(function () {
        var H = Java.use("javax.net.ssl.HttpsURLConnection");
        H.setDefaultHostnameVerifier.implementation = function () {};
        H.setHostnameVerifier.implementation = function () {};
        log("HttpsURLConnection");
      }, "HttpsURLConnection");

      safe(function () {
        var N = Java.use(
          "android.security.net.config.NetworkSecurityTrustManager"
        );
        N.checkPins.implementation = function () {};
        log("NetworkSecurityTrustManager.checkPins");
      }, "NSTM");
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
          // BoringSSL: void SSL_CTX_set_custom_verify(SSL_CTX*, int mode, callback)
          // callback is args[2]. Do NOT replace with NativeCallback — hook it.
          var cb = args[2];
          if (cb.isNull()) return;
          var ck = cb.toString();
          if (hookedCb[ck]) return;
          hookedCb[ck] = true;
          try {
            Interceptor.attach(cb, {
              onLeave: function (retval) {
                try {
                  // ssl_verify_ok == 0
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
    // Prefer named modules when present; also scan null for system libssl.
    ["libssl.so", "libboringssl.so", "libsscronet.so", null].forEach(function (m) {
      hookCustomVerifyExport(m, "SSL_CTX_set_custom_verify");
      hookCustomVerifyExport(m, "SSL_set_custom_verify");
    });

    // Soft mode flags only — no callback pointer swaps.
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

  log("boot MODE=" + MODE);
  // Short delay so cocos splash can paint; keep under anti-tamper patience.
  setTimeout(function () {
    if (MODE === "probe") {
      log("probe mode — no hooks");
      return;
    }
    safe(hookJava, "java");
    if (MODE === "native" || MODE === "full") {
      safe(hookNativeSafe, "native");
    } else {
      log("skip native (MODE=java). Re-inject with --unpin-mode native if needed.");
    }
    log("ready");
  }, 2500);
})();
