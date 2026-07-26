/*
 * Autonomous SSL / cert-pin bypass for Frida Gadget (script mode).
 * Target: Frida 16.x gadget (Java bridge bundled).
 * Covers: Java TrustManager / OkHttp / Conscrypt + native BoringSSL/OpenSSL/curl/mbedtls.
 */
(function () {
  "use strict";

  function log(msg) {
    try {
      console.log("[ssl-unpin] " + msg);
    } catch (_) {}
  }

  function hookJava() {
    if (typeof Java === "undefined" || !Java.available) {
      log("Java bridge unavailable — native hooks only");
      return;
    }
    Java.perform(function () {
      log("Java.perform — installing TrustManager hooks");

      try {
        var ArrayList = Java.use("java.util.ArrayList");
        var TrustManagerImpl = Java.use(
          "com.android.org.conscrypt.TrustManagerImpl"
        );
        TrustManagerImpl.checkTrustedRecursive.implementation = function () {
          return ArrayList.$new();
        };
        log("hooked TrustManagerImpl.checkTrustedRecursive");
      } catch (e) {
        log("TrustManagerImpl: " + e);
      }

      try {
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
      } catch (e) {
        log("SSLContext: " + e);
      }

      ["okhttp3.CertificatePinner"].forEach(function (name) {
        try {
          var C = Java.use(name);
          C.check.overloads.forEach(function (ov) {
            ov.implementation = function () {};
          });
          log("neutralized " + name + ".check");
        } catch (_) {}
      });

      try {
        var HttpsURLConnection = Java.use("javax.net.ssl.HttpsURLConnection");
        HttpsURLConnection.setDefaultHostnameVerifier.implementation =
          function () {};
        HttpsURLConnection.setHostnameVerifier.implementation = function () {};
        log("hooked HttpsURLConnection verifiers");
      } catch (e) {
        log("HttpsURLConnection: " + e);
      }

      try {
        var NSTM = Java.use(
          "android.security.net.config.NetworkSecurityTrustManager"
        );
        NSTM.checkPins.implementation = function () {};
        log("hooked NetworkSecurityTrustManager.checkPins");
      } catch (_) {}
    });
  }

  var hooked = {};

  function attachOnce(name, onEnter) {
    if (hooked[name]) return false;
    var addr = Module.findExportByName(null, name);
    if (!addr) return false;
    hooked[name] = true;
    Interceptor.attach(addr, { onEnter: onEnter });
    log("attached " + name);
    return true;
  }

  function hookNative() {
    log("native SSL hooks…");

    var acceptAll = new NativeCallback(
      function (_ssl, _out_alert) {
        return 0; /* ssl_verify_ok */
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
    attachOnce("SSL_CTX_set_verify", function (args) {
      args[1] = ptr(0);
      args[2] = ptr(0);
    });
    attachOnce("SSL_set_verify", function (args) {
      args[1] = ptr(0);
      args[2] = ptr(0);
    });
    attachOnce("mbedtls_ssl_conf_authmode", function (args) {
      args[1] = ptr(0); /* MBEDTLS_SSL_VERIFY_NONE */
    });

    attachOnce("curl_easy_setopt", function (args) {
      var opt = args[1].toInt32();
      // CURLOPT_SSL_VERIFYPEER=64, CURLOPT_SSL_VERIFYHOST=81
      if (opt === 64 || opt === 81) {
        args[2] = ptr(0);
      }
    });

    Process.enumerateModules().forEach(function (m) {
      var n = m.name.toLowerCase();
      if (
        n.indexOf("unity") < 0 &&
        n.indexOf("il2cpp") < 0 &&
        n.indexOf("mbedtls") < 0 &&
        n.indexOf("curl") < 0
      ) {
        return;
      }
      ["mbedtls_ssl_conf_authmode", "SSL_CTX_set_custom_verify", "SSL_CTX_set_verify"].forEach(
        function (sym) {
          try {
            var exp = m.findExportByName(sym);
            if (!exp) return;
            var key = m.name + "!" + sym;
            if (hooked[key]) return;
            hooked[key] = true;
            if (sym.indexOf("custom_verify") >= 0) {
              Interceptor.attach(exp, {
                onEnter: function (args) {
                  args[2] = acceptAll;
                },
              });
            } else {
              Interceptor.attach(exp, {
                onEnter: function (args) {
                  args[1] = ptr(0);
                },
              });
            }
            log("attached " + key);
          } catch (_) {}
        }
      );
    });

    var dl =
      Module.findExportByName(null, "android_dlopen_ext") ||
      Module.findExportByName(null, "dlopen");
    if (dl && !hooked.dlopen) {
      hooked.dlopen = true;
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
            p.indexOf("il2cpp") >= 0 ||
            p.indexOf("unity") >= 0 ||
            p.indexOf("ssl") >= 0 ||
            p.indexOf("curl") >= 0 ||
            p.indexOf("mbedtls") >= 0
          ) {
            log("dlopen " + this.path + " — refresh native hooks");
            hookNative();
          }
        },
      });
    }
  }

  log("booting ssl_unpin");
  hookJava();
  hookNative();
  log("ready");
})();
