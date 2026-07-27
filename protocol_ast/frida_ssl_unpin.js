/*
 * Autonomous SSL / cert-pin bypass for Frida Gadget (script mode).
 * Crash-safe: delay hooks until after splash; never throw out of boot.
 * Target: Frida 16.x gadget (Java bridge bundled).
 */
(function () {
  "use strict";

  var LOG_PATH = "/sdcard/Download/frida-unpin.log";

  function log(msg) {
    var line = "[ssl-unpin] " + msg;
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
      log("Java bridge unavailable — native hooks only");
      return;
    }
    Java.perform(function () {
      log("Java.perform — TrustManager hooks");

      safe(function () {
        var ArrayList = Java.use("java.util.ArrayList");
        var TrustManagerImpl = Java.use(
          "com.android.org.conscrypt.TrustManagerImpl"
        );
        TrustManagerImpl.checkTrustedRecursive.implementation = function () {
          return ArrayList.$new();
        };
        log("hooked TrustManagerImpl.checkTrustedRecursive");
      }, "TrustManagerImpl");

      safe(function () {
        var X509TrustManager = Java.use("javax.net.ssl.X509TrustManager");
        var SSLContext = Java.use("javax.net.ssl.SSLContext");
        var TrustManagers = Java.registerClass({
          name: "com.signal.EmptyTrustManager",
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
        log("hooked SSLContext.init");
      }, "SSLContext");

      ["okhttp3.CertificatePinner"].forEach(function (name) {
        safe(function () {
          var C = Java.use(name);
          C.check.overloads.forEach(function (ov) {
            ov.implementation = function () {};
          });
          log("neutralized " + name + ".check");
        }, name);
      });

      safe(function () {
        var HttpsURLConnection = Java.use("javax.net.ssl.HttpsURLConnection");
        HttpsURLConnection.setDefaultHostnameVerifier.implementation =
          function () {};
        HttpsURLConnection.setHostnameVerifier.implementation = function () {};
        log("hooked HttpsURLConnection verifiers");
      }, "HttpsURLConnection");

      safe(function () {
        var NSTM = Java.use(
          "android.security.net.config.NetworkSecurityTrustManager"
        );
        NSTM.checkPins.implementation = function () {};
        log("hooked NetworkSecurityTrustManager.checkPins");
      }, "NSTM");
    });
  }

  var hooked = {};

  function attachOnce(name, onEnter) {
    if (hooked[name]) return false;
    var addr = null;
    try {
      addr = Module.findExportByName(null, name);
    } catch (_) {
      return false;
    }
    if (!addr) return false;
    hooked[name] = true;
    try {
      Interceptor.attach(addr, {
        onEnter: function (args) {
          try {
            onEnter(args);
          } catch (_) {}
        },
      });
      log("attached " + name);
      return true;
    } catch (e) {
      log("attach fail " + name + ": " + e);
      return false;
    }
  }

  function hookNativeLight() {
    log("native SSL hooks (light)…");

    // Prefer mode flags over replacing callbacks (safer across BoringSSL versions).
    attachOnce("SSL_CTX_set_verify", function (args) {
      args[1] = ptr(0);
    });
    attachOnce("SSL_set_verify", function (args) {
      args[1] = ptr(0);
    });
    attachOnce("mbedtls_ssl_conf_authmode", function (args) {
      args[1] = ptr(0);
    });
    attachOnce("curl_easy_setopt", function (args) {
      var opt = args[1].toInt32();
      if (opt === 64 || opt === 81) {
        args[2] = ptr(0);
      }
    });

    // Custom verify — only if NativeCallback works; wrap tightly.
    safe(function () {
      var acceptAll = new NativeCallback(
        function (_ssl, _out_alert) {
          return 0;
        },
        "int",
        ["pointer", "pointer"]
      );
      attachOnce("SSL_CTX_set_custom_verify", function (args) {
        args[2] = acceptAll;
      });
      attachOnce("SSL_set_custom_verify", function (args) {
        args[2] = acceptAll;
      });
    }, "custom_verify");
  }

  function armDlopenRefresh() {
    var dl = null;
    try {
      dl =
        Module.findExportByName(null, "android_dlopen_ext") ||
        Module.findExportByName(null, "dlopen");
    } catch (_) {}
    if (!dl || hooked.dlopen) return;
    hooked.dlopen = true;
    try {
      Interceptor.attach(dl, {
        onEnter: function (args) {
          try {
            this.path = args[0].readCString();
          } catch (_) {
            this.path = null;
          }
        },
        onLeave: function () {
          if (!this.path) return;
          var p = this.path.toLowerCase();
          if (
            p.indexOf("ssl") >= 0 ||
            p.indexOf("curl") >= 0 ||
            p.indexOf("mbedtls") >= 0 ||
            p.indexOf("cocos") >= 0
          ) {
            log("dlopen " + this.path + " — refresh");
            safe(hookNativeLight, "refresh-native");
          }
        },
      });
      log("dlopen watcher armed");
    } catch (e) {
      log("dlopen watch fail: " + e);
    }
  }

  log("booting ssl_unpin (delayed, crash-safe)");
  // Let Lilith / cocos finish early init before any Interceptor/Java work.
  var delayMs = 4000;
  setTimeout(function () {
    safe(hookJava, "java");
    safe(hookNativeLight, "native");
    safe(armDlopenRefresh, "dlopen");
    log("ready");
  }, delayMs);
})();
